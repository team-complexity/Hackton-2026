import { cobrar_activo, monto_libre_activo } from "./teclado.js";

const TEXTO_GENERANDO = "Generando QR…";
const TEXTO_CODI = "Escanéalo desde la app de tu banco, en la opción CoDi";
const TEXTO_ESPERA = "Si el cliente ya pagó, aquí te avisamos";
const TEXTO_ERROR =
  "Este cobro ya no se puede seguir. Revisa la app de tu banco para confirmar si llegó el pago.";

let listas = false;

function raiz_vistas() { return document.getElementById("vistas"); }

function pesos(valor) {
  const numero = Number(valor);
  if (!Number.isFinite(numero)) return "";
  return `$${numero.toFixed(2)}`;
}
function texto_monto(valor) {
  return typeof valor === "number" && Number.isFinite(valor) ? pesos(valor) : "Monto libre";
}
function fecha_corta(segundos) {
  const fecha = new Date(Number(segundos) * 1000);
  if (Number.isNaN(fecha.getTime())) return "";
  return fecha.toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" });
}
function esc(texto) {
  const d = document.createElement("div");
  d.textContent = texto == null ? "" : String(texto);
  return d.innerHTML;
}

function asegurar() {
  if (listas) return;
  const raiz = raiz_vistas();
  if (!raiz) return;
  listas = true;
  const panel = document.createElement("section");
  panel.className = "panel cobro-panel";
  panel.setAttribute("data-prueba", "panel-cobro");
  panel.append(crear_teclado(), crear_generando(), crear_qr(), crear_vencido(), crear_pagado(), crear_error());
  raiz.append(panel);
}

function crear_tecla(nombre, texto) {
  const b = document.createElement("button");
  b.type = "button"; b.setAttribute("data-prueba", nombre); b.textContent = texto; return b;
}
function crear_nuevo_cobro() {
  const b = document.createElement("button");
  b.type = "button"; b.setAttribute("data-prueba", "nuevo-cobro"); b.textContent = "Nuevo cobro"; return b;
}

function crear_teclado() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-teclado");
  vista.hidden = true;
  vista.innerHTML = `
    <div class="cobro-layout">
      <div>
        <span class="kicker">Cobro</span>
        <p class="etiqueta" style="margin:0;color:var(--muted);font-size:.88rem">Monto a cobrar</p>
        <p data-prueba="monto"></p>
        <div class="teclas"></div>
        <div class="campo-concepto campo">
          <label for="concepto-cobro">Concepto (opcional)</label>
          <input id="concepto-cobro" type="text" data-prueba="concepto" maxlength="40" placeholder="Ej. Tacos, corte, servicio">
        </div>
        <div class="acciones-teclado">
          <button type="button" data-prueba="cobrar">Cobrar</button>
          <button type="button" data-prueba="monto-libre">Monto libre</button>
        </div>
        <p data-prueba="mensaje"></p>
        <p class="ayuda">Teclea el monto, agrega un concepto si quieres y genera el QR CoDi.</p>
      </div>
      <div class="panel" style="padding:20px;border-style:dashed">
        <span class="kicker">Así de fácil</span>
        <p style="margin:0 0 8px;font-family:var(--font-head);font-size:1.2rem">Del monto al QR en segundos</p>
        <p class="texto-suave" style="margin:0">Tu cliente escanea con la app de su banco. Cuando el pago llega, verás la confirmación y sonará tu caja.</p>
      </div>
    </div>`;
  const teclas = vista.querySelector(".teclas");
  for (const d of ["1","2","3","4","5","6","7","8","9"]) teclas.append(crear_tecla(`tecla-${d}`, d));
  teclas.append(crear_tecla("tecla-punto", "."), crear_tecla("tecla-0", "0"), crear_tecla("tecla-borrar", "Borrar"));
  return vista;
}

function crear_generando() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-generando");
  vista.hidden = true;
  vista.className = "estado-centro";
  vista.innerHTML = `<p data-prueba="generando">${TEXTO_GENERANDO}</p><span class="cargando" aria-hidden="true"></span>`;
  return vista;
}

