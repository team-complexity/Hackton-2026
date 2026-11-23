import { desfase, formato, restante } from "./cuenta.js";
import { Escuchas } from "./escucha.js";
import { desbloquear } from "./sonido.js";
import { leer } from "./memoria.js";
import { guardar_sesion, leer_sesion } from "./sesion.js";
import {
  cancelar_cobro,
  cerrar_sesion,
  crear_cobro,
  iniciar_sesion,
  listar_cobros,
  pedir_sesion,
} from "./servidor.js";
import { aplicar_tecla } from "./teclado.js";
import {
  fijar_login_cargando,
  fijar_mostrar_qr,
  mostrar_activar_sonido,
  mostrar_ajustes,
  mostrar_ajustes_mensaje,
  mostrar_aviso_anterior,
  mostrar_barra_sesion,
  mostrar_dashboard,
  mostrar_error,
  mostrar_generando,
  mostrar_historial,
  mostrar_login,
  mostrar_login_mensaje,
  mostrar_navegacion,
  mostrar_pagado,
  mostrar_qr,
  mostrar_reconectando,
  mostrar_recuperando,
  mostrar_registro,
  mostrar_registro_mensaje,
  mostrar_teclado,
  mostrar_vencido,
  ocultar_espera,
  ocultar_navegacion,
} from "./vistas.js";

const servidor = window.PAGO_FACIL.servidor;
const CLAVE_PERFIL = "pago_facil_perfil";
const CLAVE_PREFS = "pago_facil_prefs";
const CLAVE_CIERRE = "pago_facil_cierre";

const estado = {
  vista: "teclado",
  monto: "",
  concepto: "",
  mensaje: "",
  en_pantalla: null,
  accion_en_curso: null,
  sonido_desbloqueado: false,
  qr_reabierto: false,
};

let cuenta_id = 0;
let cobro_actual = null;
let ultimo_pago = null;
let diferencia_cuenta = 0;
let mensaje_cancelar = "";
let sesion = null;
let seccion = "dashboard";
let iniciado = false;
let historial_cache = [];

function leer_json_ls(clave, defecto) {
  try { const raw = localStorage.getItem(clave); return raw ? JSON.parse(raw) : defecto; } catch { return defecto; }
}
function escribir_json_ls(clave, valor) {
  try { localStorage.setItem(clave, JSON.stringify(valor)); } catch {}
}
function leer_perfil() {
  return { negocio: "", tipo: "", whatsapp: "", correo: "", ...leer_json_ls(CLAVE_PERFIL, {}) };
}
function leer_prefs() {
  return { sonido: true, vibracion: true, pantalla: true, ...leer_json_ls(CLAVE_PREFS, {}) };
}
function guardar_perfil(p) { escribir_json_ls(CLAVE_PERFIL, p); }
function guardar_prefs(p) { escribir_json_ls(CLAVE_PREFS, p); }

function mensaje_amigable(msg) {
  const original = String(msg || "").trim();
  const m = original.toLowerCase();
  if (!m) return "Ocurrió un problema. Intenta de nuevo.";
  if (/\b[45]\d\d\b/.test(original)) return "Ocurrió un problema. Intenta de nuevo.";
  if (m.includes("fondos") || m.includes("insuficiente")) return "Fondos insuficientes. Pide a tu cliente revisar su cuenta e intentar de nuevo.";
  if (m.includes("failed to fetch") || m.includes("networkerror")) return "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo.";
  // Mensajes ya amigables del backend/UI se conservan.
  return original;
}

function pintar_pagado(cobro, pago, vigente) {
  mostrar_pagado({
    monto_recibido: pago.monto_recibido,
    concepto: typeof cobro.concepto === "string" ? cobro.concepto : "",
    monto_pedido: cobro.monto,
    monto_distinto: Boolean(pago.monto_distinto),
    numero: pago.numero,
    total: cobro.total_recibido,
    vigente,
  });
}

