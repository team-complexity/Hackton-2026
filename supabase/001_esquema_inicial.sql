-- =====================================================================
-- PAGO FÁCIL — Esquema inicial de la base de datos (Supabase / PostgreSQL)
-- Issues: #19 (proyecto y esquema inicial) y #23 (tablas)
--
-- Cómo usarlo: Supabase → SQL Editor → New query → pegar todo → Run.
-- Se puede correr una sola vez. Si hay que repetirlo desde cero, ver el
-- bloque "BORRAR TODO" al final (comentado).
-- =====================================================================

begin;

-- ---------------------------------------------------------------------
-- 1. NEGOCIOS: quién cobra (#24)
-- ---------------------------------------------------------------------
create table negocios (
  id               uuid primary key default gen_random_uuid(),
  nombre           text not null check (length(trim(nombre)) between 1 and 80),
  correo           text not null check (correo ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
  contrasena_hash  text not null,              -- argon2 o bcrypt; nunca texto plano
  plan             text not null default 'gratis' check (plan in ('gratis', 'premium')),
  creado_en        timestamptz not null default now()
);

-- Un correo por negocio, sin importar mayúsculas (Juan@x.com = juan@x.com).
create unique index negocios_correo_unico on negocios (lower(correo));

comment on table negocios is 'Negocios que cobran con PAGO FÁCIL. No guarda CLABE ni datos bancarios.';

-- ---------------------------------------------------------------------
-- 2. CUPONES: descuentos del negocio (#37)
-- ---------------------------------------------------------------------
create table cupones (
  id             uuid primary key default gen_random_uuid(),
  negocio_id     uuid not null references negocios (id) on delete cascade,
  codigo         text not null check (codigo ~ '^[A-Z0-9_-]{3,20}$'),
  tipo           text not null check (tipo in ('porcentaje', 'monto')),
  valor          numeric(12, 2) not null check (valor > 0),
  vigente_desde  timestamptz not null default now(),
  vigente_hasta  timestamptz,                  -- vacío = sin fecha de fin
  usos_maximos   int check (usos_maximos > 0), -- vacío = ilimitado
  usos           int not null default 0 check (usos >= 0),
  activo         boolean not null default true,
  creado_en      timestamptz not null default now(),

  unique (negocio_id, codigo),
  check (tipo <> 'porcentaje' or valor <= 100),
  check (vigente_hasta is null or vigente_hasta > vigente_desde),
  check (usos_maximos is null or usos <= usos_maximos)
);

comment on column cupones.usos is 'Se suma cuando el cobro pasa a pagado, no cuando se crea el QR (principio II).';

-- ---------------------------------------------------------------------
-- 3. COBROS: cada QR de CoDi que se genera
-- ---------------------------------------------------------------------
create table cobros (
  id                   text primary key check (length(id) between 8 and 32), -- token aleatorio del backend
  negocio_id           uuid references negocios (id),   -- vacío mientras no exista el login (#24)
  monto                numeric(12, 2) check (monto > 0), -- vacío = monto libre
  monto_original       numeric(12, 2) check (monto_original > 0), -- antes del cupón
  cupon_id             uuid references cupones (id),
  concepto             varchar(40) not null default 'Cobro',
  num_ref              varchar(7) not null check (num_ref ~ '^[0-9]{1,7}$'),
  codi_qr_id           text unique,            -- id que devuelve pey; con él llega el webhook
  qr                   text,                   -- qrString de pey (la imagen se vuelve a dibujar)
  creado_en            timestamptz not null default now(),
  expira_en            timestamptz not null,
  fin_ventana          timestamptz not null,   -- expira_en + gracia
  cancelado_en         timestamptz,
  ultima_consulta_pey  timestamptz,

  check (expira_en > creado_en),
  check (fin_ventana >= expira_en),
  check (cupon_id is null or (monto is not null and monto_original is not null))
);

create index cobros_por_negocio_y_fecha on cobros (negocio_id, creado_en desc);

comment on table cobros is 'El estado (pendiente, pagado, vencido, cancelado) NO se guarda: se calcula en la vista cobros_con_estado.';

-- ---------------------------------------------------------------------
-- 4. PAGOS: dinero que sí llegó. Un cobro puede tener varios.
-- ---------------------------------------------------------------------
create table pagos (
  id              bigint generated always as identity primary key,
  cobro_id        text not null references cobros (id),
  transaccion_id  text not null unique,        -- ⚠️ CLAVE: evita contar un pago dos veces (principio II)
  numero          int not null check (numero > 0),
  monto_recibido  numeric(12, 2) not null check (monto_recibido > 0),
  monto_base      numeric(12, 2),
  pagado_en       timestamptz not null,
  fuente          text not null check (fuente in ('aviso', 'consulta')),
  registrado_en   timestamptz not null default now(),

  unique (cobro_id, numero)
);

create index pagos_por_cobro on pagos (cobro_id);
create index pagos_por_fecha on pagos (pagado_en);

comment on column pagos.transaccion_id is 'transactionId de pey. Insertar con ON CONFLICT (transaccion_id) DO NOTHING.';

-- ---------------------------------------------------------------------
-- 5. AVISOS DE WEBHOOK: webhook-id ya vistos (primera barrera contra reenvíos)
-- ---------------------------------------------------------------------
create table avisos_webhook (
  webhook_id   text primary key,
  tipo         text not null,
  recibido_en  timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- 6. VISTA: cobros con su estado calculado (misma lógica que cobros.py)
--    pagos → pagado; si no, cancelado_en → cancelado;
--    si no, ahora ≥ expira_en → vencido; si no → pendiente
-- ---------------------------------------------------------------------
create view cobros_con_estado
with (security_invoker = true) as
select
  c.*,
  (c.monto is null)                    as monto_libre,
  p.numero_de_pagos,
  coalesce(p.total_recibido, 0)        as total_recibido,
  p.ultimo_pago                        as pagado_en,
  case
    when p.numero_de_pagos > 0      then 'pagado'
    when c.cancelado_en is not null then 'cancelado'
    when now() >= c.expira_en       then 'vencido'
    else                                 'pendiente'
  end                                  as estado
from cobros c
cross join lateral (
  select
    count(*)::int        as numero_de_pagos,
    sum(monto_recibido)  as total_recibido,
    max(pagado_en)       as ultimo_pago
  from pagos
  where pagos.cobro_id = c.id
) p;

-- ---------------------------------------------------------------------
-- 7. SEGURIDAD: RLS encendido y sin políticas públicas.
--    Solo el backend entra (con su credencial en backend/.env).
--    La web NUNCA habla con Supabase directamente (principio III).
-- ---------------------------------------------------------------------
alter table negocios       enable row level security;
alter table cupones        enable row level security;
alter table cobros         enable row level security;
alter table pagos          enable row level security;
alter table avisos_webhook enable row level security;

revoke all on negocios, cupones, cobros, pagos, avisos_webhook, cobros_con_estado
  from anon, authenticated;

commit;

-- =====================================================================
-- BORRAR TODO (solo si hay que empezar de cero; quita los "--" y corre)
-- =====================================================================
-- drop view  if exists cobros_con_estado;
-- drop table if exists pagos, avisos_webhook, cobros, cupones, negocios cascade;