function crear_qr() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-qr");
  vista.hidden = true;
  vista.className = "qr-tarjeta";
  const img = document.createElement("img"); img.setAttribute("data-prueba","qr"); img.alt = "QR";
  const monto = document.createElement("p"); monto.setAttribute("data-prueba","qr-monto");
  const concepto = document.createElement("p"); concepto.setAttribute("data-prueba","qr-concepto");
  const ind = document.createElement("p"); ind.setAttribute("data-prueba","indicacion-codi"); ind.textContent = TEXTO_CODI;
  const cuenta = document.createElement("p"); cuenta.setAttribute("data-prueba","cuenta");
  const acciones = document.createElement("div"); acciones.className = "qr-acciones";
  const cancelar = document.createElement("button"); cancelar.type="button"; cancelar.setAttribute("data-prueba","cancelar"); cancelar.textContent="Cancelar cobro"; cancelar.hidden=true;
  const msg = document.createElement("p"); msg.setAttribute("data-prueba","mensaje-cancelar"); msg.hidden=true;
  acciones.append(cancelar, msg, crear_nuevo_cobro());
  vista.append(img, monto, concepto, ind, cuenta, acciones);
  return vista;
}

function crear_vencido() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-vencido");
  vista.hidden = true;
  vista.className = "estado-vencido";
  const t = document.createElement("p"); t.setAttribute("data-prueba","vencido"); t.textContent="QR vencido";
  const m = document.createElement("p"); m.setAttribute("data-prueba","vencido-monto");
  const c = document.createElement("p"); c.setAttribute("data-prueba","vencido-concepto");
  const e = document.createElement("p"); e.setAttribute("data-prueba","vencido-espera"); e.textContent=TEXTO_ESPERA;
  const a = document.createElement("div"); a.className="qr-acciones"; a.append(crear_nuevo_cobro());
  vista.append(t,m,c,e,a);
  return vista;
}

function crear_error() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-error");
  vista.hidden = true;
  vista.className = "estado-error";
  const icon = document.createElement("div"); icon.className = "error-icono"; icon.textContent = "!";
  icon.setAttribute("aria-hidden","true");
  const t = document.createElement("p"); t.setAttribute("data-prueba","error"); t.textContent = TEXTO_ERROR;
  const a = document.createElement("div"); a.className="qr-acciones"; a.append(crear_nuevo_cobro());
  vista.append(icon, t, a);
  return vista;
}

function crear_pagado() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-pagado");
  vista.hidden = true;
  const t = document.createElement("p"); t.setAttribute("data-prueba","pagado"); t.textContent="Pago recibido";
  const m = document.createElement("p"); m.setAttribute("data-prueba","pagado-monto");
  const c = document.createElement("p"); c.setAttribute("data-prueba","pagado-concepto");
  const d = document.createElement("p"); d.setAttribute("data-prueba","pagado-distinto"); d.hidden=true;
  const n = document.createElement("p"); n.setAttribute("data-prueba","pagado-numero"); n.hidden=true;
  const tot = document.createElement("p"); tot.setAttribute("data-prueba","pagado-total"); tot.hidden=true;
  const a = document.createElement("div"); a.className="qr-acciones";
  const o = document.createElement("button"); o.type="button"; o.setAttribute("data-prueba","mostrar-qr"); o.textContent="Mostrar QR otra vez"; o.hidden=true;
  a.append(o, crear_nuevo_cobro());
  vista.append(t,m,c,d,n,tot,a);
  return vista;
}

function ocultar_extras() {
  const raiz = raiz_vistas();
  if (!raiz) return;
  for (const sel of ['[data-prueba="vista-login"]','[data-prueba="vista-registro"]','[data-prueba="vista-dashboard"]','[data-prueba="vista-historial"]','[data-prueba="vista-ajustes"]']) {
    const n = raiz.querySelector(sel);
    if (n instanceof HTMLElement) n.hidden = true;
  }
}

function mostrar_solo(nombre) {
  asegurar();
  const raiz = raiz_vistas();
  if (!raiz) return;
  ocultar_extras();
  const panel = raiz.querySelector('[data-prueba="panel-cobro"]');
  if (panel instanceof HTMLElement) panel.hidden = false;
  for (const nodo of raiz.querySelectorAll('[data-prueba^="vista-"]')) {
    if (!(nodo instanceof HTMLElement)) continue;
    const p = nodo.getAttribute("data-prueba") || "";
    if (["vista-login","vista-registro","vista-dashboard","vista-historial","vista-ajustes"].includes(p)) continue;
    nodo.hidden = p !== nombre;
  }
}

export function mostrar_recuperando() { asegurar(); mostrar_solo(null); mostrar_reconectando(true); }

export function mostrar_teclado(estado) {
  asegurar();
  const monto = document.querySelector('[data-prueba="monto"]');
  const concepto = document.querySelector('[data-prueba="concepto"]');
  const cobrar = document.querySelector('[data-prueba="cobrar"]');
  const mensaje = document.querySelector('[data-prueba="mensaje"]');
  if (monto) monto.textContent = `$${estado.monto ?? ""}`;
  if (concepto instanceof HTMLInputElement) concepto.value = estado.concepto ?? "";
  if (cobrar instanceof HTMLButtonElement) cobrar.disabled = !cobrar_activo(estado.monto ?? "");
  const libre = document.querySelector('[data-prueba="monto-libre"]');
  if (libre instanceof HTMLButtonElement) libre.disabled = !monto_libre_activo(estado.monto ?? "");
  if (mensaje) mensaje.textContent = estado.mensaje ?? "";
  mostrar_solo("vista-teclado");
}

