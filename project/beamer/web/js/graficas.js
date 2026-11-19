/* graficas.js — las figuras del deck, dibujadas en vivo con D3 desde datos/*.json.
 *
 * Cada figura es una función (ctx) => void registrada con un nombre; el deck la llama
 * al entrar en la diapositiva (`data-anim="nombre"`) y la detiene al salir. Los datos
 * son los mismos que dibujan los PNG del PDF (`exportar.py` reusa las agregaciones de
 * `figuras.py`), y la paleta, los marcadores y los rangos de los ejes son los mismos.
 */
(function (global) {
  "use strict";

  const COLOR = {
    REFLEX: "#0173b2", MODEL_BASED: "#de8f05", OPEN_LOOP: "#029e73", COLD_RESTART: "#d55e00",
    CLOSED_LOOP: "#cc78bc", GOVERNED: "#ca9161", KNOWLEDGE_BASED: "#56b4e9", BAYESIAN: "#6a51c9",
  };
  const CORTO = {
    REFLEX: "RX", MODEL_BASED: "MB", OPEN_LOOP: "OL", COLD_RESTART: "CR", CLOSED_LOOP: "CL",
    GOVERNED: "GOV", KNOWLEDGE_BASED: "KB", BAYESIAN: "BAY",
  };
  const PRIMARIO = "#002d4d", TINTA = "#1A1A1A", TINTA2 = "#55565a", FONDO = "#F8F6F2";
  const ALERTA = "#E8637D";
  const RAMPA_C = ["#a9cfe0", "#5d9cc4", "#2a6b9b", PRIMARIO];

  const SIMBOLO = {
    REFLEX: [d3.symbolTriangle, 180], MODEL_BASED: [d3.symbolCircle, 0],
    OPEN_LOOP: [d3.symbolTriangle, 0], COLD_RESTART: [d3.symbolCross, 45],
    CLOSED_LOOP: [d3.symbolSquare, 0], GOVERNED: [d3.symbolCross, 0],
    KNOWLEDGE_BASED: [d3.symbolDiamond, 0], BAYESIAN: [d3.symbolWye, 0],
  };

  // El deck anima siempre (lo pide la charla); ?quieto=1 lo deja estático.
  const quieto = new URLSearchParams(location.search).has("quieto");
  const raiz = (() => {
    const s = document.currentScript && document.currentScript.src;
    return s ? s.replace(/js\/graficas\.js(\?.*)?$/, "") : "";
  })();
  const cache = new Map();
  const datos = (n) => {
    if (!cache.has(n)) cache.set(n, fetch(`${raiz}datos/${n}.json`).then((r) => r.json()));
    return cache.get(n);
  };

  const fmt = (v, d = 1) => (v == null ? "—" : v.toFixed(d).replace("-", "−"));
  const fmtSigno = (v, d = 1) => (v > 0 ? "+" : "") + fmt(v, d);

  /* --------------------------------------------------------------- contexto */
  function contexto(el) {
    const timers = [];
    return {
      el,
      T: (ms) => (quieto ? 0 : ms),
      despues(ms, fn) { timers.push(setTimeout(fn, quieto ? 0 : ms)); },
      detener() {
        timers.forEach(clearTimeout);
        d3.select(el).selectAll("*").interrupt();
        (el._paradas || []).forEach((f) => f());
        el._paradas = [];
      },
      alDetener(fn) { (el._paradas = el._paradas || []).push(fn); },
    };
  }

  function lienzo(el, w, h) {
    const svg = d3.select(el).append("svg").attr("width", w).attr("height", h)
      .attr("viewBox", `0 0 ${w} ${h}`);
    return svg;
  }

  function panel(svg, x0, y0, iw, ih) {
    return svg.append("g").attr("transform", `translate(${x0},${y0})`).datum({ iw, ih });
  }

  function ejes(g, x, y, iw, ih, op = {}) {
    if (op.rejillaY !== false) {
      g.append("g").attr("class", "rejilla")
        .call(d3.axisLeft(y).ticks(op.ticksY || 5).tickSize(-iw).tickFormat(""));
    }
    if (op.rejillaX) {
      g.append("g").attr("class", "rejilla").attr("transform", `translate(0,${ih})`)
        .call(d3.axisBottom(x).tickValues(op.ticksX).tickSize(-ih).tickFormat(""));
    }
    const ax = d3.axisBottom(x).tickSizeOuter(0).tickSize(5);
    if (op.ticksX) ax.tickValues(op.ticksX);
    if (op.fmtX) ax.tickFormat(op.fmtX);
    g.append("g").attr("class", "eje").attr("transform", `translate(0,${ih})`).call(ax);
    if (op.ejeY !== false) {
      const ay = d3.axisLeft(y).ticks(op.ticksY || 5).tickSizeOuter(0).tickSize(5);
      if (op.fmtY) ay.tickFormat(op.fmtY);
      g.append("g").attr("class", "eje").call(ay);
    }
    if (op.rotX) {
      g.append("text").attr("class", "rot").attr("x", iw / 2).attr("y", ih + 46)
        .attr("text-anchor", "middle").text(op.rotX);
    }
    if (op.rotY) {
      g.append("text").attr("class", "rot").attr("transform", "rotate(-90)")
        .attr("x", -ih / 2).attr("y", -(op.sepY || 52)).attr("text-anchor", "middle").text(op.rotY);
    }
    if (op.titulo) {
      g.append("text").attr("class", "tit").attr("x", 0).attr("y", -14).text(op.titulo);
    }
  }

  function leyenda(el, items) {
    const div = d3.select(el).append("div").attr("class", "leyenda");
    for (const it of items) {
      const s = div.append("span");
      s.append("i").style("background", it.color).style("height", it.grueso ? "4px" : "3px");
      s.append("tt").text(it.texto);
    }
    return div;
  }
  const leyendaPols = (el, pols) => leyenda(el, pols.map((p) => ({ color: COLOR[p], texto: p })));

  // traza un <path> de principio a fin
  function trazar(sel, dur, delay = 0, facil = d3.easeCubicInOut) {
    sel.each(function () {
      const L = this.getTotalLength();
      d3.select(this).attr("stroke-dasharray", `${L} ${L}`).attr("stroke-dashoffset", L)
        .transition().delay(delay).duration(dur).ease(facil).attr("stroke-dashoffset", 0)
        .on("end", function () { d3.select(this).attr("stroke-dasharray", null); });
    });
    return sel;
  }

  function contar(sel, valor, dec, dur, delay, prefijo = "", conSigno = false) {
    sel.text(prefijo + (conSigno ? fmtSigno(0, dec) : fmt(0, dec)))
      .transition().delay(delay).duration(dur).ease(d3.easeCubicOut)
      .tween("text", function () {
        const i = d3.interpolateNumber(0, valor);
        return (t) => { this.textContent = prefijo + (conSigno ? fmtSigno(i(t), dec) : fmt(i(t), dec)); };
      });
  }

  function simbolo(g, pol, x, y, tam = 70) {
    const [tipo, rot] = SIMBOLO[pol] || [d3.symbolCircle, 0];
    return g.append("path").attr("d", d3.symbol(tipo, tam)())
      .attr("transform", `translate(${x},${y}) rotate(${rot}) scale(0)`)
      .attr("fill", COLOR[pol]).datum({ x, y, rot });
  }
  function aparecer(sel, delay, dur = 260) {
    sel.transition().delay(delay).duration(dur).ease(d3.easeBackOut.overshoot(2))
      .attr("transform", (d) => `translate(${d.x},${d.y}) rotate(${d.rot || 0}) scale(1)`);
  }

  /* ------------------------------------------------------------- lineas(λ) */
  // Utilidad contra λ, con banda ±EE, una curva por política que se traza de izquierda a
  // derecha. La usan «La frontera» (dos paneles) y «El agente lógico» (uno).
  function curvasLambda(ctx, g, x, y, series, op) {
    const xs = x.domain();
    const linea = d3.line().x((d) => x(d.x)).y((d) => y(d.m));
    const area = d3.area().x((d) => x(d.x)).y0((d) => y(d.m - d.e)).y1((d) => y(d.m + d.e));
    const fin = {};
    op.orden.forEach((pol, k) => {
      const s = series[pol];
      const grueso = pol === op.destacada;
      const delay = op.delay + k * op.paso;
      const dur = op.dur;
      g.append("path").datum(s).attr("d", area).attr("fill", COLOR[pol]).attr("opacity", 0)
        .transition().delay(delay + dur * 0.7).duration(ctx.T(600)).attr("opacity", 0.14);
      trazar(g.append("path").datum(s).attr("d", linea).attr("fill", "none")
        .attr("stroke", COLOR[pol]).attr("stroke-width", grueso ? 4.6 : 2.4)
        .attr("stroke-linejoin", "round"), dur, delay);
      s.forEach((d) => {
        const f = (d.x - xs[0]) / (xs[1] - xs[0]);
        aparecer(simbolo(g, pol, x(d.x), y(d.m), grueso ? 95 : 62), delay + dur * Math.max(0, f) * 0.95);
      });
      fin[pol] = delay + dur;
    });
    return fin;
  }

  /* ================================================================ figuras */
  const F = {};

  F.frontera = async (ctx) => {
    const f = await datos("frontera");
    const pols = ["REFLEX", "MODEL_BASED", "OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP"];
    leyendaPols(ctx.el, pols);
    const W = 1150, H = 400, m = { l: 74, r: 18, t: 34, b: 62 }, gap = 40;
    const iw = (W - m.l - m.r - gap) / 2, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    const x = d3.scaleLinear([-0.015, 0.53], [0, iw]);
    const y = d3.scaleLinear([0, 118], [ih, 0]);
    // orden de trazado: las que planifican primero, MODEL_BASED al final y más gruesa
    const orden = ["OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP", "REFLEX", "MODEL_BASED"];
    ["2", "5"].forEach((c, p) => {
      const g = panel(svg, m.l + p * (iw + gap), m.t, iw, ih);
      ejes(g, x, y, iw, ih, {
        ticksX: [0, 0.1, 0.25, 0.5], fmtX: d3.format("~g"), ejeY: p === 0,
        rotX: "λ (probabilidad de deriva por tick)",
        rotY: p === 0 ? "utilidad neta (10 × entregas)" : null,
        titulo: `c = ${c} ticks por reparación`,
      });
      const base = ctx.T(250 + p * 1700);
      const fin = curvasLambda(ctx, g, x, y, f[c], {
        orden, destacada: "MODEL_BASED", delay: base, paso: ctx.T(260), dur: ctx.T(1100),
      });
      const en = (pol) => f[c][pol].find((d) => d.x === 0.5).m;
      const mb = en("MODEL_BASED");
      const plan = Math.max(en("OPEN_LOOP"), en("COLD_RESTART"), en("CLOSED_LOOP"));
      const t = fin.MODEL_BASED + ctx.T(150);
      contar(g.append("text").attr("class", "fuerte").attr("x", x(0.5)).attr("y", y(mb) - 14)
        .attr("text-anchor", "middle").style("font-size", "19px"), mb, 1, ctx.T(700), t);
      contar(g.append("text").attr("class", "anota").attr("x", x(0.5)).attr("y", y(plan) - 12)
        .attr("text-anchor", "middle").style("font-size", "18px"), plan, 1, ctx.T(700), t);
    });
  };

  F["abierto-cerrado"] = async (ctx) => {
    const d = await datos("abierto-cerrado");
    const W = 560, H = 480, m = { l: 82, r: 12, t: 54, b: 58 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    const lams = [...new Set(d.map((r) => r.lam))].sort((a, b) => a - b);
    const cs = [...new Set(d.map((r) => r.c))].sort((a, b) => a - b);
    const x = d3.scaleLinear([-0.5, lams.length - 0.5], [0, iw]);
    const y = d3.scaleLinear([-25, 48], [ih, 0]);
    const g = panel(svg, m.l, m.t, iw, ih);
    ejes(g, x, y, iw, ih, {
      ticksX: lams.map((_, i) => i), fmtX: (i) => d3.format("~g")(lams[i]), rejillaY: false,
      rotX: "λ", rotY: "OPEN_LOOP − CLOSED_LOOP  (± 2 EE)", sepY: 50,
    });
    g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(0)).attr("y2", y(0))
      .attr("stroke", TINTA2).attr("stroke-width", 1.2);
    g.append("text").attr("class", "anota").attr("x", 8).attr("y", 18).text("a favor del lazo abierto");
    g.append("text").attr("class", "anota").attr("x", 8).attr("y", ih - 8).text("a favor del lazo cerrado");
    // leyenda arriba
    const ley = svg.append("g").attr("transform", `translate(${m.l},18)`);
    cs.forEach((c, j) => {
      ley.append("circle").attr("cx", j * 78 + 6).attr("cy", 0).attr("r", 6).attr("fill", RAMPA_C[j]);
      ley.append("text").attr("class", "anota").attr("x", j * 78 + 16).attr("y", 5).text(`c = ${c}`);
    });
    ley.append("circle").attr("cx", 4 * 78 + 6).attr("cy", 0).attr("r", 5.5).attr("fill", FONDO)
      .attr("stroke", TINTA2).attr("stroke-width", 1.8);
    ley.append("text").attr("class", "anota").attr("x", 4 * 78 + 16).attr("y", 5).text("hueco: cruza el 0");
    const ancho = 0.17;
    const filas = [];
    lams.forEach((lam, i) => cs.forEach((c, j) => {
      const r = d.find((q) => q.lam === lam && q.c === c);
      if (r) filas.push({ ...r, xi: i + (j - 1.5) * ancho, j });
    }));
    filas.forEach((r, k) => {
      const t = ctx.T(300 + k * 120);
      const cx = x(r.xi), fuera = Math.abs(r.m) > 2 * r.e;
      g.append("line").attr("x1", cx).attr("x2", cx).attr("y1", y(r.m)).attr("y2", y(r.m))
        .attr("stroke", RAMPA_C[r.j]).attr("stroke-width", 2.2)
        .transition().delay(t).duration(ctx.T(420))
        .attr("y1", y(r.m - 2 * r.e)).attr("y2", y(r.m + 2 * r.e));
      g.append("circle").attr("cx", cx).attr("cy", y(r.m)).attr("r", 0)
        .attr("fill", RAMPA_C[r.j]).attr("stroke", RAMPA_C[r.j]).attr("stroke-width", 2.4)
        .transition().delay(t).duration(ctx.T(280)).attr("r", 6.5)
        // los que cruzan el cero se vacían después: «dentro del ruido» llega como segundo golpe
        .transition().delay(ctx.T(filas.length * 120 + 500 - k * 120)).duration(ctx.T(400))
        .attr("fill", fuera ? RAMPA_C[r.j] : FONDO);
    });
  };

  F["caliente-frio"] = async (ctx) => {
    const d = await datos("caliente-frio");
    const W = 560, H = 480, m = { l: 82, r: 12, t: 54, b: 58 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    const lams = [...new Set(d.map((r) => r.lam))].sort((a, b) => a - b);
    const cs = [...new Set(d.map((r) => r.c))].sort((a, b) => a - b);
    const x = d3.scaleLinear([-0.5, lams.length - 0.5], [0, iw]);
    const y = d3.scaleLinear([-6, 40], [ih, 0]);
    const g = panel(svg, m.l, m.t, iw, ih);
    ejes(g, x, y, iw, ih, {
      ticksX: lams.map((_, i) => i), fmtX: (i) => d3.format("~g")(lams[i]),
      rotX: "λ", rotY: "CLOSED_LOOP − COLD_RESTART  (± EE)", sepY: 50,
    });
    const ley = svg.append("g").attr("transform", `translate(${m.l},18)`);
    cs.forEach((c, j) => {
      ley.append("rect").attr("x", j * 92).attr("y", -8).attr("width", 16).attr("height", 16).attr("fill", RAMPA_C[j]);
      ley.append("text").attr("class", "anota").attr("x", j * 92 + 22).attr("y", 5).text(`c = ${c}`);
    });
    const ancho = 0.19, bw = x(ancho * 0.88) - x(0);
    lams.forEach((lam, i) => cs.forEach((c, j) => {
      const r = d.find((q) => q.lam === lam && q.c === c);
      if (!r) return;
      const cx = x(i + (j - 1.5) * ancho), t = ctx.T(250 + i * 420 + j * 90);
      g.append("rect").attr("x", cx - bw / 2).attr("width", bw).attr("y", y(0)).attr("height", 0)
        .attr("fill", RAMPA_C[j])
        .transition().delay(t).duration(ctx.T(650)).ease(d3.easeCubicOut)
        .attr("y", y(Math.max(0, r.m))).attr("height", Math.abs(y(r.m) - y(0)));
      g.append("line").attr("x1", cx).attr("x2", cx).attr("y1", y(r.m)).attr("y2", y(r.m))
        .attr("stroke", TINTA2).attr("stroke-width", 1.4).attr("opacity", 0)
        .transition().delay(t + ctx.T(600)).duration(ctx.T(300)).attr("opacity", 1)
        .attr("y1", y(r.m - r.e)).attr("y2", y(r.m + r.e));
    }));
    g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(0)).attr("y2", y(0))
      .attr("stroke", TINTA2).attr("stroke-width", 1.2);
    const nota = g.append("text").attr("class", "anota").attr("x", x(3 + ancho)).attr("y", y(3) - 50)
      .attr("text-anchor", "middle").style("font-size", "15px").attr("opacity", 0);
    ["c ≥ 5:", "ambas", "colapsan"].forEach((t, k) => nota.append("tspan").attr("x", x(3 + ancho)).attr("dy", k ? 17 : 0).text(t));
    nota.transition().delay(ctx.T(2300)).duration(ctx.T(500)).attr("opacity", 1);
  };

  F.dinamica = async (ctx) => {
    const d = await datos("dinamica");
    const pols = ["REFLEX", "MODEL_BASED", "OPEN_LOOP", "COLD_RESTART", "CLOSED_LOOP"];
    leyendaPols(ctx.el, pols);
    const W = 1150, H = 400, m = { l: 70, r: 18, t: 34, b: 62 }, gap = 40;
    const iw = (W - m.l - m.r - gap) / 2, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    const x = d3.scaleLinear([0, 410], [0, iw]);
    const y = d3.scaleLinear([0, 10.2], [ih, 0]);
    const marcas = { "0.1": [130, ["CLOSED_LOOP > COLD_RESTART", "desde el tick 130"]],
                     "0.5": [15, ["MODEL_BASED > CLOSED_LOOP", "desde el tick 15"]] };
    const DUR = ctx.T(7000), INICIO = ctx.T(400);
    const id = "clip" + Math.random().toString(36).slice(2);
    ["0.1", "0.5"].forEach((lam, p) => {
      const g = panel(svg, m.l + p * (iw + gap), m.t, iw, ih);
      ejes(g, x, y, iw, ih, {
        ticksX: [0, 100, 200, 300, 400], ejeY: p === 0, rotX: "tick",
        rotY: p === 0 ? "entregas acumuladas" : null, titulo: `λ = ${lam}`,
      });
      const clip = g.append("clipPath").attr("id", id + p).append("rect")
        .attr("x", -4).attr("y", -20).attr("height", ih + 24).attr("width", 0);
      const capa = g.append("g").attr("clip-path", `url(#${id + p})`);
      for (const pol of pols) {
        const s = d[lam][pol];
        capa.append("path").datum(s).attr("fill", COLOR[pol]).attr("opacity", 0.14)
          .attr("d", d3.area().x((q) => x(q[0])).y0((q) => y(q[1] - q[2])).y1((q) => y(q[1] + q[2])));
        capa.append("path").datum(s).attr("fill", "none").attr("stroke", COLOR[pol])
          .attr("stroke-width", pol === "MODEL_BASED" ? 4.2 : 2.4).attr("stroke-linejoin", "round")
          .attr("d", d3.line().x((q) => x(q[0])).y((q) => y(q[1])));
      }
      clip.transition().delay(INICIO).duration(DUR).ease(d3.easeLinear).attr("width", x(400) + 8);
      // cursor que recorre los ticks
      const cur = g.append("g").attr("opacity", quieto ? 0 : 1);
      cur.append("line").attr("y1", 0).attr("y2", ih).attr("stroke", TINTA2).attr("stroke-width", 1)
        .attr("stroke-dasharray", "2 3");
      const rot = cur.append("text").attr("class", "anota").attr("y", ih - 6).attr("x", 6).style("font-size", "15px");
      cur.attr("transform", "translate(0,0)")
        .transition().delay(INICIO).duration(DUR).ease(d3.easeLinear)
        .attr("transform", `translate(${x(400)},0)`)
        .tween("tick", () => (t) => { rot.text(`tick ${Math.round(400 * t)}`); })
        .transition().duration(ctx.T(400)).attr("opacity", 0);
      // la marca del momento en que se separan, cuando el cursor llega
      const [tick, texto] = marcas[lam];
      const mg = g.append("g").attr("opacity", 0);
      mg.append("line").attr("x1", x(tick)).attr("x2", x(tick)).attr("y1", 0).attr("y2", ih)
        .attr("stroke", PRIMARIO).attr("stroke-width", 1.6).attr("stroke-dasharray", "6 4");
      const tx = mg.append("text").attr("x", x(tick) + 10).attr("y", y(9.6))
        .style("font-size", "16px").attr("fill", PRIMARIO).attr("font-weight", 700);
      texto.forEach((t, k) => tx.append("tspan").attr("x", x(tick) + 10).attr("dy", k ? 19 : 0).text(t));
      mg.transition().delay(INICIO + (DUR * tick) / 400).duration(ctx.T(350)).attr("opacity", 1);
      // marcadores del final
      for (const pol of pols) {
        const u = d[lam][pol][d[lam][pol].length - 1];
        aparecer(simbolo(g, pol, x(u[0]), y(u[1]), 70), INICIO + DUR);
      }
    });
  };

  F["kb-r3"] = async (ctx) => {
    const f = await datos("kb-r3");
    const W = 500, H = 500, m = { l: 74, r: 110, t: 20, b: 62 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    const x = d3.scaleLinear([-0.015, 0.5], [0, iw]);
    const y = d3.scaleLinear([0, 108], [ih, 0]);
    const g = panel(svg, m.l, m.t, iw, ih);
    ejes(g, x, y, iw, ih, { ticksX: [0, 0.1, 0.25, 0.5], fmtX: d3.format("~g"), rotX: "λ",
      rotY: "utilidad neta  (r = 3, c = 5)" });
    const orden = ["OPEN_LOOP", "CLOSED_LOOP", "BAYESIAN", "MODEL_BASED", "KNOWLEDGE_BASED"];
    const fin = curvasLambda(ctx, g, x, y, f, { orden, destacada: "KNOWLEDGE_BASED", delay: ctx.T(300),
      paso: ctx.T(320), dur: ctx.T(1200) });
    const dy = { MODEL_BASED: 0, KNOWLEDGE_BASED: -8, OPEN_LOOP: 4, BAYESIAN: 0, CLOSED_LOOP: 10 };
    for (const pol of orden) {
      const v = f[pol].find((d) => d.x === 0.5).m;
      const t = g.append("text").attr("x", x(0.5) + 12).attr("y", y(v) + 6 + dy[pol])
        .style("font-size", "17px").attr("fill", TINTA).attr("opacity", 0);
      t.append("tspan").attr("font-weight", 700).attr("fill", COLOR[pol]).text(CORTO[pol] + " ");
      contar(t.append("tspan"), v, 1, ctx.T(500), fin[pol]);
      t.transition().delay(fin[pol]).duration(ctx.T(200)).attr("opacity", 1);
    }
  };

  F.fiabilidad = async (ctx) => {
    const d = await datos("fiabilidad");
    const W = 400, H = 380, m = { l: 66, r: 14, t: 14, b: 60 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    const x = d3.scaleLinear([0, 1], [0, iw]), y = d3.scaleLinear([0, 1], [ih, 0]);
    const g = panel(svg, m.l, m.t, iw, ih);
    ejes(g, x, y, iw, ih, { ticksX: [0, 0.5, 1], ticksY: 2, rejillaX: true, rotX: "probabilidad asignada",
      rotY: "frecuencia observada", sepY: 46 });
    trazar(g.append("path").attr("d", `M${x(0)},${y(0)}L${x(1)},${y(1)}`).attr("stroke", TINTA2)
      .attr("stroke-width", 1.4).attr("stroke-dasharray", "6 5").attr("fill", "none"), ctx.T(700), ctx.T(200));
    const col = COLOR.BAYESIAN;
    trazar(g.append("path").datum(d).attr("fill", "none").attr("stroke", col).attr("stroke-width", 2.6)
      .attr("d", d3.line().x((p) => x(p.x)).y((p) => y(p.y))), ctx.T(1800), ctx.T(900), d3.easeLinear);
    d.forEach((p, k) => {
      const t = ctx.T(900 + 1800 * p.x);
      g.append("line").attr("x1", x(p.x)).attr("x2", x(p.x)).attr("y1", y(p.y)).attr("y2", y(p.y))
        .attr("stroke", col).attr("stroke-width", 2)
        .transition().delay(t).duration(ctx.T(300)).attr("y1", y(p.y - p.e)).attr("y2", y(p.y + p.e));
      g.append("circle").attr("cx", x(p.x)).attr("cy", y(p.y)).attr("r", 0).attr("fill", col)
        .transition().delay(t).duration(ctx.T(200)).attr("r", 5);
    });
    const ley = g.append("g").attr("transform", "translate(10,14)");
    ley.append("line").attr("x2", 24).attr("stroke", TINTA2).attr("stroke-dasharray", "5 4").attr("stroke-width", 1.4);
    ley.append("text").attr("class", "anota").attr("x", 32).attr("y", 5).style("font-size", "15px").text("calibración perfecta");
    ley.append("line").attr("y1", 22).attr("y2", 22).attr("x2", 24).attr("stroke", col).attr("stroke-width", 2.6);
    ley.append("text").attr("class", "anota").attr("x", 32).attr("y", 27).style("font-size", "15px").text("filtro de rejilla");
  };

  F.mecanismo = async (ctx) => {
    const paneles = await datos("mecanismo");
    const W = 1150, H = 250, gap = 34, m = { t: 52, b: 34 };
    const pw = (W - gap * 3) / 4, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    paneles.forEach((p, i) => {
      const g = svg.append("g").attr("transform", `translate(${i * (pw + gap)},${m.t})`);
      g.append("text").attr("class", "tit").attr("x", pw / 2).attr("y", -24).attr("text-anchor", "middle")
        .style("font-size", "17px").text(p.titulo);
      const tope = d3.max(p.barras, (b) => b.m + b.e);
      const x = d3.scaleBand(p.barras.map((b) => b.pol), [0, pw]).padding(0.22);
      const y = d3.scaleLinear([0, tope * 1.32], [ih, 0]);
      g.append("line").attr("x2", pw).attr("y1", ih).attr("y2", ih).attr("stroke", "#8f8c86");
      p.barras.forEach((b, j) => {
        const t = ctx.T(250 + i * 500 + j * 120);
        const bx = x(b.pol);
        g.append("rect").attr("x", bx).attr("width", x.bandwidth()).attr("y", ih).attr("height", 0)
          .attr("fill", COLOR[b.pol])
          .transition().delay(t).duration(ctx.T(650)).ease(d3.easeCubicOut).attr("y", y(b.m)).attr("height", ih - y(b.m));
        g.append("line").attr("x1", bx + x.bandwidth() / 2).attr("x2", bx + x.bandwidth() / 2)
          .attr("y1", y(b.m)).attr("y2", y(b.m)).attr("stroke", TINTA2).attr("opacity", 0)
          .transition().delay(t + ctx.T(600)).duration(ctx.T(250)).attr("opacity", 1).attr("y1", y(b.m - b.e)).attr("y2", y(b.m + b.e));
        contar(g.append("text").attr("x", bx + x.bandwidth() / 2).attr("y", y(b.m) - tope * 0.06 * (ih / (tope * 1.32)) - 6)
          .attr("text-anchor", "middle").style("font-size", "16.5px").attr("fill", TINTA), b.m, p.dec, ctx.T(650), t);
        g.append("text").attr("x", bx + x.bandwidth() / 2).attr("y", ih + 22).attr("text-anchor", "middle")
          .style("font-size", "16px").attr("fill", TINTA2).style("font-family", "var(--mono)").text(CORTO[b.pol]);
      });
    });
  };

  F["quien-gana"] = async (ctx) => {
    const filas = await datos("quien-gana");
    const W = 560, H = 470, m = { l: 196, r: 30, t: 12, b: 60 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    const x = d3.scaleLinear([0, 118], [0, iw]);
    const y = d3.scaleLinear([-0.6, 7.4], [ih, 0]);
    const ys = [6.8, 5.8, 4, 3, 2, 1, 0];
    const g = panel(svg, m.l, m.t, iw, ih);
    g.append("g").attr("class", "rejilla").attr("transform", `translate(0,${ih})`)
      .call(d3.axisBottom(x).ticks(6).tickSize(-ih).tickFormat(""));
    g.append("g").attr("class", "eje").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(6).tickSizeOuter(0));
    g.append("text").attr("class", "rot").attr("x", iw / 2).attr("y", ih + 46).attr("text-anchor", "middle")
      .style("font-size", "16px").text("utilidad neta  (λ = 0.5, c = 5, r = 3)");
    const alto = y(0) - y(0.66);
    filas.forEach((f, k) => {
      const t = ctx.T(300 + k * 260), yy = y(ys[k]);
      g.append("text").attr("x", -10).attr("y", yy + 5).attr("text-anchor", "end").style("font-family", "var(--mono)")
        .style("font-size", "15px").attr("fill", TINTA).text(f.pol);
      g.append("rect").attr("x", 0).attr("y", yy - alto / 2).attr("height", alto).attr("width", 0).attr("fill", COLOR[f.pol])
        .transition().delay(t).duration(ctx.T(800)).ease(d3.easeCubicOut).attr("width", x(f.m));
      g.append("line").attr("y1", yy).attr("y2", yy).attr("x1", x(f.m)).attr("x2", x(f.m)).attr("stroke", TINTA2).attr("opacity", 0)
        .transition().delay(t + ctx.T(750)).duration(ctx.T(250)).attr("opacity", 1).attr("x1", x(f.m - f.e)).attr("x2", x(f.m + f.e));
      contar(g.append("text").attr("x", x(f.m + f.e) + 8).attr("y", yy + 6).style("font-size", "16.5px").attr("fill", TINTA),
        f.m, 1, ctx.T(800), t);
    });
    const sep = y(4.9);
    g.append("line").attr("x1", -m.l + 10).attr("x2", iw).attr("y1", sep).attr("y2", sep).attr("stroke", TINTA2).attr("stroke-dasharray", "2 4");
    g.append("text").attr("class", "anota").attr("x", iw).attr("y", sep - 6).attr("text-anchor", "end").style("font-size", "15px").text("no deliberan ↑");
    g.append("text").attr("class", "anota").attr("x", iw).attr("y", sep + 18).attr("text-anchor", "end").style("font-size", "15px").text("deliberan ↓");
  };

  F.escasez = async (ctx) => {
    const paneles = await datos("escasez");
    const W = 1150, H = 380, m = { l: 74, r: 118, t: 34, b: 60 }, gap = 40;
    const iw = (W - m.l - gap - 2 * m.r) / 2, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    const x = d3.scaleLog().base(2).domain([1.8, 30]).range([0, iw]);
    paneles.forEach((p, i) => {
      const y = d3.scaleLinear(p.y, [ih, 0]);
      const g = panel(svg, m.l + i * (iw + gap + m.r), m.t, iw, ih);
      ejes(g, x, y, iw, ih, { ticksX: [2, 4, 8, 16], fmtX: d3.format("d"), rotX: "recursos simultáneos K",
        rotY: i === 0 ? "diferencia de utilidad (± EE)" : null, titulo: p.titulo });
      if (p.y[0] < 0) g.append("line").attr("x2", iw).attr("y1", y(0)).attr("y2", y(0)).attr("stroke", TINTA2).attr("stroke-width", 1.2);
      p.series.forEach((s, k) => {
        const t = ctx.T(300 + i * 1500 + k * 500), dur = ctx.T(1100);
        g.append("path").datum(s.puntos).attr("fill", s.color).attr("opacity", 0)
          .attr("d", d3.area().x((q) => x(q.x)).y0((q) => y(q.m - q.e)).y1((q) => y(q.m + q.e)))
          .transition().delay(t + dur).duration(ctx.T(400)).attr("opacity", 0.15);
        trazar(g.append("path").datum(s.puntos).attr("fill", "none").attr("stroke", s.color).attr("stroke-width", 2.8)
          .attr("stroke-dasharray", s.punteada ? "8 6" : null)
          .attr("d", d3.line().x((q) => x(q.x)).y((q) => y(q.m))), dur, t);
        s.puntos.forEach((q, j) => {
          g.append("circle").attr("cx", x(q.x)).attr("cy", y(q.m)).attr("r", 0).attr("fill", s.color)
            .transition().delay(t + (dur * j) / 3).duration(ctx.T(200)).attr("r", 5.5);
        });
        const u = s.puntos[s.puntos.length - 1];
        const txt = g.append("text").attr("x", x(u.x) + 12).attr("y", y(u.m) + 5).style("font-size", "15.5px").attr("fill", TINTA).attr("opacity", 0);
        txt.append("tspan").text(s.rotulo.split(",")[0]);
        txt.append("tspan").attr("x", x(u.x) + 12).attr("dy", 18).attr("fill", TINTA2).text(s.rotulo.split(",")[1].trim());
        txt.transition().delay(t + dur).duration(ctx.T(300)).attr("opacity", 1);
      });
    });
  };

  F.sensibilidad = async (ctx) => {
    const filas = await datos("sensibilidad");
    const W = 1150, H = 400, m = { l: 190, r: 40, t: 34, b: 60 }, gap = 44;
    const iw = (W - m.l - m.r - gap) / 2, ih = H - m.t - m.b;
    const svg = lienzo(ctx.el, W, H);
    const ys = []; let yy = 0;
    filas.forEach((f, i) => { if (i && f.barrido !== filas[i - 1].barrido) yy += 0.6; ys.push(yy); yy += 1; });
    const y = d3.scaleLinear([-0.5, yy - 0.5], [0, ih]);
    const x = d3.scaleLinear([0, 0.72], [0, iw]);
    const alto = y(0.78) - y(0);
    [["nivel", "Utilidad de CLOSED_LOOP"], ["dif", "Diferencia OPEN_LOOP − CLOSED_LOOP"]].forEach(([campo, tit], p) => {
      const g = panel(svg, m.l + p * (iw + gap), m.t, iw, ih);
      g.append("g").attr("class", "rejilla").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(7).tickSize(-ih).tickFormat(""));
      g.append("g").attr("class", "eje").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(7).tickSizeOuter(0));
      g.append("text").attr("class", "rot").attr("x", iw / 2).attr("y", ih + 46).attr("text-anchor", "middle").style("font-size", "16px")
        .text("η² (fracción de varianza explicada)");
      g.append("text").attr("class", "tit").attr("x", 0).attr("y", -14).style("font-size", "17px").text(tit);
      filas.forEach((f, i) => {
        const cy = y(ys[i]);
        if (p === 0) {
          g.append("text").attr("x", -12).attr("y", cy + 5).attr("text-anchor", "end").style("font-size", "15.5px")
            .attr("fill", TINTA).text(`${f.barrido}  ${f.factor}`);
        }
        const v = f[campo];
        const t = ctx.T(300 + p * 1700 + i * 140);
        if (v == null) {
          if (f.lambda) g.append("text").attr("class", "anota").attr("x", 6).attr("y", cy + 5).style("font-size", "14px").attr("opacity", 0)
            .text("(sin OPEN_LOOP)").transition().delay(t).duration(ctx.T(300)).attr("opacity", 1);
          return;
        }
        g.append("rect").attr("x", 0).attr("y", cy - alto / 2).attr("height", alto).attr("width", 0)
          .attr("fill", f.lambda ? PRIMARIO : "#a3a29e")
          .transition().delay(t).duration(ctx.T(700)).ease(d3.easeCubicOut).attr("width", x(v));
        g.append("text").attr("x", x(v) + 7).attr("y", cy + 5).style("font-size", "14.5px").attr("fill", TINTA).attr("opacity", 0)
          .text(v >= 0.0005 ? v.toFixed(3) : "0").transition().delay(t + ctx.T(600)).duration(ctx.T(200)).attr("opacity", 1);
      });
    });
  };

  F.abc = async (ctx) => {
    const d = await datos("abc");
    const W = 470, H = 480, m = { l: 62, b: 58, t: 8, r: 8 };
    const hTop = 70, wDer = 70, sep = 8;
    const iw = W - m.l - m.r - wDer - sep, ih = H - m.t - m.b - hTop - sep;
    const svg = lienzo(ctx.el, W, H);
    const x = d3.scaleLinear(d.prior.lam, [0, iw]), y = d3.scaleLinear(d.prior.p, [ih, 0]);
    const g = panel(svg, m.l, m.t + hTop + sep, iw, ih);
    ejes(g, x, y, iw, ih, { rejillaY: false, ticksX: [0, 0.2, 0.4, 0.6, 0.8], ticksY: 5, rotX: "λ", rotY: "p (competencia)", sepY: 46 });
    const gt = svg.append("g").attr("transform", `translate(${m.l},${m.t})`);
    const gd = svg.append("g").attr("transform", `translate(${m.l + iw + sep},${m.t + hTop + sep})`);
    const prev = g.append("g").attr("opacity", 0);
    for (const [a, b] of d.previa) prev.append("circle").attr("cx", x(a)).attr("cy", y(b)).attr("r", 1.6).attr("fill", "#c9c6bf");
    prev.transition().delay(ctx.T(200)).duration(ctx.T(700)).attr("opacity", 1);
    const acc = g.append("g");
    const bins = 20;
    const hx = d3.scaleLinear([0, 1], [hTop, 0]), hy = d3.scaleLinear([0, 1], [0, wDer]);
    const binL = d3.bin().domain(d.prior.lam).thresholds(d3.range(bins + 1).map((i) => d.prior.lam[0] + (i * (d.prior.lam[1] - d.prior.lam[0])) / bins));
    const binP = d3.bin().domain(d.prior.p).thresholds(d3.range(bins + 1).map((i) => d.prior.p[0] + (i * (d.prior.p[1] - d.prior.p[0])) / bins));
    const maxL = d3.max(binL(d.aceptadas.map((q) => q[0])), (b) => b.length);
    const maxP = d3.max(binP(d.aceptadas.map((q) => q[1])), (b) => b.length);
    hx.domain([0, maxL]); hy.domain([0, maxP]);
    const barrasL = gt.selectAll("rect").data(binL([])).join("rect").attr("fill", PRIMARIO).attr("opacity", 0.85);
    const barrasP = gd.selectAll("rect").data(binP([])).join("rect").attr("fill", PRIMARIO).attr("opacity", 0.85);
    function hist(n) {
      const sub = d.aceptadas.slice(0, n);
      gt.selectAll("rect").data(binL(sub.map((q) => q[0]))).join("rect").attr("fill", PRIMARIO).attr("opacity", 0.85)
        .attr("x", (b) => x(b.x0) + 0.5).attr("width", (b) => Math.max(0, x(b.x1) - x(b.x0) - 1))
        .attr("y", (b) => hx(b.length)).attr("height", (b) => hTop - hx(b.length));
      gd.selectAll("rect").data(binP(sub.map((q) => q[1]))).join("rect").attr("fill", PRIMARIO).attr("opacity", 0.85)
        .attr("y", (b) => y(b.x1) + 0.5).attr("height", (b) => Math.max(0, y(b.x0) - y(b.x1) - 1))
        .attr("x", 0).attr("width", (b) => hy(b.length));
    }
    void barrasL; void barrasP;
    hist(0);
    const N = d.aceptadas.length, DUR = ctx.T(3200), INI = ctx.T(1000);
    d.aceptadas.forEach(([a, b], k) => {
      acc.append("circle").attr("cx", x(a)).attr("cy", y(b)).attr("r", 0).attr("fill", PRIMARIO).attr("opacity", 0.85)
        .transition().delay(INI + (DUR * k) / N).duration(ctx.T(220)).attr("r", 3.4);
    });
    const contador = g.append("text").attr("class", "anota").attr("x", iw - 6).attr("y", 18).attr("text-anchor", "end").style("font-size", "15px");
    let n = 0;
    const paso = () => {
      n = Math.min(N, n + Math.ceil(N / 40));
      hist(n);
      contador.text(`aceptadas: ${n} de 3.000`);
      if (n < N) ctx.despues(DUR / 40, paso);
    };
    ctx.despues(INI, paso);
    // verdad e intervalos al final
    const fin = INI + DUR + ctx.T(200);
    const [vl, vp] = d.verdad;
    const est = g.append("path").attr("d", d3.symbol(d3.symbolStar, 340)()).attr("fill", ALERTA)
      .attr("stroke", "white").attr("stroke-width", 1.2).attr("transform", `translate(${x(vl)},${y(vp)}) scale(0)`);
    est.transition().delay(fin).duration(ctx.T(400)).ease(d3.easeBackOut.overshoot(2.5))
      .attr("transform", `translate(${x(vl)},${y(vp)}) scale(1)`);
    const lineas = svg.append("g").attr("opacity", 0);
    lineas.append("line").attr("x1", m.l + x(vl)).attr("x2", m.l + x(vl)).attr("y1", m.t).attr("y2", m.t + hTop).attr("stroke", ALERTA).attr("stroke-width", 2);
    lineas.append("line").attr("y1", m.t + hTop + sep + y(vp)).attr("y2", m.t + hTop + sep + y(vp)).attr("x1", m.l + iw + sep).attr("x2", m.l + iw + sep + wDer).attr("stroke", ALERTA).attr("stroke-width", 2);
    for (const q of d.ic.lam) lineas.append("line").attr("x1", m.l + x(q)).attr("x2", m.l + x(q)).attr("y1", m.t).attr("y2", m.t + hTop).attr("stroke", TINTA).attr("stroke-dasharray", "2 3");
    for (const q of d.ic.p) lineas.append("line").attr("y1", m.t + hTop + sep + y(q)).attr("y2", m.t + hTop + sep + y(q)).attr("x1", m.l + iw + sep).attr("x2", m.l + iw + sep + wDer).attr("stroke", TINTA).attr("stroke-dasharray", "2 3");
    lineas.transition().delay(fin).duration(ctx.T(400)).attr("opacity", 1);
    const ley = g.append("g").attr("transform", `translate(${iw - 196},${ih - 70})`).attr("opacity", 0);
    ley.append("rect").attr("x", -8).attr("y", -16).attr("width", 200).attr("height", 76).attr("fill", FONDO).attr("opacity", 0.9);
    [["#c9c6bf", "previa simulada", "c"], [PRIMARIO, `aceptadas (${N})`, "c"], [ALERTA, "verdad (λ*, p*)", "s"]].forEach(([c, t, s], k) => {
      if (s === "c") ley.append("circle").attr("cx", 4).attr("cy", k * 22).attr("r", 4.5).attr("fill", c);
      else ley.append("path").attr("d", d3.symbol(d3.symbolStar, 120)()).attr("transform", `translate(4,${k * 22})`).attr("fill", c);
      ley.append("text").attr("class", "anota").attr("x", 16).attr("y", k * 22 + 5).style("font-size", "14.5px").text(t);
    });
    ley.transition().delay(fin).duration(ctx.T(400)).attr("opacity", 1);
  };

  /* ---------------------------------------------------------------- mundos */
  async function mundo(ctx, op) {
    const ind = await Mundo.indice();
    const ret = ind.semillas[String(op.semilla)];
    const co = await Mundo.corrida(op.semilla, op.pol, op.lam, op.c, ind.sin_c);
    const cv = document.createElement("canvas");
    ctx.el.appendChild(cv);
    const vista = new Mundo.Vista(cv, ret, { px: op.px, colorAgente: Mundo.colores.agente });
    vista.setCorrida(co);
    const est = d3.select(ctx.el).append("div").attr("class", "estado");
    const rep = new Mundo.Reproductor((t) => vista.dibujar(t), {
      tps: op.tps, fin: op.fin, bucle: true,
      alTick: (tk) => {
        const del = co.d[tk] ? " · deliberando" : "";
        est.html(`tick <b>${tk}</b> · entregas <b>${co.ent[tk]}</b> · lleva ${co.car[tk]}/3 · ` +
          `ediciones ${co.edi[tk]}${del}`);
      },
    });
    rep.ir(0);
    if (!quieto) ctx.despues(400, () => rep.play());
    ctx.alDetener(() => rep.pause());
  }
  F["mundo-cl"] = (ctx) => mundo(ctx, { semilla: 3, pol: "CLOSED_LOOP", lam: 0.25, c: 5, px: 430, tps: 5, fin: 160 });

  F["mundo-kb"] = async (ctx) => {
    const kb = await datos("kb-corrida");
    const cv = document.createElement("canvas");
    ctx.el.appendChild(cv);
    const vista = new Mundo.Vista(cv, kb.reticula, { px: 300, regiones: true, creencias: true });
    vista.setCorrida(kb.corrida);
    const est = d3.select(ctx.el).append("div").attr("class", "estado");
    const n = kb.corrida.ag.length - 1;
    const rep = new Mundo.Reproductor((t) => vista.dibujar(t), {
      tps: 4, fin: n, bucle: true,
      alTick: (tk) => {
        const celdas = new Set(Object.values(kb.corrida.reg[tk] || {}).flat()).size;
        est.html(`tick <b>${tk}</b> · región posible: <b>${celdas}</b> celdas` +
          (kb.corrida.d[tk] ? " · deliberando" : ""));
      },
    });
    rep.ir(0);
    if (!quieto) ctx.despues(400, () => rep.play());
    ctx.alDetener(() => rep.pause());
  };

  /* ------------------------------------------------------------------- API */
  global.Graficas = {
    figuras: F,
    async iniciar(el) {
      const nombre = el.dataset.anim;
      if (!F[nombre]) return;
      Graficas.detener(el);
      el.innerHTML = "";
      // cada arranque dibuja en un contenedor propio: si los datos llegan después de
      // salir de la diapositiva, lo que se dibuje cae en un nodo ya desprendido
      const host = document.createElement("div");
      el.appendChild(host);
      const ctx = contexto(host);
      el._ctx = ctx;
      try { await F[nombre](ctx); } catch (e) { console.error(`[graficas] ${nombre}`, e); }
    },
    detener(el) {
      // se detiene pero no se borra: la diapositiva sale con la figura completa en la
      // transición, y la próxima entrada la redibuja desde cero
      if (el._ctx) el._ctx.detener();
      el._ctx = null;
    },
    precargar(nombres) { nombres.forEach((n) => datos(n).catch(() => {})); },
    COLOR, CORTO,
  };
})(window);
