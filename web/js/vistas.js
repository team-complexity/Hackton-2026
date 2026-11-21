import { cobrar_activo, monto_libre_activo } from "./teclado.js";

const TEXTO_GENERANDO = "Generando QR…";
const TEXTO_CODI = "Escanéalo desde la app de tu banco, en la opción CoDi";
const TEXTO_ESPERA = "Si el cliente ya pagó, aquí te avisamos";
const TEXTO_ERROR =
  "Este cobro ya no se puede seguir. Revisa la app de tu banco para confirmar si llegó el pago.";
let listas = false;

/**
 * Deja en el DOM el Teclado y Generando QR, ocultos hasta que una vista los muestre
 * (spec 002, RF-001, RF-010).
 */
function asegurar() {
  if (listas) {
    return;
  }
  const raiz = document.getElementById("vistas");
  if (!raiz) {
    return;
  }
  listas = true;
  raiz.append(
    crear_teclado(),
    crear_generando(),
    crear_qr(),
    crear_vencido(),
    crear_pagado(),
    crear_error(),
  );
}

/**
 * @returns {HTMLElement}
 */
function crear_teclado() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-teclado");
  vista.hidden = true;

  const monto = document.createElement("p");
  monto.setAttribute("data-prueba", "monto");
  vista.append(monto);

  const teclas = document.createElement("div");
  teclas.className = "teclas";
  for (const digito of ["1", "2", "3", "4", "5", "6", "7", "8", "9"]) {
    teclas.append(crear_tecla(`tecla-${digito}`, digito));
  }
  teclas.append(crear_tecla("tecla-punto", "."));
  teclas.append(crear_tecla("tecla-0", "0"));
  teclas.append(crear_tecla("tecla-borrar", "Borrar"));
  vista.append(teclas);

  const concepto = document.createElement("input");
  concepto.type = "text";
  concepto.setAttribute("data-prueba", "concepto");
  concepto.setAttribute("maxlength", "40");
  vista.append(concepto);

  const cobrar = document.createElement("button");
  cobrar.type = "button";
  cobrar.setAttribute("data-prueba", "cobrar");
  cobrar.textContent = "Cobrar";
  vista.append(cobrar);

  const libre = document.createElement("button");
  libre.type = "button";
  libre.setAttribute("data-prueba", "monto-libre");
  libre.textContent = "Monto libre";
  vista.append(libre);

  const mensaje = document.createElement("p");
  mensaje.setAttribute("data-prueba", "mensaje");
  vista.append(mensaje);
  return vista;
}

/**
 * @param {string} nombre
 * @param {string} texto
 * @returns {HTMLButtonElement}
 */
function crear_tecla(nombre, texto) {
  const boton = document.createElement("button");
  boton.type = "button";
  boton.setAttribute("data-prueba", nombre);
  boton.textContent = texto;
  return boton;
}

/**
 * @returns {HTMLElement}
 */
function crear_generando() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-generando");
  vista.hidden = true;

  const texto = document.createElement("p");
  texto.setAttribute("data-prueba", "generando");
  texto.textContent = TEXTO_GENERANDO;

  const indicador = document.createElement("span");
  indicador.className = "cargando";
  indicador.setAttribute("aria-hidden", "true");
  vista.append(texto, indicador);
  return vista;
}

/**
 * @returns {HTMLElement}
 */
function crear_qr() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-qr");
  vista.hidden = true;

  const imagen = document.createElement("img");
  imagen.setAttribute("data-prueba", "qr");
  imagen.alt = "QR";

  const monto = document.createElement("p");
  monto.setAttribute("data-prueba", "qr-monto");

  const concepto = document.createElement("p");
  concepto.setAttribute("data-prueba", "qr-concepto");

  const indicacion = document.createElement("p");
  indicacion.setAttribute("data-prueba", "indicacion-codi");
  indicacion.textContent = TEXTO_CODI;

  const cuenta = document.createElement("p");
  cuenta.setAttribute("data-prueba", "cuenta");

  const cancelar = document.createElement("button");
  cancelar.type = "button";
  cancelar.setAttribute("data-prueba", "cancelar");
  cancelar.textContent = "Cancelar cobro";
  cancelar.hidden = true;

  const mensaje = document.createElement("p");
  mensaje.setAttribute("data-prueba", "mensaje-cancelar");
  mensaje.hidden = true;

  vista.append(
    imagen,
    monto,
    concepto,
    indicacion,
    cuenta,
    cancelar,
    mensaje,
    crear_nuevo_cobro(),
  );
  return vista;
}

/**
 * @returns {HTMLElement}
 */