export function mostrar_generando(_estado) {
  asegurar();
  const g = document.querySelector('[data-prueba="generando"]');
  if (g) g.textContent = TEXTO_GENERANDO;
  mostrar_solo("vista-generando");
}

export function mostrar_qr(datos) {
  asegurar();
  const img = document.querySelector('[data-prueba="qr"]');
  if (img instanceof HTMLImageElement) {
    const src = `data:image/png;base64,${datos.qr_imagen ?? ""}`;
    if (img.getAttribute("src") !== src) img.setAttribute("src", src);
  }
  const monto = document.querySelector('[data-prueba="qr-monto"]'); if (monto) monto.textContent = texto_monto(datos.monto);
  const concepto = document.querySelector('[data-prueba="qr-concepto"]'); if (concepto) concepto.textContent = datos.concepto ?? "";
  const ind = document.querySelector('[data-prueba="indicacion-codi"]'); if (ind) ind.textContent = TEXTO_CODI;
  const cuenta = document.querySelector('[data-prueba="cuenta"]'); if (cuenta) cuenta.textContent = datos.cuenta ?? "";
  const cancelar = document.querySelector('[data-prueba="cancelar"]');
  if (cancelar instanceof HTMLButtonElement) { cancelar.hidden = !datos.pendiente; cancelar.textContent = datos.cancelando ? "Cancelando…" : "Cancelar cobro"; }
  const msg = document.querySelector('[data-prueba="mensaje-cancelar"]');
  if (msg) { const t = datos.mensaje_cancelar ?? ""; msg.textContent = t; msg.hidden = t === ""; }
  mostrar_solo("vista-qr");
}

export function mostrar_pagado(datos) {
  asegurar();
  const t = document.querySelector('[data-prueba="pagado"]'); if (t) t.textContent = "Pago recibido";
  const m = document.querySelector('[data-prueba="pagado-monto"]'); if (m) m.textContent = pesos(datos.monto_recibido);
  const c = document.querySelector('[data-prueba="pagado-concepto"]'); if (c) c.textContent = datos.concepto ?? "";
  const d = document.querySelector('[data-prueba="pagado-distinto"]');
  if (d) {
    if (datos.monto_distinto) { d.hidden=false; d.textContent = `Pediste ${pesos(datos.monto_pedido)}, recibiste ${pesos(datos.monto_recibido)}`; }
    else { d.hidden=true; d.textContent=""; }
  }
  const n = document.querySelector('[data-prueba="pagado-numero"]');
  const tot = document.querySelector('[data-prueba="pagado-total"]');
  const segundo = Number(datos.numero) >= 2;
  if (n) { n.hidden=!segundo; n.textContent = segundo ? `Pago ${datos.numero}` : ""; }
  if (tot) { tot.hidden=!segundo; tot.textContent = segundo ? `Total recibido: ${pesos(datos.total)}` : ""; }
  const o = document.querySelector('[data-prueba="mostrar-qr"]'); if (o) o.hidden = !datos.vigente;
  mostrar_solo("vista-pagado");
}

export function fijar_mostrar_qr(visible) { const o = document.querySelector('[data-prueba="mostrar-qr"]'); if (o) o.hidden = !visible; }

export function mostrar_vencido(cobro, con_espera) {
  asegurar();
  const t = document.querySelector('[data-prueba="vencido"]'); if (t) t.textContent = "QR vencido";
  const m = document.querySelector('[data-prueba="vencido-monto"]'); if (m) m.textContent = texto_monto(cobro.monto);
  const c = document.querySelector('[data-prueba="vencido-concepto"]'); if (c) c.textContent = cobro.concepto ?? "";
  const e = document.querySelector('[data-prueba="vencido-espera"]'); if (e) { e.textContent = TEXTO_ESPERA; e.hidden = !con_espera; }
  mostrar_solo("vista-vencido");
}
export function ocultar_espera() { const e = document.querySelector('[data-prueba="vencido-espera"]'); if (e) e.hidden = true; }
export function mostrar_error() { asegurar(); const t = document.querySelector('[data-prueba="error"]'); if (t) t.textContent = TEXTO_ERROR; mostrar_solo("vista-error"); }

