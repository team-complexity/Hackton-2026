import { Avisados } from "./avisados.js";
import { desfase } from "./cuenta.js";
import { guardar } from "./memoria.js";
import { mantener_encendida } from "./pantalla.js";
import { ver_cobro } from "./servidor.js";
import { vibrar } from "./sonido.js";

const CONSULTA_MS = 3_000;
const CONSULTA_CON_CANAL_MS = 8_000;
const REINTENTO_MS = 15_000;

/**
 * Un cobro en escucha: consulta cada 8 s con canal abierto o cada 3 s sin él
 * (spec 002, RF-020, RF-030, RF-031, RF-033, RF-034, RF-079, QP-1).
 */
export class Escucha {
  /**
   * @param {string} id
   * @param {object | null} cobro
   * @param {(aviso: { tipo: string, escucha: Escucha, cobro?: object }) => void} al_recibir
   */
  constructor(id, cobro, al_recibir) {
    this.id = id;
    this.cobro = cobro;
    this.desfase = cobro ? desfase(cobro, Date.now() / 1000) : 0;
    /** @type {"sin_canal" | "abriendo" | "abierto" | "cortado" | "cerrado"} */
    this.canal = "sin_canal";
    this.es_anterior = false;
    this._al_recibir = al_recibir;
    /** @type {EventSource | null} */
    this._fuente = null;
    /** @type {number} */
    this._consulta = 0;
    this._consulta_en_curso = false;
    /** @type {number} */
    this._reintento = 0;
    this._terminada = false;
  }

  /**
   * Abre el canal si esta escucha todavía no tiene uno (spec 002, QP-1).
   *
   * @returns {void}
   */
  tomar_canal() {
    if (this._terminada || this._fuente) {
      return;
    }
    this._abrir_canal();
  }

  /** Inicia la consulta de un cobro recordado antes de abrir su canal (spec 002, RF-051). */
  recuperar() {
    void this._consultar();
  }

  /**
   * Pasa a la consulta cada 3 s para dejar libre una conexión (spec 002, QP-1).
   *
   * @returns {void}
   */
  soltar_canal() {
    if (this._terminada) {
      return;
    }
    if (this._fuente || this.canal !== "sin_canal") {
      this._parar_reintento();
      if (this._fuente) {
        const fuente = this._fuente;
        // El error del cierre no es un corte de red: esta fuente ya no es la viva.
        this._fuente = null;
        fuente.close();
      }
      this.canal = "sin_canal";
      this._consultar_luego();
      return;
    }
    if (this._consulta === 0) {
      this._consultar_luego();
    }
  }

  /**
   * @returns {void}
   */
  _abrir_canal() {
    if (this._fuente) {
      const anterior = this._fuente;
      this._fuente = null;
      anterior.close();
    }
    this.canal = "abriendo";
    const url = `${window.PAGO_FACIL.servidor}/api/cobros/${this.id}/eventos`;
    const fuente = new EventSource(url);
    this._fuente = fuente;
    fuente.addEventListener("open", () => {
      if (this._fuente !== fuente || this._terminada) {
        return;
      }
      this.canal = "abierto";
      this._consultar_luego();
      this._parar_reintento();
      console.info(`escucha ${this.id}: abierto`);
      this._al_recibir({ tipo: "abierto", escucha: this });
    });
    fuente.addEventListener("estado", (evento) => {
      this._aplicar_evento(fuente, evento);
    });
    fuente.addEventListener("pago", (evento) => {
      if (this._fuente !== fuente || this._terminada) {
        return;
      }
      const datos = leer_json(evento);
      if (datos && typeof datos === "object" && datos.cobro) {
        this._aplicar(datos.cobro);
      }
    });
    fuente.addEventListener("vencido", (evento) => {
      this._aplicar_evento(fuente, evento, "vencido");
    });
    fuente.addEventListener("cancelado", (evento) => {
      this._aplicar_evento(fuente, evento, "cancelado");
    });
    fuente.addEventListener("fin", () => {
      if (this._fuente !== fuente || this._terminada) {
        return;
      }
      console.info(`escucha ${this.id}: fin`);
      this._al_recibir({ tipo: "fin", escucha: this });
      this.terminar();
    });
    fuente.addEventListener("error", () => {
      if (this._fuente !== fuente || this._terminada) {
        return;
      }
      this.canal = "cortado";
      console.info(`escucha ${this.id}: cortado`);
      this._al_recibir({ tipo: "cortado", escucha: this });
      this._consultar_luego();
      // Solo el cierre definitivo (HTTP distinto de 200) se reabre a los 15 s.
      // Un corte de red lo reintenta el propio navegador (R-5, RF-034).
      if (fuente.readyState === EventSource.CLOSED) {
        this._programar_reintento();
      }
    });
  }

