/* sincro.js — el deck y el servidor local (servidor.py).
 *
 * - Escucha /api/eventos (SSE): Las órdenes que manda el celular desde control.html.
 * - Reporta a /api/estado la diapositiva actual, para que el celular la muestre.
 * - Tecla Q: Panel privado con el QR del control (solo lo entrega el servidor a esta
 *   máquina, nunca a quien entra por el túnel).
 *
 * Abierto como archivo (file://) o sin servidor, el deck funciona igual con teclado.
 */
(function (global) {
  "use strict";

  const conServidor = location.protocol === "http:" || location.protocol === "https:";
  const punto = () => document.getElementById("aviso-conexion");
  let ultimo = null;

  function qr(el, texto, celda = 6) {
    if (!el || !texto || !global.qrcode) return;
    const q = global.qrcode(0, "M");
    q.addData(texto);
    q.make();
    el.innerHTML = q.createSvgTag({ cellSize: celda, margin: 2, scalable: true });
  }

  async function config() {
    if (!conServidor) return {};
    try {
      const r = await fetch("/api/config", { cache: "no-store" });
      return r.ok ? await r.json() : {};
    } catch { return {}; }
  }

  function ordenar(m) {
    if (!global.Reveal) return;
    if (m.ir === "next") Reveal.next();
    else if (m.ir === "prev") Reveal.prev();
    else if (m.ir === "inicio") Reveal.slide(0);
    else if (Number.isInteger(m.ir)) Reveal.slide(m.ir);
  }

  function conectar() {
    if (!conServidor || !global.EventSource) return;
    const es = new EventSource("/api/eventos");
    es.onopen = () => { punto()?.classList.add("vivo"); reportar(true); };
    es.onerror = () => punto()?.classList.remove("vivo");
    es.onmessage = (e) => { try { ordenar(JSON.parse(e.data)); } catch { /* latido */ } };
  }

  function reportar(forzar = false) {
    if (!conServidor || !global.Reveal) return;
    const s = Reveal.getCurrentSlide();
    const idx = Reveal.getIndices().h;
    const estado = {
      i: idx,
      total: Reveal.getTotalSlides(),
      n: s.dataset.numero ? +s.dataset.numero : null,
      de: document.querySelectorAll(".reveal .slides > section[data-numero]").length,
      respaldo: s.hasAttribute("data-respaldo"),
      titulo: s.dataset.titulo || (s.querySelector(".relevo h2")?.textContent ?? "") ||
        s.querySelector("img")?.alt || (idx === 0 ? "Portada" : ""),
    };
    const clave = JSON.stringify(estado);
    if (!forzar && clave === ultimo) return;
    ultimo = clave;
    fetch("/api/estado", { method: "POST", headers: { "Content-Type": "application/json" }, body: clave })
      .catch(() => {});
  }

  async function panel() {
    const p = document.getElementById("panel-control");
    const visible = p.classList.toggle("visible");
    if (!visible) return;
    const c = await config();
    const url = p.querySelector(".url");
    if (c.control) {
      qr(p.querySelector(".qr"), c.control, 6);
      url.textContent = c.control;
    } else {
      p.querySelector(".qr").innerHTML = "";
      url.textContent = conServidor
        ? "El servidor no entregó la URL de control (¿se abrió por el túnel?)."
        : "Sin servidor: Correr  python web/servidor.py --tunel";
    }
  }

  global.Sincro = { conectar, reportar, config, qr, panel };
})(window);
