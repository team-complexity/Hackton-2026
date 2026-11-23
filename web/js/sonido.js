const CLAVE_PREFS = "pago_facil_prefs";

function leer_prefs() {
  try {
    const raw = localStorage.getItem(CLAVE_PREFS);
    if (!raw) return { sonido: true, vibracion: true, pantalla: true };
    const p = JSON.parse(raw);
    return {
      sonido: p.sonido !== false,
      vibracion: p.vibracion !== false,
      pantalla: p.pantalla !== false,
    };
  } catch {
    return { sonido: true, vibracion: true, pantalla: true };
  }
}

function wav_pago_recibido() {
  const tasa = 22050;
  const dur = 0.75;
  const muestras = Math.floor(tasa * dur);
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
  for (let i = 0; i < muestras; i += 1) {
    const t = i / tasa;
    // Dos tonos tipo caja: ding-dong claro
    let f = 880;
    let amp = 0;
    if (t < 0.18) { f = 987.77; amp = Math.min(1, t / 0.01) * (1 - t / 0.22); }
    else if (t < 0.75) { f = 1318.51; const tt = t - 0.18; amp = Math.min(1, tt / 0.01) * Math.exp(-tt * 4.2); }
    const muestra = Math.round(Math.sin(2 * Math.PI * f * t) * 11000 * amp);
    const off = 44 + i * 2;
    buffer[off] = muestra & 255;
    buffer[off + 1] = (muestra >> 8) & 255;
  }
  return new Blob([buffer], { type: "audio/wav" });
}

const audio = new Audio(URL.createObjectURL(wav_pago_recibido()));

function escribir_texto(b, o, t) { for (let i = 0; i < t.length; i += 1) b[o + i] = t.charCodeAt(i); }
function escribir_u32(b, o, v) { b[o]=v&255; b[o+1]=(v>>8)&255; b[o+2]=(v>>16)&255; b[o+3]=(v>>24)&255; }
function escribir_u16(b, o, v) { b[o]=v&255; b[o+1]=(v>>8)&255; }

function rebobinar() {
  try { audio.pause(); audio.currentTime = 0; } catch {}
}

function reproducir(volumen) {
  rebobinar();
  try {
    audio.volume = volumen;
    const p = audio.play();
    if (p && typeof p.catch === "function") p.catch(() => {});
    if (volumen === 0) audio.pause();
  } catch {}
}

export function desbloquear() { reproducir(0); }

export function sonar() {
  if (!leer_prefs().sonido) return;
  reproducir(1);
}

export function vibrar() {
  if (!leer_prefs().vibracion) return;
  try { if (typeof navigator.vibrate === "function") navigator.vibrate([200, 100, 200]); } catch {}
}