  /**
   * @param {EventSource} fuente
   * @param {Event} evento
   * @param {string} [tipo]
   * @returns {void}
   */
  _aplicar_evento(fuente, evento, tipo) {
    if (this._fuente !== fuente || this._terminada) {
      return;
    }
    const datos = leer_json(evento);
    if (datos) {
      this._aplicar(datos, tipo);
    }
  }

  /**
   * @param {object} cobro
   * @param {string} [tipo]
   * @returns {void}
   */
  _aplicar(cobro, tipo = this.cobro ? "cobro" : "recuperado") {
    if (this._terminada) {
      return;
    }
    // Un evento retenido o una respuesta retrasada pueden traer un estado anterior.
    if (
      this.cobro &&
      (cobro.numero_de_pagos < this.cobro.numero_de_pagos ||
        (cobro.numero_de_pagos === this.cobro.numero_de_pagos &&
          cobro.hora_servidor < this.cobro.hora_servidor))
    ) {
      return;
    }
    this.cobro = cobro;
    this.desfase = desfase(cobro, Date.now() / 1000);
    this._al_recibir({ tipo, escucha: this, cobro });
  }

  /**
   * @returns {void}
   */
  _consultar_luego() {
    if (this._terminada || this._consulta_en_curso) {
      return;
    }
    this._parar_consulta();
    const espera = this.canal === "abierto" ? CONSULTA_CON_CANAL_MS : CONSULTA_MS;
    this._consulta = window.setTimeout(() => {
      void this._consultar();
    }, espera);
  }

  /**
   * @returns {Promise<void>}
   */
  async _consultar() {
    if (this._terminada || this._consulta_en_curso) {
      return;
    }
    this._parar_consulta();
    this._consulta_en_curso = true;
    console.info(`escucha ${this.id}: consulta`);
    const resultado = await ver_cobro(this.id);
    this._consulta_en_curso = false;
    if (this._terminada) {
      return;
    }
    if (resultado.cobro) {
      const cobro = resultado.cobro;
      if (
        cobro.hora_servidor != null &&
        cobro.fin_ventana != null &&
        cobro.hora_servidor >= cobro.fin_ventana
      ) {
        if (this.cobro) {
          this._aplicar(cobro);
        }
        console.info(`escucha ${this.id}: fin`);
        this._al_recibir({ tipo: "fin", escucha: this, cobro });
        this.terminar();
        return;
      }
      if (!this.cobro) {
        this._aplicar(cobro);
        return;
      }
      this._aplicar(cobro);
      if (this._fuente && this._fuente.readyState === EventSource.CLOSED) {
        this._programar_reintento();
      }
      this._consultar_luego();
      return;
    }
    if (resultado.no_existe) {
      this._al_recibir({ tipo: "no_existe", escucha: this });
      this.terminar();
      return;
    }
    if (resultado.sin_conexion) {
      this._consultar_luego();
    }
  }

  /**
   * @returns {void}
   */
  _programar_reintento() {
    if (this._reintento !== 0 || this._terminada || this.canal === "abierto") {
      return;
    }
    this._reintento = window.setTimeout(() => {
      this._reintento = 0;
      if (this._terminada || this.canal === "abierto") {
        return;
      }
      this._abrir_canal();
    }, REINTENTO_MS);
  }

  /**
   * @returns {void}
   */
  _parar_consulta() {
    window.clearTimeout(this._consulta);
    this._consulta = 0;
  }

  /**
   * @returns {void}
   */
  _parar_reintento() {
    window.clearTimeout(this._reintento);
    this._reintento = 0;
  }

