import { leer_sesion } from "./sesion.js";

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
 * @param {boolean} con_auth
 * @returns {HeadersInit}
 */
function cabeceras_json(con_auth = false) {
  const cabeceras = { "Content-Type": "application/json" };
  if (con_auth) {
    const token = leer_sesion();
    if (token) {
      cabeceras.Authorization = `Bearer ${token}`;
    }
  }
  return cabeceras;
}

/**
 * @param {boolean} con_auth
 * @returns {HeadersInit}
 */
function cabeceras_auth(con_auth = true) {
  const cabeceras = {};
  if (con_auth) {
    const token = leer_sesion();
    if (token) {
      cabeceras.Authorization = `Bearer ${token}`;
    }
  }
  return cabeceras;
}

/**
 * @param {unknown} detalle
 * @returns {string}
 */
function texto_detalle(detalle) {
  return typeof detalle === "string" && detalle ? detalle : MENSAJE_SIN_CONEXION;
}

/**
 * Pide un cobro al servidor. Devuelve `{ cobro }` o `{ mensaje }`
 * (spec 002, RF-009, RF-012, RF-013, RF-062, RF-063, RF-064, RF-078).
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
      headers: cabeceras_json(false),
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
      const cuerpo = await respuesta.json().catch(() => ({}));
      return { mensaje: texto_detalle(cuerpo.detail) };
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
 * (spec 002, RF-030, RF-033, RF-056, RF-057, RF-063, RF-064).
 *
 * @param {string} id
 * @returns {Promise<{ cobro?: object, no_existe?: boolean, sin_conexion?: boolean }>}
 */
export async function ver_cobro(id) {
  try {
    const respuesta = await fetch(direccion(`/api/cobros/${id}`), {
      headers: cabeceras_auth(false),
    });
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
 * Pide cancelar un cobro.
 *
 * @param {string} id
 * @returns {Promise<{ cobro?: object, mensaje?: string }>}
 */
export async function cancelar_cobro(id) {
  try {
    const respuesta = await fetch(direccion(`/api/cobros/${id}/cancelar`), {
      method: "POST",
      headers: cabeceras_auth(false),
    });
    if (respuesta.status === 200) {
      return { cobro: await respuesta.json() };
    }
    if (respuesta.status === 404 || respuesta.status === 409) {
      const cuerpo = await respuesta.json().catch(() => ({}));
      return { mensaje: texto_detalle(cuerpo.detail) };
    }
    return { mensaje: MENSAJE_SIN_CONEXION };
  } catch {
    return { mensaje: MENSAJE_SIN_CONEXION };
  }
}

/**
 * Inicia sesión con correo y contraseña.
 *
 * @param {string} correo
 * @param {string} clave
 * @returns {Promise<{ sesion?: { token: string, correo: string, plan: string }, mensaje?: string }>}
 */
export async function iniciar_sesion(correo, clave) {
  try {
    const respuesta = await fetch(direccion("/api/sesion"), {
      method: "POST",
      headers: cabeceras_json(false),
      body: JSON.stringify({ correo, clave }),
    });
    const cuerpo = await respuesta.json().catch(() => ({}));
    if (respuesta.status === 200) {
      return { sesion: cuerpo };
    }
    return { mensaje: texto_detalle(cuerpo.detail) };
  } catch {
    return { mensaje: MENSAJE_SIN_CONEXION };
  }
}

/**
 * Consulta la sesión actual.
 *
 * @returns {Promise<{ sesion?: { correo: string, plan: string }, sin_sesion?: boolean, no_disponible?: boolean }>}
 */
export async function pedir_sesion() {
  try {
    const respuesta = await fetch(direccion("/api/sesion"), {
      headers: cabeceras_auth(true),
    });
    if (respuesta.status === 200) {
      return { sesion: await respuesta.json() };
    }
    if (respuesta.status === 401) {
      return { sin_sesion: true };
    }
    if (respuesta.status === 404) {
      return { no_disponible: true };
    }
    return { sin_sesion: true };
  } catch {
    return { no_disponible: true };
  }
}

/**
 * Cierra la sesión actual.
 *
 * @returns {Promise<void>}
 */
export async function cerrar_sesion() {
  try {
    await fetch(direccion("/api/sesion"), {
      method: "DELETE",
      headers: cabeceras_auth(true),
    });
  } catch {
    // Cerrar sesión localmente es suficiente si el servidor no responde.
  }
}

/**
 * Lista cobros para historial.
 *
 * @returns {Promise<{ cobros?: object[], mensaje?: string, sin_sesion?: boolean }>}
 */
export async function listar_cobros() {
  try {
    const respuesta = await fetch(direccion("/api/cobros"), {
      headers: cabeceras_auth(true),
    });
    if (respuesta.status === 200) {
      return { cobros: await respuesta.json() };
    }
    if (respuesta.status === 401) {
      return { sin_sesion: true };
    }
    const cuerpo = await respuesta.json().catch(() => ({}));
    return { mensaje: texto_detalle(cuerpo.detail) };
  } catch {
    return { mensaje: MENSAJE_SIN_CONEXION };
  }
}
