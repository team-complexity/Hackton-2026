alter table cobros add column qr_imagen text;

comment on column cobros.qr is 'qrString de pey (la imagen es la que manda pey).';
