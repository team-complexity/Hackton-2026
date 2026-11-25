-- PAGO FÁCIL — Consultas de verificación.
-- Para correrlas a mano. El comando de migraciones no las aplica.

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
