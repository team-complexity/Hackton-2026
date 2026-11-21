try {
  const sesion = navigator.audioSession;
  if (sesion) {
    sesion.type = "playback";
  }
} catch {
  // La sesión es opcional. El elemento de audio puede seguir reproduciendo (R-7).
}

const audio = new Audio(URL.createObjectURL(wav_dos_tonos()));
let ultimo_intento = 0;

/**
 * WAV PCM de unos 0.6 s con dos tonos, armado en memoria (spec 002, R-7, DP-10).
 *
 * @returns {Blob}
 */
function wav_dos_tonos() {
  const tasa = 8000;
  const muestras = Math.floor(tasa * 0.6);
  const datos = muestras * 2;
  const buffer = new Uint8Array(44 + datos);
  escribir_texto(buffer, 0, "RIFF");
  escribir_u32(buffer, 4, 36 + datos);
  escribir_texto(buffer, 8, "WAVE");
  escribir_texto(buffer, 12, "fmt ");
  escribir_u32(buffer, 16, 16);
  escribir_u16(buffer, 20, 1);
  escribir_u16(buffer, 22, 1);
  escribir_u32(buffer, 24, tasa);
  escribir_u32(buffer, 28, tasa * 2);
  escribir_u16(buffer, 32, 2);
  escribir_u16(buffer, 34, 16);
  escribir_texto(buffer, 36, "data");
  escribir_u32(buffer, 40, datos);
  for (let indice = 0; indice < muestras; indice += 1) {
    const tiempo = indice / tasa;
    const frecuencia = tiempo < 0.3 ? 880 : 1174;
    const muestra = Math.round(Math.sin(2 * Math.PI * frecuencia * tiempo) * 12000);
    const offset = 44 + indice * 2;
    buffer[offset] = muestra & 255;
    buffer[offset + 1] = (muestra >> 8) & 255;
  }
  return new Blob([buffer], { type: "audio/wav" });
}

/**
 * @param {Uint8Array} buffer
 * @param {number} offset
 * @param {string} texto
 */
function escribir_texto(buffer, offset, texto) {
  for (let indice = 0; indice < texto.length; indice += 1) {
    buffer[offset + indice] = texto.charCodeAt(indice);
  }
}

/**
 * @param {Uint8Array} buffer
 * @param {number} offset
 * @param {number} valor
 */
function escribir_u32(buffer, offset, valor) {
  buffer[offset] = valor & 255;
  buffer[offset + 1] = (valor >> 8) & 255;
  buffer[offset + 2] = (valor >> 16) & 255;
  buffer[offset + 3] = (valor >> 24) & 255;
}

/**
 * @param {Uint8Array} buffer
 * @param {number} offset
 * @param {number} valor
 */
function escribir_u16(buffer, offset, valor) {
  buffer[offset] = valor & 255;
  buffer[offset + 1] = (valor >> 8) & 255;
}

function rebobinar() {
  try {
    audio.currentTime = 0;
  } catch {
    // Sin metadatos el navegador no deja rebobinar; el play sigue (R-7).
  }
}

/**
 * @param {number} volumen 0 para desbloquear sin que se oiga, 1 para el aviso
 * @returns {Promise<boolean>}
 */
async function reproducir(volumen) {
  const intento = ++ultimo_intento;
  const silencio = volumen === 0;
  const motivo = silencio ? "desbloqueo" : "aviso";
  try {
    rebobinar();
    audio.muted = silencio;
    audio.volume = volumen;
    await audio.play();
    // Pausar antes de que play se resuelva rechaza la promesa con AbortError.
    if (silencio && intento === ultimo_intento) {
      audio.pause();
    }
    console.info(`sonido: ${motivo} iniciado`);
    return true;
  } catch (error) {
    console.info(`sonido: ${motivo} rechazado (${error?.name || "Error"})`);
    return false;
  }
}

/**
 * Primer toque: reproduce en silencio para que el navegador deje sonar después
 * (spec 002, RF-025).
 *
 * @returns {Promise<boolean>}
 */
export function desbloquear() {
  return reproducir(0);
}

/**
 * Reproduce el sonido de pago y devuelve si se inició (spec 002, RF-022, RF-054).
 *
 * @returns {Promise<boolean>}
 */
export function sonar() {
  return reproducir(1);
}

/**
 * Vibra solo si el celular lo permite (spec 002, RF-024).
 *
 * @returns {void}
 */
export function vibrar() {
  try {
    if (typeof navigator.vibrate === "function") {
      navigator.vibrate([200, 100, 200]);
    }
  } catch {
    // Safari de iPhone no vibra; no es un fallo (R-8).
  }
}
