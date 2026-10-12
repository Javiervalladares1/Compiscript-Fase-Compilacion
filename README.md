# Compiscript — Fase de compilación

Frontend de Compiscript escrito en Python con ANTLR 4.13.1.

Esta primera entrega contiene **50 de los 100 archivos originales**. La división
se hizo por cantidad de archivos, conservando las dependencias del núcleo para
que el compilador se pueda ejecutar desde un clon del repositorio.

## Incluido

- Gramática de Compiscript y lexer, parser, listener y visitor generados por ANTLR.
- Construcción, serialización y visualización del AST.
- Sistema de tipos, tabla de símbolos y análisis semántico.
- API de compilación e interfaz de línea de comandos.
- Herramientas para regenerar el parser y entorno Docker.
- Programa principal y dos ejemplos: uno válido y uno con error de sintaxis.

## Requisitos

- Python 3.10 o superior.
- Java 11 o superior, solo para regenerar el parser.
- Graphviz, opcional para exportar imágenes del AST.

## Inicio rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 program/Driver.py program/program.cps
```

Los archivos generados por ANTLR ya están incluidos. Para regenerarlos:

```bash
./scripts/generate_parser.sh
```

## Usar el compilador

```bash
# Analizar un programa válido
python3 program/Driver.py examples/valid/01_tipos_basicos.cps

# Verificar un error sintáctico; devuelve código de salida 1
python3 program/Driver.py examples/invalid/14_sintaxis.cps

# Exportar el AST a JSON
python3 program/Driver.py program/program.cps --ast-json ast.json

# Imprimir la tabla de símbolos
python3 program/Driver.py program/program.cps --symbols

# Ejecutar únicamente análisis léxico y sintáctico
python3 program/Driver.py program/program.cps --syntax-only

# Ver todas las opciones
python3 program/Driver.py --help
```

## Estructura

```text
compiler/       Parser, AST, tipos, símbolos, análisis semántico, API y CLI
program/        Gramática, archivos generados, Driver.py y programa principal
examples/       Dos ejemplos incluidos en esta entrega
scripts/        Generación del parser
commands/       Comandos auxiliares de ANTLR para Docker
Dockerfile      Entorno del curso
requirements.txt
```

## Segunda mitad

Los otros **50 archivos originales** contienen el IDE web, la batería de pruebas,
la documentación, las contribuciones, la configuración local y los ejemplos
restantes.

Se conservaron en la carpeta local `pendiente/archivos/`, respetando sus rutas
originales. `pendiente/README.md` explica cómo integrarlos después.
La carpeta `pendiente/` está excluida de Git y no se descarga al clonar este repo.
Las versiones originales de este README y de `.gitignore` se conservaron en
`pendiente/originales/`.