export function mostrar_aviso_anterior(monto, concepto) {
  const raiz = raiz_vistas(); if (!raiz) return;
  let caja = raiz.querySelector('[data-prueba="avisos-anteriores"]');
  if (!(caja instanceof HTMLElement)) { caja = document.createElement("div"); caja.setAttribute("data-prueba","avisos-anteriores"); raiz.append(caja); }
  const aviso = document.createElement("button"); aviso.type="button"; aviso.setAttribute("data-prueba","aviso-anterior");
  aviso.textContent = `Pago de un cobro anterior: ${pesos(monto)} ${concepto}`.trim();
  aviso.addEventListener("click", () => { aviso.hidden = true; });
  caja.append(aviso);
}
export function mostrar_activar_sonido(visible) {
  const raiz = raiz_vistas(); if (!raiz) return;
  let a = raiz.querySelector('[data-prueba="activar-sonido"]');
  if (!(a instanceof HTMLElement)) { a = document.createElement("p"); a.setAttribute("data-prueba","activar-sonido"); raiz.append(a); }
  a.textContent = "Toca para activar el sonido"; a.hidden = !visible;
}
export function mostrar_reconectando(visible) {
  const raiz = raiz_vistas(); if (!raiz) return;
  let a = raiz.querySelector('[data-prueba="reconectando"]');
  if (!(a instanceof HTMLElement)) { a = document.createElement("p"); a.setAttribute("data-prueba","reconectando"); raiz.append(a); }
  a.textContent = "Reconectando…"; a.hidden = !visible;
}

/* ---- Shell / nuevas pantallas ---- */
export function mostrar_barra_sesion(sesion, al_salir) {
  const acciones = document.querySelector('[data-prueba="barra-acciones"]');
  if (!(acciones instanceof HTMLElement)) return;
  acciones.replaceChildren();
  if (!sesion) return;
  const correo = document.createElement("span");
  correo.className = "muted";
  correo.style.fontSize = ".85rem";
  correo.setAttribute("data-prueba","usuario-correo");
  correo.textContent = sesion.correo || "";
  const salir = document.createElement("button");
  salir.type = "button"; salir.className = "btn-ghost"; salir.style.width="auto"; salir.style.minHeight="40px"; salir.style.padding="8px 12px";
  salir.setAttribute("data-prueba","salir"); salir.textContent = "Salir";
  salir.addEventListener("click", al_salir);
  acciones.append(correo, salir);
}

export function mostrar_navegacion(actual, al_ir) {
  const nav = document.querySelector('[data-prueba="navegacion"]');
  if (!(nav instanceof HTMLElement)) return;
  nav.hidden = false; nav.replaceChildren();
  for (const [id, texto] of [["dashboard","Inicio"],["cobrar","Cobrar"],["historial","Corte"],["ajustes","Ajustes"]]) {
    const b = document.createElement("button");
    b.type="button"; b.className="nav-boton"; b.setAttribute("data-prueba",`nav-${id}`); b.textContent = texto;
    if (actual === id) b.setAttribute("aria-current","page");
    b.addEventListener("click", () => al_ir(id));
    nav.append(b);
  }
}
export function ocultar_navegacion() {
  const nav = document.querySelector('[data-prueba="navegacion"]');
  if (nav instanceof HTMLElement) { nav.hidden = true; nav.replaceChildren(); }
}

function ocultar_panel_cobro() { const p = raiz_vistas()?.querySelector('[data-prueba="panel-cobro"]'); if (p instanceof HTMLElement) p.hidden = true; }

function asegurar_login() {
  const raiz = raiz_vistas(); if (!raiz) return null;
  let v = raiz.querySelector('[data-prueba="vista-login"]');
  if (v instanceof HTMLElement) return v;
  v = document.createElement("section");
  v.className = "panel panel-pad auth-wrap anim-in";
  v.setAttribute("data-prueba","vista-login"); v.hidden = true;
  v.innerHTML = `
    <span class="kicker">Acceso</span>
    <h2 class="titulo-panel">Entra a tu caja</h2>
    <p class="texto-suave">Inicia sesión para cobrar, ver tu historial y ajustar tu negocio.</p>
    <form data-prueba="form-login" novalidate>
      <div class="campo"><label for="login-correo">Correo</label><input id="login-correo" data-prueba="login-correo" type="email" autocomplete="username" placeholder="demo@pagofacil.mx"></div>
      <div class="campo"><label for="login-clave">Contraseña</label><input id="login-clave" data-prueba="login-clave" type="password" autocomplete="current-password" placeholder="Tu contraseña"></div>
      <p data-prueba="login-mensaje" class="mensaje-error"></p>
      <div style="margin-top:16px"><button type="submit" data-prueba="entrar">Entrar</button></div>
    </form>
    <div class="auth-alt">
      <p>¿Aún no tienes cuenta?</p>
      <button type="button" data-prueba="ir-registro">Registrar mi negocio</button>
    </div>`;
  raiz.append(v);
  return v;
}

