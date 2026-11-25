/**
 * Diferencia entre la hora del servidor y la del celular, en segundos.
 *
 * Sin hora_servidor vale 0 y avisa en consola (spec 002, RF-019).
 *
 * @param {{ hora_servidor?: number | null }} cobro
 * @param {number} ahora segundos Unix del celular
 * @returns {number}
 */
export function desfase(cobro, ahora) {
  if (cobro.hora_servidor == null) {
    console.warn("El cobro no trae hora_servidor; la cuenta usa el reloj del celular.");
    return 0;
  }
  return cobro.hora_servidor - ahora;
}

/**
 * Segundos que le quedan al QR: expira_en menos el ahora ya corregido (spec 002, RF-018, RF-019).
 *
 * @param {{ expira_en: number }} cobro
 * @param {number} desfase segundos de desfase(cobro, ahora)
 * @param {number} ahora segundos Unix del celular
 * @returns {number}
 */
export function restante(cobro, desfase, ahora) {
  return cobro.expira_en - (ahora + desfase);
}

/**
 * m:ss. Trunca los decimales y no baja de 0:00 (spec 002, RF-018).
 *
 * @param {number} segundos
 * @returns {string}
 */
export function formato(segundos) {
  const enteros = Math.trunc(segundos);
  const seguro = enteros > 0 ? enteros : 0;
  const minutos = Math.floor(seguro / 60);
  const resto = seguro % 60;
  const texto_resto = resto < 10 ? `0${resto}` : String(resto);
  return `${minutos}:${texto_resto}`;
}
