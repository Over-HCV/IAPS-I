#!/usr/bin/env bash
# build.sh — compila las diapositivas del proyecto final.
#
#   ./build.sh          main.tex -> main.pdf
#   ./build.sh clean    borra auxiliares (deja el PDF)
#
# LuaLaTeX porque Midcentury carga fuentes con fontspec. latexmk repite las
# pasadas que hagan falta: la portada y la marca de agua usan
# `remember picture` y con una sola pasada salen vacías sin avisar.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ "${1:-}" = "clean" ]; then
  latexmk -c -lualatex main.tex
  exit 0
fi

# -g: las figuras entran por \IfFileExists y latexmk no las ve como
# dependencias; sin forzar, una figura nueva no reconstruye el PDF.
latexmk -g -lualatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null \
  || { tail -40 main.log; exit 1; }

# Lo que importa revisar: frames que no caben (vbox) y figuras que faltan.
grep -n "Overfull \\\\vbox" main.log || true
grep -c "falta figuras/" main.log >/dev/null 2>&1 || true
echo "✓ main.pdf ($(pdfinfo main.pdf 2>/dev/null | awk '/Pages/{print $2}') páginas)"
