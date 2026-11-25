/**
 * Lleva, por cobro, el número de pago más alto ya mostrado (spec 002, RF-029, RF-053, RF-075).
 */
export class Avisados {
  constructor() {
    /** @type {Map<string, number>} */
    this._ultimo = new Map();
  }

  /**
   * Pagos con numero mayor al último avisado, en el orden del cobro, y sube esa marca
   * (spec 002, RF-029).
   *
   * @param {{ id: string, pagos?: { numero: number }[] }} cobro
   * @returns {{ numero: number }[]}
   */
  nuevos(cobro) {
    const ultimo = this._ultimo.get(cobro.id) ?? 0;
    const pagos = Array.isArray(cobro.pagos) ? cobro.pagos : [];
    const frescos = pagos.filter((pago) => pago.numero > ultimo);
    let maximo = ultimo;
    for (const pago of frescos) {
      if (pago.numero > maximo) {
        maximo = pago.numero;
      }
    }
    if (maximo > ultimo) {
      this._ultimo.set(cobro.id, maximo);
    }
    return frescos;
  }

  /**
   * Fija el último avisado en numero_de_pagos, sin devolver los pagos
   * (spec 002, RF-053, RF-075).
   *
   * @param {{ id: string, numero_de_pagos: number }} cobro
   * @returns {void}
   */
  marcar_todos(cobro) {
    this._ultimo.set(cobro.id, cobro.numero_de_pagos);
  }
}