export function mostrar_login(mensaje, al_entrar, al_ir_registro) {
  asegurar();
  const v = asegurar_login(); if (!v) return;
  ocultar_panel_cobro(); ocultar_extras(); v.hidden = false;
  const msg = v.querySelector('[data-prueba="login-mensaje"]'); if (msg) msg.textContent = mensaje || "";
  const form = v.querySelector('[data-prueba="form-login"]');
  if (form instanceof HTMLFormElement && !form.dataset.listo) {
    form.dataset.listo = "1";
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const c = v.querySelector('[data-prueba="login-correo"]');
      const p = v.querySelector('[data-prueba="login-clave"]');
      al_entrar(c instanceof HTMLInputElement ? c.value : "", p instanceof HTMLInputElement ? p.value : "");
    });
  }
  const ir = v.querySelector('[data-prueba="ir-registro"]');
  if (ir instanceof HTMLButtonElement && !ir.dataset.listo) { ir.dataset.listo="1"; ir.addEventListener("click", al_ir_registro); }
}
export function fijar_login_cargando(cargando) {
  const b = document.querySelector('[data-prueba="entrar"]');
  if (b instanceof HTMLButtonElement) { b.disabled = cargando; b.textContent = cargando ? "Entrando…" : "Entrar"; }
}
export function mostrar_login_mensaje(m) { const e = document.querySelector('[data-prueba="login-mensaje"]'); if (e) e.textContent = m || ""; }

function asegurar_registro() {
  const raiz = raiz_vistas(); if (!raiz) return null;
  let v = raiz.querySelector('[data-prueba="vista-registro"]');
  if (v instanceof HTMLElement) return v;
  v = document.createElement("section");
  v.className = "panel panel-pad auth-wrap anim-in";
  v.setAttribute("data-prueba","vista-registro"); v.hidden = true;
  v.innerHTML = `
    <span class="kicker">Registro</span>
    <h2 class="titulo-panel">Registra tu negocio</h2>
    <p class="texto-suave">Crea el perfil de tu negocio. Tus datos se guardan en este dispositivo para la demo.</p>
    <form data-prueba="form-registro" novalidate>
      <div class="campo"><label for="reg-negocio">Nombre del negocio</label><input id="reg-negocio" data-prueba="reg-negocio" type="text" placeholder="Mi tiendita"></div>
      <div class="campo"><label for="reg-tipo">Tipo de negocio</label><select id="reg-tipo" data-prueba="reg-tipo"><option value="">Elige una opción</option><option>Tiendita / abarrotes</option><option>Puesto o comercio de calle</option><option>Ferretería</option><option>Tortillería</option><option>Otro</option></select></div>
      <div class="campo"><label for="reg-correo">Correo</label><input id="reg-correo" data-prueba="reg-correo" type="email" autocomplete="email" placeholder="correo@negocio.com"></div>
      <div class="campo"><label for="reg-whatsapp">WhatsApp</label><input id="reg-whatsapp" data-prueba="reg-whatsapp" type="tel" placeholder="10 dígitos"></div>
      <div class="campo"><label for="reg-clave">Contraseña</label><input id="reg-clave" data-prueba="reg-clave" type="password" autocomplete="new-password" placeholder="Crea una contraseña"></div>
      <p data-prueba="registro-mensaje" class="mensaje-error"></p>
      <div style="margin-top:16px"><button type="submit" data-prueba="registrar">Crear cuenta</button></div>
    </form>
    <div class="auth-alt"><p>¿Ya tienes cuenta?</p><button type="button" data-prueba="ir-login">Volver a iniciar sesión</button></div>`;
  raiz.append(v);
  return v;
}