const escuchas = new Escuchas({
  recuperado(cobro, en_pantalla) {
    if (!estado.sonido_desbloqueado) mostrar_activar_sonido(true);
    if (en_pantalla) mostrar_cobro_recuperado(cobro);
  },
  pagado(pago, cobro) {
    cobro_actual = cobro; ultimo_pago = pago; estado.vista = "pago_recibido"; estado.qr_reabierto = false;
    const segundos = restante(cobro, diferencia_cuenta, Date.now() / 1000);
    pintar_pagado(cobro, pago, segundos >= 1);
  },
  anterior(pago, cobro) { mostrar_aviso_anterior(pago.monto_recibido, typeof cobro.concepto === "string" ? cobro.concepto : ""); },
  cancelado() { if (estado.accion_en_curso === "cancelando") return; volver_al_teclado(); },
  reconectando(visible) { mostrar_reconectando(visible); },
  vencido(cobro) { cobro_actual = cobro; estado.vista = "qr_vencido"; mostrar_vencido(cobro, true); },
  error() { parar_cuenta(); cobro_actual = null; estado.vista = "error"; estado.en_pantalla = null; mostrar_error(); },
  fin() { if (estado.vista === "recuperando") volver_al_teclado(); else ocultar_espera(); },
});

async function arrancar() {
  const token = leer_sesion();
  if (token) {
    const resultado = await pedir_sesion();
    if (resultado.sesion) { sesion = resultado.sesion; entrar_app(); return; }
    if (resultado.no_disponible) { entrar_app(); return; }
    guardar_sesion(null);
  } else {
    const resultado = await pedir_sesion();
    if (resultado.sesion) { sesion = resultado.sesion; entrar_app(); return; }
    if (resultado.no_disponible) { entrar_app(); return; }
  }
  mostrar_login("", al_entrar, al_ir_registro);
}

function entrar_app() {
  mostrar_barra_sesion(sesion, al_salir);
  if (sesion) mostrar_navegacion(seccion, ir_a); else ocultar_navegacion();
  if (!iniciado) { iniciado = true; mostrar_teclado(estado); conectar(); recuperar(); }
  if (sesion && seccion === "dashboard") { ir_a("dashboard"); }
  else if (seccion === "historial") ir_a("historial");
  else if (seccion === "ajustes") ir_a("ajustes");
  else if (seccion === "cobrar") ir_a("cobrar");
  else ir_a(sesion ? "dashboard" : "cobrar");
}

async function al_entrar(correo, clave) {
  mostrar_login_mensaje("");
  fijar_login_cargando(true);
  const resultado = await iniciar_sesion(correo, clave);
  fijar_login_cargando(false);
  if (resultado.sesion) {
    guardar_sesion(resultado.sesion.token);
    sesion = { correo: resultado.sesion.correo, plan: resultado.sesion.plan };
    const perfil = leer_perfil();
    if (!perfil.correo) { perfil.correo = sesion.correo; guardar_perfil(perfil); }
    seccion = "dashboard";
    entrar_app();
    return;
  }
  mostrar_login_mensaje(mensaje_amigable(resultado.mensaje || "No se pudo iniciar sesión."));
}

function al_ir_registro() { mostrar_registro("", al_registrar, al_ir_login); }
function al_ir_login() { mostrar_login("", al_entrar, al_ir_registro); }

async function al_registrar(datos) {
  const perfil = { negocio: datos.negocio.trim(), tipo: datos.tipo.trim(), whatsapp: datos.whatsapp.trim(), correo: datos.correo.trim().toLowerCase() };
  if (!perfil.negocio || !perfil.correo || !datos.clave) { mostrar_registro_mensaje("Completa nombre del negocio, correo y contraseña."); return; }
  guardar_perfil(perfil);
  // Sin tocar backend: intentamos iniciar sesión con las credenciales dadas.
  const resultado = await iniciar_sesion(perfil.correo, datos.clave);
  if (resultado.sesion) {
    guardar_sesion(resultado.sesion.token);
    sesion = { correo: resultado.sesion.correo, plan: resultado.sesion.plan };
    seccion = "dashboard";
    entrar_app();
    return;
  }
  mostrar_registro_mensaje("Perfil guardado en este dispositivo. Para entrar en esta demo usa la cuenta configurada del backend (demo@pagofacil.mx).");
}