  /**
   * Cierra el canal y detiene la consulta (spec 002, RF-040).
   *
   * @returns {void}
   */
  terminar() {
    if (this._terminada) {
      return;
    }
    this._terminada = true;
    this.canal = "cerrado";
    this._parar_consulta();
    this._parar_reintento();
    if (this._fuente) {
      const fuente = this._fuente;
      this._fuente = null;
      fuente.close();
    }
  }
}

/**
 * Las escuchas de esta pantalla. Como máximo 3 canales: el cobro en pantalla
 * y los dos anteriores más recientes (spec 002, RF-021, RF-043, RF-058, QP-1).
 */
export class Escuchas {
  /**
   * @param {{
   *   recuperado: (cobro: object, en_pantalla: boolean) => void,
   *   pagado: (pago: object, cobro: object) => void,
   *   anterior: (pago: object, cobro: object) => void,
   *   cancelado: (cobro: object) => void,
   *   reconectando: (visible: boolean) => void,
   *   vencido: (cobro: object) => void,
   *   error: () => void,
   *   fin: () => void,
   *   sonido: () => void,
   * }} vistas
   */
  constructor(vistas) {
    this._vistas = vistas;
    this._avisados = new Avisados();
    /** @type {Map<string, Escucha>} */
    this._por_id = new Map();
    /** @type {string[]} */
    this._anteriores = [];
    /** @type {string | null} */
    this._en_pantalla = null;
    this._pantalla_pedida = false;
    this._sin_sonido = false;
  }

  /**
   * Tras recargar, los pagos se muestran sin sonar hasta el primer toque
   * (spec 002, RF-054, RF-055).
   *
   * @param {boolean} sin_sonido
   * @returns {void}
   */
  fijar_sin_sonido(sin_sonido) {
    this._sin_sonido = sin_sonido;
  }

  /**
   * @param {{ id: string }} cobro
   * @returns {void}
   */
  poner_en_pantalla(cobro) {
    this._pedir_pantalla_encendida();
    this._agregar(cobro.id, cobro);
    this._en_pantalla = cobro.id;
    this._repartir();
    this._recordar();
  }

  /**
   * Registra todos los ids antes de consultarlos para conservar su orden y poder
   * guardar cambios aunque otras recuperaciones sigan pendientes (spec 002, RF-051).
   *
   * @param {{ en_pantalla: string | null, anteriores: string[] }} recordado
   * @returns {void}
   */
  recuperar(recordado) {
    this._en_pantalla = recordado.en_pantalla;
    this._anteriores = [...new Set(recordado.anteriores)].filter((id) => id !== this._en_pantalla);
    if (this._en_pantalla) {
      this._agregar(this._en_pantalla, null);
    }
    for (const id of this._anteriores) {
      this._agregar(id, null).es_anterior = true;
    }
    this._recordar();
    for (const escucha of this._por_id.values()) {
      escucha.recuperar();
    }
  }

  /**
   * @param {string} id
   * @param {object | null} cobro
   * @returns {Escucha}
   */
  _agregar(id, cobro) {
    const escucha = new Escucha(id, cobro, (aviso) => {
      this._recibir(aviso);
    });
    this._por_id.set(id, escucha);
    return escucha;
  }

  /**
   * Nuevo cobro y la cancelación confirmada dejan la escucha como anterior
   * (spec 002, RF-043, RF-049).
   *
   * @returns {void}
   */
  pasar_a_anterior() {
    const id = this._en_pantalla;
    if (!id) {
      return;
    }
    const escucha = this._por_id.get(id);
    this._en_pantalla = null;
    if (escucha) {
      escucha.es_anterior = true;
      this._anteriores.push(id);
    }
    this._vistas.reconectando(false);
    this._repartir();
    this._recordar();
  }

  /**
   * El cobro en pantalla y los dos anteriores más recientes usan canal
   * (spec 002, QP-1).
   *
   * @returns {void}
   */
  _repartir() {
    /** @type {Set<string>} */
    const deben = new Set();
    if (this._en_pantalla && this._por_id.get(this._en_pantalla)?.cobro) {
      deben.add(this._en_pantalla);
    }
    this._anteriores = this._anteriores.filter((id) => this._por_id.has(id));
    const recuperados = this._anteriores.filter((id) => this._por_id.get(id).cobro);
    for (const id of recuperados.slice(-2)) {
      deben.add(id);
    }
    for (const [id, escucha] of this._por_id) {
      if (escucha.cobro && !deben.has(id)) {
        escucha.soltar_canal();
      }
    }
    for (const id of deben) {
      this._por_id.get(id).tomar_canal();
    }
  }

