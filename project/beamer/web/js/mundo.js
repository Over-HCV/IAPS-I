/* mundo.js — la retícula del modelo, dibujada desde corridas reales.
 *
 * No simula nada: Reproduce los frames que `exportar.py` sacó de
 * `animacion.traza_corrida` (el modelo MESA corriendo de verdad). Formato compacto:
 * celdas como x·15 + y, recursos y creencias como pares planos [rid, celda, …].
 * Los colores son los de `project/animacion.py`, para que el deck, el cuaderno y la
 * tira del documento digan lo mismo con el mismo color.
 *
 * Lo usan el deck (index.html) y el simulador público (simulador.html).
 */
(function (global) {
  "use strict";

  const C = {
    agente: "#1f77b4", base: "#2ca02c", recurso: "#ff7f0e", creencia: "#8c8c8c",
    plan: "#7b5cd6", vision: "#2f80ed", mal: "#d62728", region: "#ff7f0e",
    obst: "#8f8c86", fondo: "#fbfaf7", rejilla: "#e6e2da", delib: "#DB6720",
  };

  const raiz = (() => {
    const s = document.currentScript && document.currentScript.src;
    return s ? s.replace(/js\/mundo\.js(\?.*)?$/, "") : "";
  })();

  const cache = new Map();
  function cargar(ruta) {
    if (!cache.has(ruta)) {
      cache.set(ruta, fetch(raiz + ruta).then((r) => {
        if (!r.ok) throw new Error(`${ruta}: ${r.status}`);
        return r.json();
      }));
    }
    return cache.get(ruta);
  }
  const indice = () => cargar("datos/corridas/indice.json");
  const nombre = (s, pol, lam, c, sinC) =>
    `${s}-${pol}-${+lam}-${sinC && sinC.includes(pol) ? 5 : c}`;
  const corrida = (s, pol, lam, c, sinC) =>
    cargar(`datos/corridas/${nombre(s, pol, lam, c, sinC)}.json`);

  function pares(arr) {
    const m = new Map();
    for (let i = 0; i < arr.length; i += 2) m.set(arr[i], arr[i + 1]);
    return m;
  }

  /* ------------------------------------------------------------------ vista */
  class Vista {
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {object} ret  retícula de `indice.semillas[s]` (lado, obst, base, radio)
     * @param {object} op   {colorAgente, ruta, vision, creencias, regiones, estela, oscuro}
     */
    constructor(canvas, ret, op = {}) {
      this.cv = canvas;
      this.ctx = canvas.getContext("2d");
      this.px = op.px || canvas.width;
      this.op = Object.assign(
        { ruta: true, vision: true, creencias: true, regiones: false, estela: 14,
          colorAgente: C.agente, escala: 2 },
        op,
      );
      this.setReticula(ret);
      this.co = null;
    }

    setReticula(ret) {
      this.ret = ret;
      this.lado = ret.lado;
      this.obst = new Set(ret.obst);
      this.cv.width = this.cv.height = Math.round(this.px * this.op.escala);
      this.k = this.cv.width / this.lado;
    }

    setCorrida(co) { this.co = co; }

    // centro de la celda en píxeles del canvas (y hacia arriba, como en matplotlib)
    xy(celda) {
      const x = Math.floor(celda / this.lado), y = celda % this.lado;
      return [(x + 0.5) * this.k, (this.lado - y - 0.5) * this.k];
    }
    mezcla(a, b, f) {
      if (a === b || b === undefined) return this.xy(a);
      const p = this.xy(a), q = this.xy(b);
      return [p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f];
    }

    dibujar(t) {
      const { ctx, k, lado, co, op } = this;
      const W = this.cv.width;
      ctx.clearRect(0, 0, W, W);
      ctx.fillStyle = C.fondo;
      ctx.fillRect(0, 0, W, W);
      if (!co) return;
      const n = co.ag.length - 1;
      t = Math.max(0, Math.min(n, t));
      const i = Math.floor(t), j = Math.min(n, i + 1);
      const f = easeInOut(t - i);

      // rejilla
      ctx.strokeStyle = C.rejilla;
      ctx.lineWidth = Math.max(1, k * 0.03);
      ctx.beginPath();
      for (let g = 0; g <= lado; g++) {
        ctx.moveTo(g * k, 0); ctx.lineTo(g * k, W);
        ctx.moveTo(0, g * k); ctx.lineTo(W, g * k);
      }
      ctx.stroke();

      // región posible (KNOWLEDGE_BASED)
      if (op.regiones && co.reg) {
        ctx.fillStyle = hexA(C.region, 0.24);
        const vistas = new Set();
        for (const celdas of Object.values(co.reg[i] || {})) {
          for (const c of celdas) {
            if (vistas.has(c)) continue;
            vistas.add(c);
            const [cx, cy] = this.xy(c);
            ctx.fillRect(cx - k / 2, cy - k / 2, k, k);
          }
        }
      }

      // visión: rombo de Manhattan ≤ r alrededor del agente (Von Neumann de MESA)
      const ag = co.ag[i];
      if (op.vision && this.ret.radio != null) {
        const r = this.ret.radio;
        const ax = Math.floor(ag / lado), ay = ag % lado;
        ctx.fillStyle = hexA(C.vision, 0.11);
        for (let dx = -r; dx <= r; dx++) {
          for (let dy = -r + Math.abs(dx); dy <= r - Math.abs(dx); dy++) {
            const x = ax + dx, y = ay + dy;
            if (x < 0 || y < 0 || x >= lado || y >= lado) continue;
            const [cx, cy] = this.xy(x * lado + y);
            ctx.fillRect(cx - k / 2, cy - k / 2, k, k);
          }
        }
      }

      // obstáculos
      ctx.fillStyle = hexA(C.obst, 0.5);
      for (const c of this.obst) {
        const [cx, cy] = this.xy(c);
        ctx.fillRect(cx - k * 0.42, cy - k * 0.42, k * 0.84, k * 0.84);
      }

      // base
      const [bx, by] = this.xy(this.ret.base);
      ctx.fillStyle = C.base;
      ctx.fillRect(bx - k * 0.42, by - k * 0.42, k * 0.84, k * 0.84);

      // estela del agente
      if (op.estela) {
        ctx.strokeStyle = hexA(op.colorAgente, 0.28);
        ctx.lineWidth = k * 0.09;
        ctx.lineJoin = ctx.lineCap = "round";
        ctx.beginPath();
        const desde = Math.max(0, i - op.estela);
        for (let s = desde; s <= i; s++) {
          const [px, py] = this.xy(co.ag[s]);
          s === desde ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        const [qx, qy] = this.mezcla(co.ag[i], co.ag[j], f);
        ctx.lineTo(qx, qy);
        ctx.stroke();
      }

      const posAg = this.mezcla(co.ag[i], co.ag[j], f);

      // plan vivo: agente → ruta que queda
      if (op.ruta && co.ruta[i].length) {
        ctx.strokeStyle = hexA(C.plan, 0.9);
        ctx.lineWidth = k * 0.1;
        ctx.setLineDash([k * 0.12, k * 0.2]);
        ctx.beginPath();
        ctx.moveTo(posAg[0], posAg[1]);
        for (const c of co.ruta[i]) {
          const [px, py] = this.xy(c);
          ctx.lineTo(px, py);
        }
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // recursos reales (interpolados si el mismo rid sigue en el tick siguiente)
      const rec = pares(co.rec[i]), recSig = pares(co.rec[j]);
      ctx.fillStyle = C.recurso;
      for (const [rid, c] of rec) {
        const [px, py] = this.mezcla(c, recSig.get(rid), f);
        disco(ctx, px, py, k * 0.27);
      }

      // creencias obsoletas: rombo hueco donde el agente cree que está y ya no está
      const cre = pares(co.cre[i]);
      if (op.creencias) {
        ctx.strokeStyle = C.creencia;
        ctx.lineWidth = k * 0.07;
        for (const [rid, c] of cre) {
          if (rec.get(rid) === c) continue;
          const [px, py] = this.xy(c);
          rombo(ctx, px, py, k * 0.3);
        }
      }

      // objetivo: anillo sobre la creencia y flecha creencia → realidad (la divergencia)
      const obj = co.obj[i];
      if (obj >= 0 && cre.has(obj)) {
        const [cx, cy] = this.xy(cre.get(obj));
        ctx.strokeStyle = C.plan;
        ctx.lineWidth = k * 0.08;
        ctx.beginPath(); ctx.arc(cx, cy, k * 0.45, 0, 2 * Math.PI); ctx.stroke();
        if (rec.has(obj) && rec.get(obj) !== cre.get(obj)) {
          const [rx, ry] = this.xy(rec.get(obj));
          flecha(ctx, cx, cy, rx, ry, k, C.mal);
        }
      }

      // agente
      ctx.fillStyle = op.colorAgente;
      disco(ctx, posAg[0], posAg[1], k * 0.36);
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = k * 0.06;
      ctx.beginPath(); ctx.arc(posAg[0], posAg[1], k * 0.36, 0, 2 * Math.PI); ctx.stroke();

      // deliberando: arco de progreso ámbar alrededor del agente
      const d = co.d[i];
      if (d) {
        const [el, dur] = d;
        const p = dur ? Math.min(1, (el + f) / dur) : 1;
        ctx.strokeStyle = C.delib;
        ctx.lineWidth = k * 0.13;
        ctx.beginPath();
        ctx.arc(posAg[0], posAg[1], k * 0.62, -Math.PI / 2, -Math.PI / 2 + p * 2 * Math.PI);
        ctx.stroke();
      }

      // carga a bordo
      if (co.car[i]) {
        ctx.fillStyle = op.colorAgente;
        ctx.font = `700 ${Math.round(k * 0.55)}px Heros, Helvetica, sans-serif`;
        ctx.textAlign = "left";
        ctx.textBaseline = "alphabetic";
        ctx.fillText(`×${co.car[i]}`, posAg[0] + k * 0.42, posAg[1] - k * 0.38);
      }

      // edición aplicada: destello del plan
      if (co.e[i] === 1 && op.ruta) {
        ctx.strokeStyle = hexA(C.plan, 0.55 * (1 - f));
        ctx.lineWidth = k * 0.2;
        ctx.beginPath(); ctx.arc(posAg[0], posAg[1], k * (0.7 + f * 0.8), 0, 2 * Math.PI); ctx.stroke();
      }
    }
  }

  /* ------------------------------------------------------------- reproductor */
  class Reproductor {
    /** @param {(t:number)=>void} pintar  @param {object} op {tps, fin, bucle, alTick, alTerminar} */
    constructor(pintar, op = {}) {
      this.pintar = pintar;
      this.op = Object.assign({ tps: 8, fin: 400, bucle: false, desde: 0 }, op);
      this.t = this.op.desde;
      this.vivo = false;
      this._ult = null;
      this._raf = null;
      this._tickPrevio = -1;
    }
    play() {
      if (this.vivo) return;
      if (this.t >= this.op.fin) this.t = this.op.desde;
      this.vivo = true;
      this._ult = null;
      const paso = (ahora) => {
        if (!this.vivo) return;
        if (this._ult != null) this.t += ((ahora - this._ult) / 1000) * this.op.tps;
        this._ult = ahora;
        if (this.t >= this.op.fin) {
          if (this.op.bucle) this.t = this.op.desde;
          else { this.t = this.op.fin; this.vivo = false; }
        }
        this._emitir();
        if (this.vivo) this._raf = requestAnimationFrame(paso);
        else if (this.op.alTerminar) this.op.alTerminar();
      };
      this._raf = requestAnimationFrame(paso);
    }
    pause() { this.vivo = false; if (this._raf) cancelAnimationFrame(this._raf); }
    ir(t) { this.t = Math.max(0, Math.min(this.op.fin, t)); this._emitir(); }
    _emitir() {
      this.pintar(this.t);
      const tk = Math.floor(this.t);
      if (tk !== this._tickPrevio && this.op.alTick) this.op.alTick(tk);
      this._tickPrevio = tk;
    }
  }

  /* ------------------------------------------------------------------ dibujo */
  function disco(ctx, x, y, r) { ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI); ctx.fill(); }
  function rombo(ctx, x, y, r) {
    ctx.beginPath();
    ctx.moveTo(x, y - r); ctx.lineTo(x + r, y); ctx.lineTo(x, y + r); ctx.lineTo(x - r, y);
    ctx.closePath(); ctx.stroke();
  }
  function flecha(ctx, x0, y0, x1, y1, k, color) {
    const a = Math.atan2(y1 - y0, x1 - x0), L = Math.hypot(x1 - x0, y1 - y0);
    const xe = x0 + Math.cos(a) * (L - k * 0.3), ye = y0 + Math.sin(a) * (L - k * 0.3);
    ctx.strokeStyle = ctx.fillStyle = color;
    ctx.lineWidth = k * 0.09;
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(xe, ye); ctx.stroke();
    const h = k * 0.3;
    ctx.beginPath();
    ctx.moveTo(xe + Math.cos(a) * h * 0.6, ye + Math.sin(a) * h * 0.6);
    ctx.lineTo(xe - Math.cos(a - 0.5) * h, ye - Math.sin(a - 0.5) * h);
    ctx.lineTo(xe - Math.cos(a + 0.5) * h, ye - Math.sin(a + 0.5) * h);
    ctx.closePath(); ctx.fill();
  }
  function hexA(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }
  function easeInOut(x) { return x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2; }

  global.Mundo = { Vista, Reproductor, indice, corrida, cargar, nombre, colores: C, hexA };
})(window);