async function al_salir() {
  await cerrar_sesion();
  guardar_sesion(null);
  sesion = null;
  seccion = "dashboard";
  ocultar_navegacion();
  mostrar_barra_sesion(null, al_salir);
  mostrar_login("", al_entrar, al_ir_registro);
}

function resumen_desde_cobros(cobros) {
  const hoy = new Date();
  const y = hoy.getFullYear(), m = hoy.getMonth(), d = hoy.getDate();
  let total = 0, cuenta = 0, pagados = 0, pendientes = 0;
  for (const c of cobros || []) {
    const f = new Date(Number(c.creado_en) * 1000);
    const es_hoy = f.getFullYear() === y && f.getMonth() === m && f.getDate() === d;
    if (!es_hoy) continue;
    cuenta += 1;
    if (c.estado === "pagado") { pagados += 1; total += Number(c.total_recibido || 0); }
    if (c.estado === "pendiente") pendientes += 1;
  }
  return { total, cuenta, pagados, pendientes, cobrado_hoy: total, cobros_hoy: cuenta, pagados_hoy: pagados, pendientes_hoy: pendientes };
}

async function cargar_historial() {
  const resultado = await listar_cobros();
  if (resultado.sin_sesion) { await sesion_expirada(); return null; }
  if (resultado.cobros) { historial_cache = resultado.cobros; return resultado.cobros; }
  return null;
}

async function sesion_expirada() {
  guardar_sesion(null); sesion = null; ocultar_navegacion(); mostrar_barra_sesion(null, al_salir);
  mostrar_login("Tu sesión terminó. Vuelve a entrar.", al_entrar, al_ir_registro);
}

async function ir_a(destino) {
  seccion = destino;
  if (sesion) mostrar_navegacion(seccion, ir_a);
  if (destino === "dashboard") {
    const cobros = await cargar_historial();
    if (!sesion) return;
    const perfil = leer_perfil();
    const r = resumen_desde_cobros(cobros || historial_cache);
    mostrar_dashboard({ negocio: perfil.negocio || sesion?.correo?.split("@")[0] || "tu negocio", ...r }, { cobrar: () => ir_a("cobrar"), corte: () => ir_a("historial"), ajustes: () => ir_a("ajustes") });
    return;
  }
  if (destino === "historial") {
    mostrar_historial([], "Cargando historial…", { total: 0, cuenta: 0, pagados: 0, pendientes: 0 }, al_cerrar_dia);
    const cobros = await cargar_historial();
    if (!sesion) return;
    if (cobros) mostrar_historial(cobros, "", resumen_desde_cobros(cobros), al_cerrar_dia);
    else mostrar_historial([], mensaje_amigable("No se pudo cargar el historial."), resumen_desde_cobros(historial_cache), al_cerrar_dia);
    return;
  }
  if (destino === "ajustes") {
    mostrar_ajustes(leer_perfil(), leer_prefs(), al_guardar_perfil, al_guardar_prefs);
    return;
  }
  mostrar_vista_cobro_actual();
}

function al_cerrar_dia() {
  const r = resumen_desde_cobros(historial_cache);
  escribir_json_ls(CLAVE_CIERRE, { fecha: new Date().toISOString(), ...r });
  mostrar_historial(historial_cache, "", r, al_cerrar_dia);
  const contenido = document.querySelector('[data-prueba="historial-contenido"]');
  if (contenido instanceof HTMLElement) {
    const aviso = document.createElement("div");
    aviso.className = "vacio"; aviso.style.marginBottom = "12px"; aviso.style.borderStyle = "solid"; aviso.style.borderColor = "var(--line-strong)";
    aviso.textContent = `Cierre guardado en este dispositivo · ${new Date().toLocaleString("es-MX")}`;
    contenido.prepend(aviso);
  }
}

function al_guardar_perfil(perfil) {
  const actual = leer_perfil();
  guardar_perfil({ ...actual, ...perfil });
  mostrar_ajustes_mensaje("Perfil guardado.");
  setTimeout(() => mostrar_ajustes_mensaje(""), 2000);
}
function al_guardar_prefs(prefs) {
  guardar_prefs(prefs);
  mostrar_ajustes_mensaje("Preferencias guardadas.");
  setTimeout(() => mostrar_ajustes_mensaje(""), 2000);
}

