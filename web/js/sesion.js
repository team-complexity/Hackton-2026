const CLAVE_SESION = "pago_facil_sesion";

/**
 * Guarda o borra el token de sesión en este navegador.
 *
 * @param {string | null} token
 * @returns {void}
 */
export function guardar_sesion(token) {
  try {
    if (token) {
      localStorage.setItem(CLAVE_SESION, token);
    } else {
      localStorage.removeItem(CLAVE_SESION);
    }
  } catch {
    // Sin almacenamiento, la sesión solo vive en memoria.
  }
}

/**
 * Lee el token guardado.
 *
 * @returns {string | null}
 */
export function leer_sesion() {
  try {
    const token = localStorage.getItem(CLAVE_SESION);
    return typeof token === "string" && token ? token : null;
  } catch {
    return null;
  }
}