function crear_vencido() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-vencido");
  vista.hidden = true;

  const titulo = document.createElement("p");
  titulo.setAttribute("data-prueba", "vencido");
  titulo.textContent = "QR vencido";

  const monto = document.createElement("p");
  monto.setAttribute("data-prueba", "vencido-monto");

  const concepto = document.createElement("p");
  concepto.setAttribute("data-prueba", "vencido-concepto");

  const espera = document.createElement("p");
  espera.setAttribute("data-prueba", "vencido-espera");
  espera.textContent = TEXTO_ESPERA;

  vista.append(titulo, monto, concepto, espera, crear_nuevo_cobro());
  return vista;
}

/**
 * @returns {HTMLElement}
 */
function crear_error() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-error");
  vista.hidden = true;

  const texto = document.createElement("p");
  texto.setAttribute("data-prueba", "error");
  texto.textContent = TEXTO_ERROR;

  vista.append(texto, crear_nuevo_cobro());
  return vista;
}

/**
 * @returns {HTMLButtonElement}
 */
function crear_nuevo_cobro() {
  const boton = document.createElement("button");
  boton.type = "button";
  boton.setAttribute("data-prueba", "nuevo-cobro");
  boton.textContent = "Nuevo cobro";
  return boton;
}

/**
 * @returns {HTMLElement}
 */
function crear_pagado() {
  const vista = document.createElement("section");
  vista.setAttribute("data-prueba", "vista-pagado");
  vista.hidden = true;

  const titulo = document.createElement("p");
  titulo.setAttribute("data-prueba", "pagado");
  titulo.textContent = "Pago recibido";

  const monto = document.createElement("p");
  monto.setAttribute("data-prueba", "pagado-monto");

  const concepto = document.createElement("p");
  concepto.setAttribute("data-prueba", "pagado-concepto");

  const distinto = document.createElement("p");
  distinto.setAttribute("data-prueba", "pagado-distinto");
  distinto.hidden = true;

  const numero = document.createElement("p");
  numero.setAttribute("data-prueba", "pagado-numero");
  numero.hidden = true;

  const total = document.createElement("p");
  total.setAttribute("data-prueba", "pagado-total");
  total.hidden = true;

  const otra_vez = document.createElement("button");
  otra_vez.type = "button";
  otra_vez.setAttribute("data-prueba", "mostrar-qr");
  otra_vez.textContent = "Mostrar QR otra vez";
  otra_vez.hidden = true;

  vista.append(titulo, monto, concepto, distinto, numero, total, otra_vez, crear_nuevo_cobro());
  return vista;
}

/**
 * @param {number | string | null | undefined} valor
 * @returns {string}
 */
function pesos(valor) {
  const numero = Number(valor);
  if (!Number.isFinite(numero)) {
    return "";
  }
  return `$${numero.toFixed(2)}`;
}

/**
 * @param {number | null | undefined} valor
 * @returns {string}
 */
function texto_monto(valor) {
  return typeof valor === "number" && Number.isFinite(valor) ? pesos(valor) : "Monto libre";
}

/**
 * @param {string | null} nombre
 */
function mostrar_solo(nombre) {
  const raiz = document.getElementById("vistas");
  if (!raiz) {
    return;
  }
  for (const nodo of raiz.children) {
    if (!(nodo instanceof HTMLElement)) {
      continue;
    }
    const prueba = nodo.getAttribute("data-prueba") ?? "";
    if (!prueba.startsWith("vista-")) {
      continue;
    }
    nodo.hidden = prueba !== nombre;
  }
}

/** Muestra la espera antes de recuperar el cobro en pantalla (spec 002, RF-051, RF-052). */
export function mostrar_recuperando() {
  mostrar_solo(null);
  mostrar_reconectando(true);
}

/**
 * Pinta la vista Teclado solo con texto y atributos fijos
 * (spec 002, RF-001, RF-002, RF-005, RF-006, RF-060, RF-077).
 *
 * @param {{ monto?: string, concepto?: string, mensaje?: string }} estado
 * @returns {void}
 */
export function mostrar_teclado(estado) {
  asegurar();
  const monto = document.querySelector('[data-prueba="monto"]');
  const concepto = document.querySelector('[data-prueba="concepto"]');
  const cobrar = document.querySelector('[data-prueba="cobrar"]');
  const mensaje = document.querySelector('[data-prueba="mensaje"]');
  if (monto) {
    monto.textContent = `$${estado.monto ?? ""}`;
  }
  if (concepto instanceof HTMLInputElement) {
    concepto.value = estado.concepto ?? "";
  }
  if (cobrar instanceof HTMLButtonElement) {
    cobrar.disabled = !cobrar_activo(estado.monto ?? "");
  }
  const libre = document.querySelector('[data-prueba="monto-libre"]');
  if (libre instanceof HTMLButtonElement) {
    libre.disabled = !monto_libre_activo(estado.monto ?? "");
  }
  if (mensaje) {
    mensaje.textContent = estado.mensaje ?? "";
  }
  mostrar_solo("vista-teclado");
}