function mostrar_vista_cobro_actual() {
  if (estado.vista === "qr") { pintar_qr_actual(); return; }
  if (estado.vista === "pago_recibido" && cobro_actual && ultimo_pago) { const s = restante(cobro_actual, diferencia_cuenta, Date.now() / 1000); pintar_pagado(cobro_actual, ultimo_pago, s >= 1); return; }
  if (estado.vista === "qr_vencido" && cobro_actual) { mostrar_vencido(cobro_actual, true); return; }
  if (estado.vista === "error") { mostrar_error(); return; }
  if (estado.vista === "generando") { mostrar_generando(estado); return; }
  if (estado.vista === "recuperando") { mostrar_recuperando(); return; }
  mostrar_teclado(estado);
}

function conectar() {
  const raiz = document.getElementById("vistas");
  if (!raiz) return;
  for (const boton of raiz.querySelectorAll('[data-prueba^="tecla-"]')) boton.addEventListener("click", al_tecla);
  const concepto = raiz.querySelector('[data-prueba="concepto"]');
  if (concepto instanceof HTMLInputElement) concepto.addEventListener("input", () => { estado.concepto = concepto.value; });
  const cobrar = raiz.querySelector('[data-prueba="cobrar"]');
  if (cobrar) cobrar.addEventListener("click", () => { void al_cobrar(); });
  for (const boton of raiz.querySelectorAll('[data-prueba="nuevo-cobro"]')) boton.addEventListener("click", al_nuevo);
  const libre = raiz.querySelector('[data-prueba="monto-libre"]');
  if (libre) libre.addEventListener("click", () => { void pedir_cobro(null); });
  const otra = raiz.querySelector('[data-prueba="mostrar-qr"]');
  if (otra) otra.addEventListener("click", al_mostrar_qr);
  const cancelar = raiz.querySelector('[data-prueba="cancelar"]');
  if (cancelar) cancelar.addEventListener("click", () => { void al_cancelar(); });
  const logo = document.querySelector('[data-prueba="logo-inicio"]');
  if (logo) logo.addEventListener("click", (e) => { e.preventDefault(); if (sesion) ir_a("dashboard"); });
}

