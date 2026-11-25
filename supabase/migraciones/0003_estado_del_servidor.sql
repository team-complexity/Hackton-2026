create table estado_del_servidor (
  unico boolean primary key default true check (unico),
  conciliado_hasta timestamptz not null
);

alter table estado_del_servidor enable row level security;

revoke all on estado_del_servidor from anon, authenticated;
