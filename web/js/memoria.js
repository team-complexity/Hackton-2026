const CLAVE = "pago_facil_escucha";
const ID_VALIDO = /^[A-Za-z0-9_-]{1,32}$/;

/**
 * Guarda qué cobro está en pantalla y cuáles son anteriores.
 * Si el celular no deja escribir, no pasa nada (spec 002, RF-051, RF-076).
 *
 * @param {string | null} en_pantalla
 * @param {string[]} anteriores
 * @returns {void}
 */
export function guardar(en_pantalla, anteriores) {
  try {
    const datos = {
      en_pantalla: en_pantalla ?? null,
      anteriores: Array.isArray(anteriores) ? anteriores : [],
    };
    localStorage.setItem(CLAVE, JSON.stringify(datos));
  } catch {
    try {
      localStorage.removeItem(CLAVE);
    } catch {
      // Si el almacenamiento está bloqueado por completo, tampoco se puede borrar.
    }
  }
}

/**
 * Lee lo guardado. Si no tiene la forma exigida, devuelve null
 * (spec 002, RF-051, RF-076, RF-077).
 *
 * @returns {{ en_pantalla: string | null, anteriores: string[] } | null}
 */
export function leer() {
  try {
    const texto = localStorage.getItem(CLAVE);
    if (typeof texto !== "string") {
      return null;
    }
    const datos = JSON.parse(texto);
    if (!forma_valida(datos)) {
      return null;
    }
    return {
      en_pantalla: datos.en_pantalla,
      anteriores: datos.anteriores.slice(),
    };
  } catch {
    return null;
  }
}

/**
 * Solo se aceptan las dos claves y los ids. Lo demás se ignora entero (RF-077).
 *
 * @param {object} datos
 * @returns {boolean}
 */
function forma_valida(datos) {
  if (!datos || typeof datos !== "object" || Array.isArray(datos)) {
    return false;
  }
  const claves = Object.keys(datos);
  if (claves.length !== 2 || !claves.includes("en_pantalla") || !claves.includes("anteriores")) {
    return false;
  }
  if (!(datos.en_pantalla === null || es_id(datos.en_pantalla))) {
    return false;
  }
  if (!Array.isArray(datos.anteriores) || !datos.anteriores.every(es_id)) {
    return false;
  }
  return true;
}

/**
 * @param {unknown} valor
 * @returns {boolean}
 */
function es_id(valor) {
  return typeof valor === "string" && ID_VALIDO.test(valor);
}