function al_nuevo() { volver_al_teclado(); }
function volver_al_teclado() {
  escuchas.pasar_a_anterior(); parar_cuenta(); cobro_actual = null;
  estado.vista = "teclado"; estado.monto = ""; estado.concepto = ""; estado.mensaje = ""; estado.en_pantalla = null; estado.qr_reabierto = false;
  ultimo_pago = null; mensaje_cancelar = ""; mostrar_reconectando(false); mostrar_teclado(estado);
}
async function al_cancelar() {
  if (estado.accion_en_curso || estado.vista !== "qr" || !cobro_actual) return;
  if (cobro_actual.estado !== "pendiente") return;
  const id = cobro_actual.id; estado.accion_en_curso = "cancelando"; mensaje_cancelar = ""; pintar_qr_actual();
  const resultado = await cancelar_cobro(id);
  if (estado.accion_en_curso !== "cancelando") return;
  estado.accion_en_curso = null;
  if (resultado.cobro) { volver_al_teclado(); return; }
  mensaje_cancelar = mensaje_amigable(resultado.mensaje ?? "");
  if (estado.vista === "qr" && cobro_actual) pintar_qr_actual();
}
function al_tecla(evento) {
  const boton = evento.currentTarget; if (!(boton instanceof HTMLElement)) return;
  const nombre = boton.getAttribute("data-prueba") ?? "";
  estado.monto = aplicar_tecla(estado.monto, nombre.slice("tecla-".length));
  estado.mensaje = ""; estado.vista = "teclado"; mostrar_teclado(estado);
}
function al_cobrar() { void pedir_cobro(Number(estado.monto)); }
async function pedir_cobro(monto) {
  if (estado.accion_en_curso) return;
  desbloquear(); estado.sonido_desbloqueado = true; estado.accion_en_curso = "creando"; estado.vista = "generando"; mostrar_generando(estado);
  const resultado = await crear_cobro(monto, estado.concepto);
  estado.accion_en_curso = null;
  if (resultado.cobro) { estado.en_pantalla = resultado.cobro.id; estado.vista = "qr"; empezar_cuenta(resultado.cobro); escuchas.poner_en_pantalla(resultado.cobro); return; }
  estado.mensaje = mensaje_amigable(resultado.mensaje ?? "");
  estado.vista = "teclado"; parar_cuenta(); mostrar_teclado(estado);
}
function al_mostrar_qr() {
  const actual = cobro_actual; if (!actual || !ultimo_pago || estado.vista !== "pago_recibido") return;
  const s = restante(actual, diferencia_cuenta, Date.now() / 1000); if (s < 1) return;
  estado.qr_reabierto = true; estado.vista = "qr"; pintar_qr_actual();
}
function parar_cuenta() { if (cuenta_id !== 0) { window.clearInterval(cuenta_id); cuenta_id = 0; } }
function pintar_qr_actual() {
  const actual = cobro_actual; if (!actual) return;
  const s = restante(actual, diferencia_cuenta, Date.now() / 1000);
  mostrar_qr({ qr_imagen: typeof actual.qr_imagen === "string" ? actual.qr_imagen : "", monto: actual.monto, concepto: typeof actual.concepto === "string" ? actual.concepto : "", cuenta: formato(s), pendiente: actual.estado === "pendiente", cancelando: estado.accion_en_curso === "cancelando", mensaje_cancelar });
}
function tiene_pagos(cobro) { return Array.isArray(cobro.pagos) && cobro.pagos.length > 0; }
function empezar_cuenta(cobro) {
  parar_cuenta(); cobro_actual = cobro; diferencia_cuenta = desfase(cobro, Date.now() / 1000);
  const pintar = () => {
    const actual = cobro_actual; if (!actual) return;
    const segundos = restante(actual, diferencia_cuenta, Date.now() / 1000);
    if (segundos < 1 && estado.qr_reabierto && ultimo_pago) { estado.qr_reabierto = false; estado.vista = "pago_recibido"; pintar_pagado(actual, ultimo_pago, false); return; }
    if (segundos < 1 && !tiene_pagos(actual) && estado.vista === "qr") { parar_cuenta(); estado.vista = "qr_vencido"; mostrar_vencido(actual, true); return; }
    if (estado.vista === "qr") pintar_qr_actual();
    if (estado.vista === "pago_recibido") fijar_mostrar_qr(segundos >= 1);
  };
  pintar(); cuenta_id = window.setInterval(pintar, 250);
}
function mostrar_cobro_recuperado(cobro) {
  mostrar_reconectando(false);
  if (cobro.estado === "cancelado") { volver_al_teclado(); return; }
  const pagos = Array.isArray(cobro.pagos) ? cobro.pagos : [];
  estado.en_pantalla = cobro.id;
  if (pagos.length > 0) { const pago = pagos[pagos.length - 1]; ultimo_pago = pago; estado.vista = "pago_recibido"; empezar_cuenta(cobro); const s = restante(cobro, diferencia_cuenta, Date.now() / 1000); pintar_pagado(cobro, pago, s >= 1); return; }
  if (cobro.estado === "vencido") { cobro_actual = cobro; estado.vista = "qr_vencido"; mostrar_vencido(cobro, true); return; }
  estado.vista = "qr"; empezar_cuenta(cobro);
}
function pedir_toque_para_sonar() {
  escuchas.fijar_sin_sonido(true);
  document.addEventListener("click", () => { escuchas.fijar_sin_sonido(false); desbloquear(); estado.sonido_desbloqueado = true; mostrar_activar_sonido(false); }, { capture: true, once: true });
}
function recuperar() {
  const recordado = leer();
  if (!recordado || (!recordado.en_pantalla && recordado.anteriores.length === 0)) return;
  pedir_toque_para_sonar();
  if (recordado.en_pantalla) { estado.vista = "recuperando"; mostrar_recuperando(); }
  escuchas.recuperar(recordado);
}

void arrancar();
export { servidor };
