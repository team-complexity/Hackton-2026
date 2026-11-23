-- PAGO FÁCIL — Datos de prueba ficticios.
-- Solo se cargan con --datos-de-prueba en una base marcada local.

-- ---------------------------------------------------------------------
-- A. Un negocio, un cupón y cuatro cobros (uno por estado)
-- ---------------------------------------------------------------------
insert into negocios (id, nombre, correo, contrasena_hash)
values ('00000000-0000-0000-0000-000000000001', 'Tacos Demo', 'demo@pagofacil.test',
        'hash-de-ejemplo-no-es-real')
on conflict do nothing;

insert into cupones (negocio_id, codigo, tipo, valor, usos_maximos)
values ('00000000-0000-0000-0000-000000000001', 'BIENVENIDA10', 'porcentaje', 10, 50)
on conflict do nothing;

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
   now() - interval '5 min', now() + interval '5 min', now() + interval '15 min', now() - interval '1 min')
on conflict do nothing;

-- ---------------------------------------------------------------------
-- B. Registrar un pago (así lo debe hacer el backend con el webhook)
-- ---------------------------------------------------------------------
insert into pagos (cobro_id, transaccion_id, numero, monto_recibido, pagado_en, fuente)
values ('prueba-pagado', '01PRUEBATRANSACCION0000001', 1, 80.00, now() - interval '55 min', 'aviso')
on conflict do nothing;
