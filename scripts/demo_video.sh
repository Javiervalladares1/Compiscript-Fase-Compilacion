#!/usr/bin/env bash
# Demostracion guiada para grabar. --auto ejecuta todos los pasos sin pausas.
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
INTERACTIVE=1
if [[ "${1:-}" == "--auto" ]]; then
  INTERACTIVE=0
  shift
fi
if [[ $# -ne 0 ]]; then
  printf 'Uso: bash scripts/demo_video.sh [--auto]\n' >&2
  exit 2
fi
PYTHON="$PROJECT_ROOT/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  printf 'Primero prepara el entorno con bash scripts/start_ide.sh.\n' >&2
  exit 1
fi
if ! command -v spim >/dev/null 2>&1; then
  printf 'Se necesita SPIM en PATH para esta demostracion.\n' >&2
  exit 1
fi

step() {
  printf '\n========== %s ==========\n' "$1"
  if [[ "$INTERACTIVE" == 1 && -t 0 ]]; then
    read -r -p 'Presiona Enter cuando estes listo para mostrar este paso... '
  fi
}

step '1. Programa fuente: factorial recursivo'
cat examples/mips/01_factorial.cps

step '2. Compilacion del fuente a TAC y MIPS'
"$PYTHON" program/Driver.py examples/mips/01_factorial.cps \
  --tac out/video/factorial.tac --mips out/video/factorial.asm

step '3. TAC: parametros, llamadas, temporales y retornos'
cat out/video/factorial.tac

step '4. MIPS: guardar estado, llamar y restaurar la pila'
awk '/addiu \$sp|sw \$ra|lw \$ra|sw \$fp|lw \$fp|jal |jr \$ra/ {print NR ": " $0}' out/video/factorial.asm

step '5. Ejecutar el assembler directamente en la herramienta externa SPIM'
spim -file out/video/factorial.asm

step '6. Mas de cuatro argumentos y llamadas anidadas'
"$PYTHON" program/Driver.py examples/mips/02_llamadas_y_parametros.cps \
  --tac out/video/llamadas.tac --mips out/video/llamadas.asm --run

step '7. Estrategia alternativa: resultados respaldados en pila'
"$PYTHON" program/Driver.py examples/mips/01_factorial.cps \
  --allocation stack --mips out/video/factorial_pila.asm --run

step '8. Pruebas de la fase 3'
"$PYTHON" -m pytest tests/test_mips.py -q

printf '\nDemostracion terminada. Artefactos en out/video/.\n'