/**
 * Pinta Generando QR y oculta el resto (spec 002, RF-010, RF-077).
 *
 * @param {object} _estado
 * @returns {void}
 */
export function mostrar_generando(_estado) {
  asegurar();
  const generando = document.querySelector('[data-prueba="generando"]');
  if (generando) {
    generando.textContent = TEXTO_GENERANDO;
  }
  mostrar_solo("vista-generando");
}

/**
 * Pinta la vista QR. La imagen solo usa el prefijo data de un PNG
 * (spec 002, RF-015, RF-016, RF-017, RF-018, RF-077).
 *
 * @param {{
 *   qr_imagen?: string,
 *   monto?: number | null,
 *   concepto?: string,
 *   cuenta?: string,
 *   pendiente?: boolean,
 *   cancelando?: boolean,
 *   mensaje_cancelar?: string,
 * }} datos
 * @returns {void}
 */
export function mostrar_qr(datos) {
  asegurar();
  const imagen = document.querySelector('[data-prueba="qr"]');
  if (imagen instanceof HTMLImageElement) {
    const src = `data:image/png;base64,${datos.qr_imagen ?? ""}`;
    if (imagen.getAttribute("src") !== src) {
      imagen.setAttribute("src", src);
    }
  }
  const monto = document.querySelector('[data-prueba="qr-monto"]');
  if (monto) {
    monto.textContent = texto_monto(datos.monto);
  }
  const concepto = document.querySelector('[data-prueba="qr-concepto"]');
  if (concepto) {
    concepto.textContent = datos.concepto ?? "";
  }
  const indicacion = document.querySelector('[data-prueba="indicacion-codi"]');
  if (indicacion) {
    indicacion.textContent = TEXTO_CODI;
  }
  const cuenta = document.querySelector('[data-prueba="cuenta"]');
  if (cuenta) {
    cuenta.textContent = datos.cuenta ?? "";
  }
  const cancelar = document.querySelector('[data-prueba="cancelar"]');
  if (cancelar instanceof HTMLButtonElement) {
    cancelar.hidden = !datos.pendiente;
    cancelar.textContent = datos.cancelando ? "Cancelando…" : "Cancelar cobro";
  }
  const mensaje = document.querySelector('[data-prueba="mensaje-cancelar"]');
  if (mensaje) {
    const texto = datos.mensaje_cancelar ?? "";
    mensaje.textContent = texto;
    mensaje.hidden = texto === "";
  }
  mostrar_solo("vista-qr");
}

/**
 * Pinta Pago recibido solo con texto (spec 002, RF-023, RF-026, RF-028, RF-077).
 *
 * @param {{
 *   monto_recibido?: number,
 *   concepto?: string,
 *   monto_pedido?: number | null,
 *   monto_distinto?: boolean,
 *   numero?: number,
 *   total?: number,
 *   vigente?: boolean,
 * }} datos
 * @returns {void}
 */
export function mostrar_pagado(datos) {
  asegurar();
  const titulo = document.querySelector('[data-prueba="pagado"]');
  if (titulo) {
    titulo.textContent = "Pago recibido";
  }
  const monto = document.querySelector('[data-prueba="pagado-monto"]');
  if (monto) {
    monto.textContent = pesos(datos.monto_recibido);
  }
  const concepto = document.querySelector('[data-prueba="pagado-concepto"]');
  if (concepto) {
    concepto.textContent = datos.concepto ?? "";
  }
  const distinto = document.querySelector('[data-prueba="pagado-distinto"]');
  if (distinto) {
    if (datos.monto_distinto) {
      distinto.hidden = false;
      distinto.textContent = `Pediste ${pesos(datos.monto_pedido)}, recibiste ${pesos(datos.monto_recibido)}`;
    } else {
      distinto.hidden = true;
      distinto.textContent = "";
    }
  }
  const numero = document.querySelector('[data-prueba="pagado-numero"]');
  const total = document.querySelector('[data-prueba="pagado-total"]');
  const segundo = Number(datos.numero) >= 2;
  if (numero) {
    numero.hidden = !segundo;
    numero.textContent = segundo ? `Pago ${datos.numero}` : "";
  }
  if (total) {
    total.hidden = !segundo;
    total.textContent = segundo ? `Total recibido: ${pesos(datos.total)}` : "";
  }
  const otra_vez = document.querySelector('[data-prueba="mostrar-qr"]');
  if (otra_vez) {
    otra_vez.hidden = !datos.vigente;
  }
  mostrar_solo("vista-pagado");
}

