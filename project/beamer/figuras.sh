#!/usr/bin/env bash
# figuras.sh — todas las figuras de la presentación final, en figuras/.
#
#   ./figuras.sh              copia las de resultados y genera las de diapositiva
#   ./figuras.sh frontera abc solo regenera las nombradas (ver figuras.py)
#
# Dos fuentes, ninguna dibujada a mano:
#   1. Copias tal cual de project/results/animaciones/ (las tiras completas,
#      que entran al respaldo).
#   2. figuras.py: las mismas cifras redibujadas a tamaño de diapositiva (16:9,
#      tipografía del tema, una política = un color en todo el deck), leídas de
#      los CSV y parquet de project/results/ con las funciones del paquete.
#
# Se puede llamar desde cualquier carpeta: el script se ubica solo y corre
# Python desde la raíz del repositorio, que es donde `import project` funciona.
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="$(cd "$AQUI/../.." && pwd)"
RESULTADOS="$RAIZ/project/results"
SALIDA="$AQUI/figuras"
mkdir -p "$SALIDA"

# El .venv del repositorio; si se movió de disco y no arranca, uv lo resuelve.
if "$RAIZ/.venv/bin/python" -c "import project" >/dev/null 2>&1 \
   || (cd "$RAIZ" && "$RAIZ/.venv/bin/python" -c "import project") >/dev/null 2>&1; then
  PY=("$RAIZ/.venv/bin/python")
else
  PY=(uv run --project "$RAIZ" python)
fi

# --- 1. copias de resultados ---------------------------------------------------
# Solo las tiras completas de seis instantáneas (respaldo): el resto de las
# figuras del documento son anchas de tres o cuatro paneles y en una diapositiva
# no se leen, así que figuras.py las redibuja a la escala de la diapositiva.
if [ "$#" -eq 0 ]; then
  for f in tira-knowledge-based tira-bayesian; do
    cp "$RESULTADOS/animaciones/$f.png" "$SALIDA/$f.png"
  done
  echo "copiadas de results/animaciones/: tira-knowledge-based, tira-bayesian"
fi

# --- 2. figuras de diapositiva ---------------------------------------------------
cd "$RAIZ"
MPLBACKEND=Agg PYTHONPATH="$RAIZ${PYTHONPATH:+:$PYTHONPATH}" \
  "${PY[@]}" "$AQUI/figuras.py" "$@"

echo "figuras en $SALIDA: $(ls -1 "$SALIDA" | wc -l | tr -d ' ') archivos"

# --- 3. datos del deck web ---------------------------------------------------------
# Los mismos resultados en JSON para web/ (gráficas animadas y simulador). Sin
# argumentos se exporta todo, incluidas las 120 corridas del simulador.
if [ "$#" -eq 0 ]; then
  MPLBACKEND=Agg PYTHONPATH="$RAIZ${PYTHONPATH:+:$PYTHONPATH}" \
    "${PY[@]}" "$AQUI/web/exportar.py"
fi