export function mostrar_registro(mensaje, al_registrar, al_ir_login) {
  asegurar();
  const v = asegurar_registro(); if (!v) return;
  ocultar_panel_cobro(); ocultar_extras(); v.hidden = false;
  const msg = v.querySelector('[data-prueba="registro-mensaje"]'); if (msg) msg.textContent = mensaje || "";
  const form = v.querySelector('[data-prueba="form-registro"]');
  if (form instanceof HTMLFormElement && !form.dataset.listo) {
    form.dataset.listo = "1";
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const dato = (s) => { const n = v.querySelector(s); return n instanceof HTMLInputElement || n instanceof HTMLSelectElement ? n.value : ""; };
      al_registrar({ negocio: dato('[data-prueba="reg-negocio"]'), tipo: dato('[data-prueba="reg-tipo"]'), correo: dato('[data-prueba="reg-correo"]'), whatsapp: dato('[data-prueba="reg-whatsapp"]'), clave: dato('[data-prueba="reg-clave"]') });
    });
  }
  const ir = v.querySelector('[data-prueba="ir-login"]');
  if (ir instanceof HTMLButtonElement && !ir.dataset.listo) { ir.dataset.listo="1"; ir.addEventListener("click", al_ir_login); }
}
export function mostrar_registro_mensaje(m) { const e = document.querySelector('[data-prueba="registro-mensaje"]'); if (e) e.textContent = m || ""; }

function asegurar_dashboard() {
  const raiz = raiz_vistas(); if (!raiz) return null;
  let v = raiz.querySelector('[data-prueba="vista-dashboard"]');
  if (v instanceof HTMLElement) return v;
  v = document.createElement("section");
  v.className = "dash-grid anim-in";
  v.setAttribute("data-prueba","vista-dashboard"); v.hidden = true;
  raiz.append(v);
  return v;
}

export function mostrar_dashboard(datos, acciones) {
  asegurar();
  const v = asegurar_dashboard(); if (!v) return;
  ocultar_panel_cobro(); ocultar_extras(); v.hidden = false;
  const nombre = datos.negocio || "tu negocio";
  v.innerHTML = `
    <div class="panel dash-hero">
      <div>
        <span class="kicker">Dashboard</span>
        <h2 class="dash-saludo">Hola, ${esc(nombre)}</h2>
        <p class="texto-suave">Tu caja digital está lista. Cobra rápido y lleva control de tu día.</p>
      </div>
      <div class="dash-stats">
        <div class="stat-card"><span class="stat-label">Cobrado hoy</span><div class="stat-valor">${esc(pesos(datos.cobrado_hoy))}</div></div>
        <div class="stat-card"><span class="stat-label">Cobros hoy</span><div class="stat-valor">${esc(String(datos.cobros_hoy))}</div></div>
        <div class="stat-card"><span class="stat-label">Pagados</span><div class="stat-valor">${esc(String(datos.pagados_hoy))}</div></div>
        <div class="stat-card"><span class="stat-label">Pendientes</span><div class="stat-valor">${esc(String(datos.pendientes_hoy))}</div></div>
      </div>
    </div>
    <div class="acciones-grid">
      <button type="button" class="accion-card" data-prueba="dash-cobrar"><div class="accion-top"><h3 class="accion-titulo">Cobrar con QR</h3><span class="pill" style="font-size:.7rem;padding:4px 10px;border-radius:999px;border:1px solid var(--line-strong);color:var(--neon-soft)">Rápido</span></div><p class="accion-desc">Teclea el monto, genera el QR CoDi y recibe la confirmación al instante.</p></button>
      <button type="button" class="accion-card" data-prueba="dash-corte"><div class="accion-top"><h3 class="accion-titulo">Corte de caja</h3></div><p class="accion-desc">Revisa el resumen del día y el historial de cobros.</p></button>
      <button type="button" class="accion-card" data-prueba="dash-ajustes"><div class="accion-top"><h3 class="accion-titulo">Ajustes</h3></div><p class="accion-desc">Edita el perfil de tu negocio y preferencias de la app.</p></button>
      <div class="accion-card" data-prueba="dash-chatbot">
        <div class="accion-top"><h3 class="accion-titulo">Chatbot de apoyo</h3><span class="corona">Premium</span></div>
        <p class="accion-desc">Resuelve dudas sobre tus cobros dentro de la app.</p>
        <div class="chat-caja">
          <div class="chat-log" data-prueba="chat-log"><div class="chat-msg chat-bot">Hola 👋 Soy tu asistente de PAGO FÁCIL. ¿En qué te ayudo?</div></div>
          <div class="chat-row"><input data-prueba="chat-input" type="text" placeholder="Escribe tu duda..." aria-label="Mensaje al chatbot"><button type="button" class="btn-primary" data-prueba="chat-enviar" style="width:auto">Enviar</button></div>
        </div>
      </div>
    </div>`;
  v.querySelector('[data-prueba="dash-cobrar"]')?.addEventListener("click", acciones.cobrar);
  v.querySelector('[data-prueba="dash-corte"]')?.addEventListener("click", acciones.corte);
  v.querySelector('[data-prueba="dash-ajustes"]')?.addEventListener("click", acciones.ajustes);
  const enviar = () => {
    const input = v.querySelector('[data-prueba="chat-input"]');
    const log = v.querySelector('[data-prueba="chat-log"]');
    if (!(input instanceof HTMLInputElement) || !(log instanceof HTMLElement)) return;
    const texto = input.value.trim();
    if (!texto) return;
    const u = document.createElement("div"); u.className="chat-msg chat-user"; u.textContent = texto; log.append(u);
    const b = document.createElement("div"); b.className="chat-msg chat-bot";
    b.textContent = "Puedo ayudarte con cobros, QR y cortes de caja. Esta función está activa en modo demo premium 👑.";
    log.append(b); input.value = ""; log.scrollTop = log.scrollHeight;
  };
  v.querySelector('[data-prueba="chat-enviar"]')?.addEventListener("click", enviar);
  v.querySelector('[data-prueba="chat-input"]')?.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); enviar(); } });
}