/**
 * Muestra u oculta Mostrar QR otra vez sin volver a pintar el pago (spec 002, RF-069).
 *
 * @param {boolean} visible
 * @returns {void}
 */
export function fijar_mostrar_qr(visible) {
  const otra_vez = document.querySelector('[data-prueba="mostrar-qr"]');
  if (otra_vez) {
    otra_vez.hidden = !visible;
  }
}

/**
 * Pinta QR vencido, sin la imagen del QR (spec 002, RF-035, RF-036, RF-037, RF-038, RF-077).
 *
 * @param {{ monto?: number | null, concepto?: string }} cobro
 * @param {boolean} con_espera
 * @returns {void}
 */
export function mostrar_vencido(cobro, con_espera) {
  asegurar();
  const titulo = document.querySelector('[data-prueba="vencido"]');
  if (titulo) {
    titulo.textContent = "QR vencido";
  }
  const monto = document.querySelector('[data-prueba="vencido-monto"]');
  if (monto) {
    monto.textContent = texto_monto(cobro.monto);
  }
  const concepto = document.querySelector('[data-prueba="vencido-concepto"]');
  if (concepto) {
    concepto.textContent = cobro.concepto ?? "";
  }
  const espera = document.querySelector('[data-prueba="vencido-espera"]');
  if (espera) {
    espera.textContent = TEXTO_ESPERA;
    espera.hidden = !con_espera;
  }
  mostrar_solo("vista-vencido");
}

/**
 * Quita el aviso de que el pago todavía puede llegar (spec 002, RF-038, RF-040).
 *
 * @returns {void}
 */
export function ocultar_espera() {
  const espera = document.querySelector('[data-prueba="vencido-espera"]');
  if (espera) {
    espera.hidden = true;
  }
}

/**
 * Pinta la vista Error (spec 002, RF-057, RF-077).
 *
 * @returns {void}
 */
export function mostrar_error() {
  asegurar();
  const texto = document.querySelector('[data-prueba="error"]');
  if (texto) {
    texto.textContent = TEXTO_ERROR;
  }
  mostrar_solo("vista-error");
}

/**
 * Aviso de un pago de un cobro anterior, encima de la vista actual
 * (spec 002, RF-045, RF-077).
 *
 * @param {number | string | null | undefined} monto
 * @param {string} concepto
 * @returns {void}
 */
export function mostrar_aviso_anterior(monto, concepto) {
  const raiz = document.getElementById("vistas");
  if (!raiz) {
    return;
  }
  let caja = raiz.querySelector('[data-prueba="avisos-anteriores"]');
  if (!(caja instanceof HTMLElement)) {
    caja = document.createElement("div");
    caja.setAttribute("data-prueba", "avisos-anteriores");
    raiz.append(caja);
  }
  const aviso = document.createElement("button");
  aviso.type = "button";
  aviso.setAttribute("data-prueba", "aviso-anterior");
  aviso.textContent = `Pago de un cobro anterior: ${pesos(monto)} ${concepto}`.trim();
  aviso.addEventListener("click", () => {
    aviso.hidden = true;
  });
  caja.append(aviso);
}

/**
 * Pide un toque tras recuperar cobros o cuando el navegador rechaza el sonido (spec 002, RF-054).
 *
 * @param {boolean} visible
 * @returns {void}
 */
export function mostrar_activar_sonido(visible) {
  const raiz = document.getElementById("vistas");
  if (!raiz) {
    return;
  }
  let aviso = raiz.querySelector('[data-prueba="activar-sonido"]');
  if (!(aviso instanceof HTMLElement)) {
    aviso = document.createElement("p");
    aviso.setAttribute("data-prueba", "activar-sonido");
    raiz.append(aviso);
  }
  aviso.textContent = "Toca para activar el sonido";
  aviso.hidden = !visible;
}

/**
 * Aviso encima de la vista del cobro en pantalla (spec 002, RF-032).
 *
 * @param {boolean} visible
 * @returns {void}
 */
export function mostrar_reconectando(visible) {
  const raiz = document.getElementById("vistas");
  if (!raiz) {
    return;
  }
  let aviso = raiz.querySelector('[data-prueba="reconectando"]');
  if (!(aviso instanceof HTMLElement)) {
    aviso = document.createElement("p");
    aviso.setAttribute("data-prueba", "reconectando");
    raiz.append(aviso);
  }
  aviso.textContent = "Reconectando…";
  aviso.hidden = !visible;
}
