/**
 * Aplica una tecla al texto del monto.
 *
 * Teclas: "0" a "9", "punto" y "borrar". Ignora el tercer decimal, el segundo
 * punto y el sexto dígito entero (spec 002, RF-001, RF-003, RF-004, RF-066, RF-067, RF-068).
 *
 * @param {string} texto
 * @param {string} tecla
 * @returns {string}
 */
export function aplicar_tecla(texto, tecla) {
  if (tecla === "borrar") {
    return texto.slice(0, -1);
  }
  if (tecla === "punto") {
    if (texto.includes(".")) {
      return texto;
    }
    if (texto === "") {
      return "0.";
    }
    return `${texto}.`;
  }
  if (!/^[0-9]$/.test(tecla)) {
    return texto;
  }
  if (texto === "0") {
    return tecla;
  }
  const punto = texto.indexOf(".");
  if (punto === -1) {
    // El tope es la parte entera: "12345" + punto sí queda "12345." (RF-068).
    if (texto.length >= 5) {
      return texto;
    }
    return texto + tecla;
  }
  const decimales = texto.length - punto - 1;
  if (decimales >= 2) {
    return texto;
  }
  return texto + tecla;
}

/**
 * Cobrar solo con un monto mayor a 0 (spec 002, RF-006).
 *
 * @param {string} texto
 * @returns {boolean}
 */
export function cobrar_activo(texto) {
  if (texto === "") {
    return false;
  }
  const valor = Number(texto);
  return Number.isFinite(valor) && valor > 0;
}

/**
 * Monto libre es el caso contrario de Cobrar (spec 002, RF-065).
 *
 * @param {string} texto
 * @returns {boolean}
 */
export function monto_libre_activo(texto) {
  return !cobrar_activo(texto);
}
