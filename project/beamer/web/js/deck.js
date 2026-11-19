/* deck.js — arranque del deck: Reveal, pie y numeración, entradas, animaciones. */
(function () {
  "use strict";

  const quieto = new URLSearchParams(location.search).has("quieto");
  if (quieto) document.documentElement.classList.add("quieto");
  const todas = [...document.querySelectorAll(".reveal .slides > section")];

  /* ---------------------------------------------- numeración como en beamer */
  // La portada cuenta (sin pie); los relevos, «Gracias» y el respaldo no cuentan.
  const numeradas = todas.filter((s) =>
    !s.classList.contains("relevo-s") && !s.hasAttribute("data-respaldo") && !s.hasAttribute("data-sin-numero"));
  const total = numeradas.length;
  numeradas.forEach((s, k) => {
    s.dataset.numero = k + 1;
    const marco = s.querySelector(".marco");
    if (!marco) return;
    const pie = document.createElement("div");
    pie.className = "pie";
    pie.innerHTML = `<span>Over H. C. V.</span><span>Planes auto-editables</span>` +
      `<span><b>${k + 1}</b> / ${total}</span><div class="avance" style="width:${((k + 1) / total) * 100}%"></div>`;
    marco.appendChild(pie);
  });

  /* ------------------------------------------------- entradas escalonadas */
  for (const s of todas) {
    s.querySelectorAll(".e").forEach((el, i) => el.style.setProperty("--i", Math.min(i, 14)));
  }

  /* --------------------------------------------------------- matemáticas */
  if (window.renderMathInElement) {
    renderMathInElement(document.querySelector(".reveal"), {
      delimiters: [{ left: "\\(", right: "\\)", display: false }], throwOnError: false,
    });
  }

  /* ---------------------------------------------------- cifras que cuentan */
  function contarCifras(s) {
    const fmt = (n) => Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    s.querySelectorAll(".cuenta").forEach((el, k) => {
      const v = +el.dataset.v;
      if (quieto) { el.textContent = fmt(v); return; }
      d3.select(el).interrupt().text(fmt(0)).transition().delay(200 + k * 180).duration(1400)
        .ease(d3.easeCubicOut).tween("text", () => {
          const i = d3.interpolateNumber(0, v);
          return (t) => { el.textContent = fmt(i(t)); };
        });
    });
  }

  /* ------------------------------------- fondo vivo de portada y relevos */
  // Decorativo: Recursos que derivan por una retícula 32 × 18 (la de la portada) y un
  // agente que va hacia el más cercano. Los datos están en las diapositivas, no aquí.
  function fondoVivo(canvas) {
    const W = 1280, H = 720, N = 32, M = 18, k = W / N;
    const esc = 2;
    canvas.width = W * esc; canvas.height = H * esc;
    const ctx = canvas.getContext("2d");
    ctx.scale(esc, esc);
    const rnd = d3.randomLcg(7);
    const azar = (n) => Math.floor(rnd() * n);
    const rec = d3.range(8).map(() => ({ x: azar(N), y: azar(M), px: 0, py: 0, t: 0 }));
    rec.forEach((r) => { r.px = r.x; r.py = r.y; });
    const ag = { x: 6, y: 9, px: 6, py: 9 };
    const estela = [];
    let ult = null, acum = 0, raf = 0;
    const PASO = 650;
    function paso() {
      for (const r of rec) {
        r.px = r.x; r.py = r.y;
        if (rnd() < 0.35) {
          const [dx, dy] = [[1, 0], [-1, 0], [0, 1], [0, -1]][azar(4)];
          r.x = Math.min(N - 1, Math.max(0, r.x + dx)); r.y = Math.min(M - 1, Math.max(0, r.y + dy));
        }
      }
      ag.px = ag.x; ag.py = ag.y;
      const obj = rec.reduce((a, b) => (Math.abs(b.x - ag.x) + Math.abs(b.y - ag.y) < Math.abs(a.x - ag.x) + Math.abs(a.y - ag.y) ? b : a));
      if (obj.x !== ag.x) ag.x += Math.sign(obj.x - ag.x); else if (obj.y !== ag.y) ag.y += Math.sign(obj.y - ag.y);
      if (ag.x === obj.x && ag.y === obj.y) { obj.x = azar(N); obj.y = azar(M); obj.px = obj.x; obj.py = obj.y; }
      estela.push([ag.x, ag.y]); if (estela.length > 18) estela.shift();
    }
    function pintar(f) {
      ctx.clearRect(0, 0, W, H);
      const e = f < 0.5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2;
      ctx.strokeStyle = "rgba(191,229,238,0.35)"; ctx.lineWidth = 1.4; ctx.setLineDash([2, 4]);
      ctx.beginPath();
      estela.forEach(([x, y], i) => { const X = (x + 0.5) * k, Y = (y + 0.5) * k; i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); });
      ctx.stroke(); ctx.setLineDash([]);
      for (const r of rec) {
        const X = (r.px + (r.x - r.px) * e + 0.5) * k, Y = (r.py + (r.y - r.py) * e + 0.5) * k;
        const g = ctx.createRadialGradient(X, Y, 0, X, Y, k * 1.6);
        g.addColorStop(0, "rgba(245,154,60,0.55)"); g.addColorStop(1, "rgba(245,154,60,0)");
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(X, Y, k * 1.6, 0, 7); ctx.fill();
        ctx.fillStyle = "#f59a3c"; ctx.beginPath(); ctx.arc(X, Y, 4.5, 0, 7); ctx.fill();
      }
      const AX = (ag.px + (ag.x - ag.px) * e + 0.5) * k, AY = (ag.py + (ag.y - ag.py) * e + 0.5) * k;
      ctx.fillStyle = "#e9f6fa"; ctx.beginPath(); ctx.arc(AX, AY, 6, 0, 7); ctx.fill();
      ctx.strokeStyle = "rgba(191,229,238,0.7)"; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(AX, AY, 12, 0, 7); ctx.stroke();
    }
    function bucle(ahora) {
      if (ult != null) acum += ahora - ult;
      ult = ahora;
      while (acum >= PASO) { acum -= PASO; paso(); }
      pintar(acum / PASO);
      raf = requestAnimationFrame(bucle);
    }
    paso();
    if (quieto) pintar(1); else raf = requestAnimationFrame(bucle);
    return () => cancelAnimationFrame(raf);
  }

  /* ------------------------------------------------------ simulador */
  let configCache = null;
  async function prepararSimulador(s, entrar) {
    const fr = s.querySelector("iframe");
    if (fr && entrar && !fr.src) fr.src = fr.dataset.src;
    if (fr && fr.contentWindow) fr.contentWindow.postMessage({ simulador: entrar ? "play" : "pausa" }, "*");
    if (!entrar) return;
    configCache = configCache || (await Sincro.config());
    const url = configCache.publico;
    const caja = s.querySelector(".qr-publico"), texto = s.querySelector(".url-publica");
    if (url) { Sincro.qr(caja, url, 6); texto.textContent = url.replace(/^https?:\/\//, ""); }
    else { caja.innerHTML = ""; texto.textContent = "Sin enlace público: Correr servidor.py --tunel"; }
  }

  /* ------------------------------------------------- ciclo por diapositiva */
  const paradas = new Map();
  function entrar(s) {
    s.querySelectorAll("[data-anim]").forEach((el) => Graficas.iniciar(el));
    contarCifras(s);
    const cv = s.querySelector("canvas.vivo");
    if (cv) paradas.set(s, fondoVivo(cv));
    if (s.hasAttribute("data-simulador")) prepararSimulador(s, true);
  }
  function salir(s) {
    if (!s) return;
    s.querySelectorAll("[data-anim]").forEach((el) => Graficas.detener(el));
    if (paradas.has(s)) { paradas.get(s)(); paradas.delete(s); }
    if (s.hasAttribute("data-simulador")) prepararSimulador(s, false);
  }

  Graficas.precargar(["frontera", "abierto-cerrado", "caliente-frio", "dinamica", "kb-r3",
    "fiabilidad", "mecanismo", "quien-gana", "escasez", "sensibilidad", "abc", "kb-corrida"]);

  Reveal.initialize({
    width: 1280, height: 720, margin: 0, minScale: 0.1, maxScale: 4,
    center: false, hash: true, controls: false, progress: false, slideNumber: false,
    transition: "fade", transitionSpeed: "fast", backgroundTransition: "none",
    keyboard: { 81: () => Sincro.panel() },
    plugins: window.RevealNotes ? [RevealNotes] : [],
  }).then(() => {
    entrar(Reveal.getCurrentSlide());
    Sincro.conectar();
    Sincro.reportar(true);
  });
  Reveal.on("slidechanged", (ev) => {
    salir(ev.previousSlide);
    entrar(ev.currentSlide);
    Sincro.reportar();
  });
})();
