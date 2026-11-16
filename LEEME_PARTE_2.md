# Parte 2 — IDE, pruebas y documentación

Este paquete complementa la fase de generación de código del repositorio:

https://github.com/Javiervalladares1/Compiscript-Fase-Compilacion

La parte 1 contiene el compilador, TAC, MIPS, simulador y seis ejemplos.
La parte 2 agrega el IDE, todas las pruebas, ejemplos restantes y documentación.
La división se hizo por componentes. Ambas partes forman una sola entrega.

## Integración

1. Actualiza el clon del repositorio o descárgalo desde GitHub.
2. Extrae **el contenido de este ZIP directamente en la raíz del proyecto**,
   junto a `compiler/`, `program/` y `README.md`. Deben quedar `ide/app.py`,
   `tests/test_mips.py` y `docs/FASE3_MIPS.md` en esas rutas.
3. Conserva el README de la parte 1. El manifiesto identifica el commit y los
   hashes de los archivos compatibles. La carpeta histórica `archivos/` no se
   utiliza para ejecutar esta fase.

Por terminal, estando en la raíz del clon actualizado:

```bash
python3 -m zipfile -e /ruta/parte2_ide_pruebas_documentacion.zip .
python3 scripts/empaquetar_fase3.py --verify /ruta/parte2_ide_pruebas_documentacion.zip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

En Windows utiliza `.venv\Scripts\activate` para activar el entorno. También
puedes extraer el ZIP con la herramienta del sistema, respetando las rutas.

## Ejecución

Instala SPIM para ejecutar el assembler: `brew install spim` en macOS o
`sudo apt install spim` en Debian/Ubuntu. También se incluye en la imagen Docker.

```bash
python program/Driver.py examples/mips/01_factorial.cps --run
python program/Driver.py program/program.cps --mips out/programa.asm --run
python -m pytest -o addopts='' -q
bash scripts/start_ide.sh
```

Abre **http://127.0.0.1:5001**. En Windows, el IDE se inicia igualmente con
`python ide/app.py --port 5001`. No requiere descargar bibliotecas de JavaScript.

El IDE permite escribir código, seleccionar el modo de registros o pila,
inspeccionar las etapas y descargar o ejecutar MIPS. El programa del curso
incluye una advertencia esperada de índice inválido dentro de un `try`; deja
el modo estricto desactivado para demostrar su captura en ejecución.

## Contenido y validación

- `docs/FASE3_MIPS.md`: algoritmos, convención de llamadas y alcance.
- `docs/architecture.md`: arquitectura de todas las etapas.
- `docs/REQUISITOS_FASE3.md`: correspondencia con los requisitos del curso.
- `docs/VALIDACION_FASE3.md`: resultados reales de pruebas y del navegador.
- `tests/`: batería completa; los casos MIPS requieren SPIM en PATH.
- `CONTRIBUTIONS.md`: plantilla para registrar los tres integrantes y sus
  contribuciones reales. Los nombres y la autoría no se inventan.
- `MANIFIESTO_PARTE2.json`: inventario y SHA-256 de ambas partes.

Para presentar el proyecto, integra este paquete y conserva la batería de
pruebas. Si luego agregas la parte 2 a GitHub, incluye sus rutas originales;
la carpeta `out/` y los respaldos locales permanecen fuera del repositorio.
