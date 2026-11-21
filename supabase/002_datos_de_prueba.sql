-- =====================================================================
-- PAGO FÁCIL — Datos de prueba y consultas de verificación (#23)
-- Todo es FICTICIO. Correr DESPUÉS de 001_esquema_inicial.sql.
-- Cada bloque se puede correr por separado en el SQL Editor de Supabase.
-- =====================================================================

-- ---------------------------------------------------------------------
-- A. Un negocio, un cupón y cuatro cobros (uno por estado)
-- ---------------------------------------------------------------------
insert into negocios (id, nombre, correo, contrasena_hash)
values ('00000000-0000-0000-0000-000000000001', 'Tacos Demo', 'demo@pagofacil.test',
        'hash-de-ejemplo-no-es-real');

insert into cupones (negocio_id, codigo, tipo, valor, usos_maximos)
values ('00000000-0000-0000-0000-000000000001', 'BIENVENIDA10', 'porcentaje', 10, 50);

insert into cobros (id, negocio_id, monto, concepto, num_ref, codi_qr_id, creado_en, expira_en, fin_ventana, cancelado_en)
values
  -- pendiente: vence en 10 minutos
  ('prueba-pendiente', '00000000-0000-0000-0000-000000000001', 150.00, 'Tacos',  '1234567', 'qr-prueba-1',
   now(), now() + interval '10 min', now() + interval '20 min', null),
  -- pagado: tendrá un pago
  ('prueba-pagado',    '00000000-0000-0000-0000-000000000001',  80.00, 'Refresco', '2345678', 'qr-prueba-2',
   now() - interval '1 hour', now() - interval '50 min', now() - interval '40 min', null),
  -- vencido: ya pasó su hora y nadie pagó
  ('prueba-vencido',   '00000000-0000-0000-0000-000000000001', 200.00, 'Gringas', '3456789', 'qr-prueba-3',
   now() - interval '2 hour', now() - interval '110 min', now() - interval '100 min', null),
  -- cancelado
  ('prueba-cancelado', '00000000-0000-0000-0000-000000000001',  50.00, 'Agua', '4567890', 'qr-prueba-4',
   now() - interval '5 min', now() + interval '5 min', now() + interval '15 min', now() - interval '1 min');

-- ---------------------------------------------------------------------
-- B. Registrar un pago (así lo debe hacer el backend con el webhook)
-- ---------------------------------------------------------------------
insert into pagos (cobro_id, transaccion_id, numero, monto_recibido, pagado_en, fuente)
values ('prueba-pagado', '01PRUEBATRANSACCION0000001', 1, 80.00, now() - interval '55 min', 'aviso')
on conflict (transaccion_id) do nothing;

-- ---------------------------------------------------------------------
-- C. PRUEBA DEL CRITERIO DE #23: el MISMO webhook llega otra vez.
--    Debe decir "INSERT 0 0" (no inserta nada) y el pago no se duplica.
-- ---------------------------------------------------------------------
insert into pagos (cobro_id, transaccion_id, numero, monto_recibido, pagado_en, fuente)
values ('prueba-pagado', '01PRUEBATRANSACCION0000001', 2, 80.00, now(), 'consulta')
on conflict (transaccion_id) do nothing;

select count(*) as pagos_del_cobro   -- debe dar 1
from pagos where cobro_id = 'prueba-pagado';

-- ---------------------------------------------------------------------
-- D. Historial del negocio con su estado (lo que usará #38)
--    Debe mostrar: pendiente, pagado, vencido y cancelado.
-- ---------------------------------------------------------------------
select id, concepto, monto, estado, numero_de_pagos, total_recibido, creado_en
from cobros_con_estado
where negocio_id = '00000000-0000-0000-0000-000000000001'
order by creado_en desc;

-- ---------------------------------------------------------------------
-- E. Corte del día (hora de la Ciudad de México)
-- ---------------------------------------------------------------------
select
  count(p.id)                     as pagos_de_hoy,
  coalesce(sum(p.monto_recibido), 0) as total_cobrado_hoy
from pagos p
join cobros c on c.id = p.cobro_id
where c.negocio_id = '00000000-0000-0000-0000-000000000001'
  and (p.pagado_en at time zone 'America/Mexico_City')::date
      = (now() at time zone 'America/Mexico_City')::date;

-- ---------------------------------------------------------------------
-- F. Limpiar los datos de prueba
-- ---------------------------------------------------------------------
-- delete from pagos    where cobro_id like 'prueba-%';
-- delete from cobros   where id like 'prueba-%';
-- delete from cupones  where negocio_id = '00000000-0000-0000-0000-000000000001';
-- delete from negocios where id = '00000000-0000-0000-0000-000000000001';
