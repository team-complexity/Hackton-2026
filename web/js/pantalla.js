/** @type {Promise<{ release: () => Promise<void> }> | { release: () => Promise<void> } | null} */
let bloqueo = null;
let pedido = false;
let encendida = false;

/**
 * @returns {boolean}
 */
function hay_bloqueo() {
  const api = navigator.wakeLock;
  return Boolean(api && typeof api.request === "function");
}

/**
 * Pide el bloqueo si debe estar encendida y no hay uno vivo (spec 002, RF-058).
 *
 * @returns {Promise<void>}
 */
async function pedir() {
  if (!encendida || bloqueo || pedido || !hay_bloqueo()) {
    return;
  }
  pedido = true;
  try {
    const obtenido = await navigator.wakeLock.request("screen");
    if (encendida) {
      bloqueo = obtenido;
    } else {
      // Se pidió soltar mientras el navegador contestaba: este bloqueo no se queda pegado (RF-059).
      await obtenido.release();
    }
  } catch (error) {
    console.warn("No se pudo mantener la pantalla encendida.", error);
  } finally {
    pedido = false;
  }
}

/**
 * Pide o suelta que la pantalla no se apague (spec 002, RF-058, RF-059).
 *
 * @param {boolean} si_o_no
 * @returns {Promise<void>}
 */
export async function mantener_encendida(si_o_no) {
  encendida = si_o_no;
  if (!si_o_no) {
    const actual = bloqueo;
    bloqueo = null;
    if (actual && typeof actual.release === "function") {
      try {
        await actual.release();
      } catch (error) {
        console.warn("No se pudo soltar el bloqueo de pantalla.", error);
      }
    }
    return;
  }
  await pedir();
}

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState !== "visible" || !encendida) {
    return;
  }
  // El navegador suelta el bloqueo al ocultar la página (R-9).
  bloqueo = null;
  pedir();
});