  /**
   * @param {string} id
   * @param {string} tipo
   * @returns {void}
   */
  _cerrar(id, tipo) {
    const era_pantalla = id === this._en_pantalla;
    const escucha = this._por_id.get(id);
    this._por_id.delete(id);
    this._anteriores = this._anteriores.filter((otro) => otro !== id);
    if (era_pantalla) {
      this._en_pantalla = null;
    }
    if (escucha) {
      escucha.terminar();
    }
    if (era_pantalla) {
      this._vistas.reconectando(false);
      if (tipo === "no_existe") {
        this._vistas.error();
      } else {
        this._vistas.fin();
      }
    }
    this._repartir();
    this._recordar();
    this._soltar_si_vacia();
  }

  /**
   * @returns {void}
   */
  _recordar() {
    guardar(this._en_pantalla, this._anteriores.slice());
  }

  /** @returns {void} */
  _pedir_pantalla_encendida() {
    if (!this._pantalla_pedida) {
      this._pantalla_pedida = true;
      void mantener_encendida(true);
    }
  }

  /**
   * @returns {void}
   */
  _soltar_si_vacia() {
    if (this._por_id.size === 0) {
      this._pantalla_pedida = false;
      void mantener_encendida(false);
    }
  }

  /**
   * @param {{ tipo: string, escucha: Escucha, cobro?: object }} aviso
   * @returns {void}
   */
  _recibir(aviso) {
    const en_pantalla = aviso.escucha.id === this._en_pantalla;
    if (aviso.tipo === "cortado" && en_pantalla) {
      this._vistas.reconectando(true);
      return;
    }
    if (aviso.tipo === "abierto" && en_pantalla) {
      this._vistas.reconectando(false);
      return;
    }
    if (aviso.tipo === "vencido" && en_pantalla) {
      const cobro = aviso.cobro || aviso.escucha.cobro;
      const pagos = cobro && Array.isArray(cobro.pagos) ? cobro.pagos : [];
      if (pagos.length === 0 && cobro) {
        this._vistas.vencido(cobro);
      }
      return;
    }
    if (aviso.tipo === "cancelado" && en_pantalla) {
      this._vistas.cancelado(aviso.cobro || aviso.escucha.cobro);
      return;
    }
    if (aviso.tipo === "fin" || aviso.tipo === "no_existe") {
      this._cerrar(aviso.escucha.id, aviso.tipo);
      return;
    }
    if (aviso.tipo === "recuperado" && aviso.cobro) {
      this._pedir_pantalla_encendida();
      this._avisados.marcar_todos(aviso.cobro);
      this._vistas.recuperado(aviso.cobro, en_pantalla);
      if (!en_pantalla) {
        const pagos = Array.isArray(aviso.cobro.pagos) ? aviso.cobro.pagos : [];
        for (const pago of pagos) {
          this._vistas.anterior(pago, aviso.cobro);
        }
      }
      this._repartir();
      return;
    }
    if (aviso.tipo !== "cobro" || !aviso.cobro) {
      return;
    }
    if (en_pantalla && aviso.cobro.estado === "cancelado") {
      this._vistas.cancelado(aviso.cobro);
      return;
    }
    const nuevos = this._avisados.nuevos(aviso.cobro);
    for (const pago of nuevos) {
      if (!this._sin_sonido) {
        this._vistas.sonido();
        vibrar();
      }
      if (en_pantalla) {
        this._vistas.pagado(pago, aviso.cobro);
      } else {
        this._vistas.anterior(pago, aviso.cobro);
      }
    }
  }
}

/**
 * @param {Event} evento
 * @returns {object | null}
 */
function leer_json(evento) {
  if (!("data" in evento) || typeof evento.data !== "string") {
    return null;
  }
  try {
    const datos = JSON.parse(evento.data);
    if (!datos || typeof datos !== "object") {
      return null;
    }
    return datos;
  } catch {
    return null;
  }
}