function asegurar_historial() {
  const raiz = raiz_vistas(); if (!raiz) return null;
  let v = raiz.querySelector('[data-prueba="vista-historial"]');
  if (v instanceof HTMLElement) return v;
  v = document.createElement("section");
  v.className = "panel panel-pad anim-in";
  v.setAttribute("data-prueba","vista-historial"); v.hidden = true;
  raiz.append(v);
  return v;
}

export function mostrar_historial(cobros, mensaje = "", resumen = null, al_cerrar_dia = null) {
  asegurar();
  const v = asegurar_historial(); if (!v) return;
  ocultar_panel_cobro(); ocultar_extras(); v.hidden = false;
  const r = resumen || { total: 0, cuenta: 0, pagados: 0, pendientes: 0 };
  v.innerHTML = `
    <div class="historial-encabezado">
      <div><span class="kicker">Corte de caja</span><h2 class="titulo-panel">Resumen e historial</h2><p class="texto-suave">Revisa tus cobros y el resumen del día.</p></div>
      ${al_cerrar_dia ? '<button type="button" class="btn-ghost" data-prueba="cerrar-dia" style="width:auto">Cerrar día</button>' : ''}
    </div>
    <div class="resumen-corte">
      <div class="corte-card"><div class="corte-valor">${esc(pesos(r.total))}</div><div class="corte-label">Cobrado hoy</div></div>
      <div class="corte-card"><div class="corte-valor">${esc(String(r.cuenta))}</div><div class="corte-label">Cobros hoy</div></div>
      <div class="corte-card"><div class="corte-valor">${esc(String(r.pagados))}</div><div class="corte-label">Pagados</div></div>
      <div class="corte-card"><div class="corte-valor">${esc(String(r.pendientes))}</div><div class="corte-label">Pendientes</div></div>
    </div>
    <div data-prueba="historial-contenido"></div>`;
  if (al_cerrar_dia) v.querySelector('[data-prueba="cerrar-dia"]')?.addEventListener("click", al_cerrar_dia);
  const contenido = v.querySelector('[data-prueba="historial-contenido"]');
  if (!(contenido instanceof HTMLElement)) return;
  contenido.replaceChildren();
  if (mensaje) { const e = document.createElement("p"); e.className="mensaje-error"; e.setAttribute("data-prueba","historial-mensaje"); e.textContent = mensaje; contenido.append(e); return; }
  if (!Array.isArray(cobros) || cobros.length === 0) { const vacio = document.createElement("div"); vacio.className="vacio"; vacio.setAttribute("data-prueba","historial-vacio"); vacio.textContent = "Todavía no hay cobros. Cuando generes uno, aparecerá aquí."; contenido.append(vacio); return; }
  const lista = document.createElement("div"); lista.className="historial-lista"; lista.setAttribute("data-prueba","historial-lista");
  for (const cobro of cobros) {
    const item = document.createElement("article"); item.className="historial-item"; item.setAttribute("data-prueba","historial-item");
    const fila = document.createElement("div"); fila.className="historial-fila";
    const iz = document.createElement("div");
    const m = document.createElement("p"); m.className="historial-monto"; m.textContent = texto_monto(cobro.monto);
    const c = document.createElement("p"); c.className="historial-concepto"; c.textContent = typeof cobro.concepto === "string" ? cobro.concepto : "";
    iz.append(m,c);
    const est = document.createElement("span"); est.className = `estado-cobro estado-${cobro.estado || "pendiente"}`;
    est.textContent = ({pendiente:"Pendiente", pagado:"Pagado", vencido:"Vencido", cancelado:"Cancelado"})[cobro.estado] || cobro.estado;
    fila.append(iz, est);
    const meta = document.createElement("p"); meta.className="historial-meta";
    const pagos = Number(cobro.numero_de_pagos); const total = Number(cobro.total_recibido);
    const partes = [fecha_corta(cobro.creado_en)];
    if (pagos > 0) { partes.push(`${pagos} pago${pagos===1?"":"s"}`); partes.push(`Total ${pesos(total)}`); }
    meta.textContent = partes.filter(Boolean).join(" · ");
    item.append(fila, meta); lista.append(item);
  }
  contenido.append(lista);
}

