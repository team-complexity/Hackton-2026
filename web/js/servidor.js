const MENSAJE_SIN_CONEXION =
  "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo.";
const MENSAJE_SIN_QR = "No se pudo mostrar el QR. Intenta de nuevo.";
const ESPERA_CREAR_MS = 15_000;

/**
 * Junta la única dirección configurada con la ruta (spec 002, RF-064).
 *
 * @param {string} ruta
 * @returns {string}
 */
function direccion(ruta) {
  return window.PAGO_FACIL.servidor + ruta;
}

/**
 * Pide un cobro al servidor. Devuelve `{ cobro }` o `{ mensaje }`
 * (spec 002, RF-009, RF-012, RF-013, RF-062, RF-063, RF-064, RF-078).
 *
 * La espera de 15 s usa setTimeout y AbortController: el reloj de las pruebas
 * no controla AbortSignal.timeout (QP-4).
 *
 * @param {number | null} monto
 * @param {string} concepto
 * @returns {Promise<{ cobro?: object, mensaje?: string }>}
 */
export async function crear_cobro(monto, concepto) {
  const controlador = new AbortController();
  const espera = setTimeout(() => {
    controlador.abort();
  }, ESPERA_CREAR_MS);
  try {
    const respuesta = await fetch(direccion("/api/cobros"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ monto, concepto }),
      signal: controlador.signal,
    });
    if (respuesta.status === 201) {
      const cobro = await respuesta.json();
      if (cobro && cobro.qr_imagen) {
        return { cobro };
      }
      return { mensaje: MENSAJE_SIN_QR };
    }
    if (
      respuesta.status === 422 ||
      respuesta.status === 429 ||
      respuesta.status === 502 ||
      respuesta.status === 503
    ) {
      const cuerpo = await respuesta.json();
      return { mensaje: cuerpo.detail };
    }
    return { mensaje: MENSAJE_SIN_CONEXION };
  } catch {
    return { mensaje: MENSAJE_SIN_CONEXION };
  } finally {
    clearTimeout(espera);
  }
}

/**
 * Consulta un cobro. Devuelve `{ cobro }`, `{ no_existe: true }` o `{ sin_conexion: true }`
 * (spec 002, RF-030, RF-033, RF-056, RF-057, RF-063, RF-064, RF-079).
 *
 * @param {string} id
 * @returns {Promise<{ cobro?: object, no_existe?: boolean, sin_conexion?: boolean }>}
 */
export async function ver_cobro(id) {
  try {
    const respuesta = await fetch(direccion(`/api/cobros/${id}`), { cache: "no-store" });
    if (respuesta.status === 200) {
      return { cobro: await respuesta.json() };
    }
    if (respuesta.status === 404) {
      return { no_existe: true };
    }
    return { sin_conexion: true };
  } catch {
    return { sin_conexion: true };
  }
}

/**
 * Pide cancelar un cobro. La vista lo usa desde el corte 2
 * (spec 002, RF-047, RF-050, RF-063, RF-064).
 *
 * @param {string} id
 * @returns {Promise<{ cobro?: object, mensaje?: string }>}
 */
export async function cancelar_cobro(id) {
  try {
    const respuesta = await fetch(direccion(`/api/cobros/${id}/cancelar`), {
      method: "POST",
    });
    if (respuesta.status === 200) {
      return { cobro: await respuesta.json() };
    }
    if (respuesta.status === 404 || respuesta.status === 409) {
      const cuerpo = await respuesta.json();
      return { mensaje: cuerpo.detail };
    }
    return { mensaje: MENSAJE_SIN_CONEXION };
  } catch {
    return { mensaje: MENSAJE_SIN_CONEXION };
  }
}