function asegurar_ajustes() {
  const raiz = raiz_vistas(); if (!raiz) return null;
  let v = raiz.querySelector('[data-prueba="vista-ajustes"]');
  if (v instanceof HTMLElement) return v;
  v = document.createElement("section"); v.className="panel panel-pad anim-in"; v.setAttribute("data-prueba","vista-ajustes"); v.hidden=true; raiz.append(v); return v;
}

export function mostrar_ajustes(perfil, prefs, al_guardar_perfil, al_guardar_prefs) {
  asegurar();
  const v = asegurar_ajustes(); if (!v) return;
  ocultar_panel_cobro(); ocultar_extras(); v.hidden = false;
  v.innerHTML = `
    <span class="kicker">Ajustes</span>
    <h2 class="titulo-panel">Tu negocio y preferencias</h2>
    <p class="texto-suave">Personaliza tu perfil y cómo se comporta la app en este dispositivo.</p>
    <div class="ajustes-grid" style="margin-top:20px">
      <div class="ajuste-card">
        <h3>Perfil del negocio</h3>
        <p>Estos datos se guardan localmente en este dispositivo.</p>
        <form data-prueba="form-perfil" novalidate>
          <div class="campo"><label for="perfil-negocio">Nombre del negocio</label><input id="perfil-negocio" data-prueba="perfil-negocio" value="${esc(perfil.negocio||"")}"></div>
          <div class="campo"><label for="perfil-tipo">Tipo de negocio</label><input id="perfil-tipo" data-prueba="perfil-tipo" value="${esc(perfil.tipo||"")}"></div>
          <div class="campo"><label for="perfil-whatsapp">WhatsApp</label><input id="perfil-whatsapp" data-prueba="perfil-whatsapp" value="${esc(perfil.whatsapp||"")}"></div>
          <div class="campo"><label for="perfil-correo">Correo</label><input id="perfil-correo" data-prueba="perfil-correo" value="${esc(perfil.correo||"")}"></div>
          <p data-prueba="ajustes-mensaje" class="mensaje-error"></p>
          <div style="margin-top:16px"><button type="submit" data-prueba="guardar-perfil">Guardar perfil</button></div>
        </form>
      </div>
      <div class="ajuste-card">
        <h3>Preferencias</h3>
        <p>Elige cómo quieres recibir avisos al cobrar.</p>
        <div class="switch-row"><label for="pref-sonido">Sonido de pago recibido</label><input id="pref-sonido" data-prueba="pref-sonido" type="checkbox" ${prefs.sonido ? "checked" : ""}></div>
        <div class="switch-row"><label for="pref-vibracion">Vibración</label><input id="pref-vibracion" data-prueba="pref-vibracion" type="checkbox" ${prefs.vibracion ? "checked" : ""}></div>
        <div class="switch-row"><label for="pref-pantalla">Mantener pantalla activa</label><input id="pref-pantalla" data-prueba="pref-pantalla" type="checkbox" ${prefs.pantalla ? "checked" : ""}></div>
        <div style="margin-top:16px"><button type="button" class="btn-ghost" data-prueba="guardar-ajustes">Guardar preferencias</button></div>
      </div>
    </div>`;
  v.querySelector('[data-prueba="form-perfil"]')?.addEventListener("submit", (e) => {
    e.preventDefault();
    const val = (s) => { const n = v.querySelector(s); return n instanceof HTMLInputElement ? n.value : ""; };
    al_guardar_perfil({ negocio: val('[data-prueba="perfil-negocio"]'), tipo: val('[data-prueba="perfil-tipo"]'), whatsapp: val('[data-prueba="perfil-whatsapp"]'), correo: val('[data-prueba="perfil-correo"]') });
  });
  v.querySelector('[data-prueba="guardar-ajustes"]')?.addEventListener("click", () => {
    const chk = (s) => { const n = v.querySelector(s); return n instanceof HTMLInputElement ? n.checked : false; };
    al_guardar_prefs({ sonido: chk('[data-prueba="pref-sonido"]'), vibracion: chk('[data-prueba="pref-vibracion"]'), pantalla: chk('[data-prueba="pref-pantalla"]') });
  });
}
export function mostrar_ajustes_mensaje(m) { const e = document.querySelector('[data-prueba="ajustes-mensaje"]'); if (e) e.textContent = m || ""; }
