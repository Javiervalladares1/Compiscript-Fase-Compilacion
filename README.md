# Compiscript — Generación de código MIPS

Compilador en Python con ANTLR 4.13.1. Traduce programas `.cps` a un AST tipado,
código de tres direcciones (TAC) y MIPS32 que se ejecuta en SPIM.

## Entrega en dos partes

1. **Repositorio: núcleo del compilador.** Incluye análisis léxico, sintáctico
   y semántico, TAC, backend MIPS, `getReg()`, marcos de pila, ejecución en SPIM,
   seis ejemplos y entorno Docker. Funciona por línea de comandos sin la parte 2.
2. **ZIP `parte2_ide_pruebas_documentacion.zip`.** Incluye el IDE, la batería
   completa de pruebas, documentación de arquitectura y uso, ejemplos del
   frontend y plantilla de contribuciones. Se extrae **en la raíz de este
   repositorio**, conservando las carpetas `ide/`, `tests/`, `docs/`, etc.

El ZIP incluye `LEEME_PARTE_2.md` y un manifiesto con hashes para comprobar su
contenido. La separación es por componentes, no por cantidad de archivos.
La carpeta `archivos/` que pueda existir en GitHub es un respaldo de la entrega
anterior; para esta fase se utiliza la estructura de la raíz y el ZIP nuevo.

## Inicio rápido: parte 1

Requiere Python 3.10 o posterior. Java 11 o posterior solamente se necesita
para regenerar el parser; los archivos generados ya están incluidos.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python program/Driver.py examples/mips/01_factorial.cps \
  --tac out/factorial.tac --mips out/factorial.asm
```

Para ejecutar el resultado, instala SPIM (`brew install spim` en macOS o
`sudo apt install spim` en Debian/Ubuntu) y utiliza:

```bash
python program/Driver.py examples/mips/01_factorial.cps --run
# Salida: 120, 720 y 5040, cada numero en una linea.

spim -file out/factorial.asm

# La misma compilacion utilizando la estrategia de pila:
python program/Driver.py examples/mips/01_factorial.cps --allocation stack --run

# Programa completo del curso, con clases y try/catch:
python program/Driver.py program/program.cps --mips out/programa.asm --run
```

`--run` usa el ejecutable real de SPIM. Generar `.tac` y `.asm` no requiere el
simulador. El assembler usa instrucciones y syscalls comunes a SPIM y MARS;
la validación automatizada utiliza SPIM.

## IDE y pruebas: parte 2

Después de extraer el ZIP en la raíz:

```bash
bash scripts/start_ide.sh
```

Abre **http://127.0.0.1:5001**. Permite editar código, elegir registros o pila,
examinar diagnósticos, AST, símbolos, TAC y MIPS, descargar `.tac`/`.asm`, y
ver la salida de SPIM. Incluye ejemplos de recursión, llamadas, arreglos,
funciones anidadas, herencia, excepciones y el programa completo del curso.

```bash
source .venv/bin/activate
python -m pytest -o addopts='' -q
```

Las pruebas de ejecución se omiten cuando SPIM no está instalado; para validar
la entrega completa debe estar disponible en `PATH`.

La guía `docs/FASE3_MIPS.md` explica los algoritmos y su alcance;
`docs/architecture.md` describe la arquitectura y
`docs/REQUISITOS_FASE3.md` relaciona cada requisito con código y pruebas.

## Funcionalidad

- Llamadas y retornos con `$sp`, `$fp`, `$ra`, parámetros en registros y pila,
  preservación de `$s0-$s7`, recursión directa, mutua y llamadas anidadas.
- Asignación mediante `getReg()`, descriptores, siguiente uso y spill a memoria;
  estrategia alternativa de pila.
- `integer`, `boolean`, `string`, `null`, arreglos y matrices; extensión `float`
  y `void` conservada del frontend anterior.
- Operadores, cortocircuito, ternario, ciclos, `foreach`, `switch`, `break`,
  `continue` y retornos tempranos.
- Funciones anidadas con capturas por enlace estático mientras su entorno está
  activo; clases, inicializadores, constructores heredados y métodos virtuales.
- `try/catch` para división por cero, índices inválidos y acceso a objetos nulos,
  incluso si el error ocurre en una función llamada.

Se diagnostican con `GEN001` los valores de función escapables o indirectos,
la impresión directa de arreglos/objetos, la concatenación con `float`, el
módulo `float`, los literales fuera del rango de MIPS y marcos demasiado grandes.
Los enteros usan 32 bits y los `float` precisión simple. El heap no tiene GC.

## Estructura

```text
compiler/       Frontend, IR/TAC, backend MIPS, simulador, API y CLI
program/        Gramática, archivos ANTLR y programa del curso
examples/mips/  Seis programas ejecutables de esta fase
ide/            Editor web (parte 2)
tests/          Pruebas del frontend, MIPS e IDE (parte 2)
docs/           Arquitectura, requisitos y guías (parte 2)
scripts/        Generación del parser; inicio del IDE en la parte 2
```

El frontend se puede ejecutar de manera independiente:

```bash
python program/Driver.py program/program.cps --symbols
python program/Driver.py program/program.cps --ast-json out/ast.json
python program/Driver.py program/program.cps --syntax-only
python program/Driver.py --help
```

Para regenerar lexer, parser y visitor: `bash scripts/generate_parser.sh`.
La gramática conserva las extensiones del frontend anterior (`float`, `void`
y diagnóstico semántico de `const` sin inicializador); no se editan a mano
los archivos generados.

## Docker

```bash
docker build -t compiscript-fase3 .
docker run --rm -it -v "$(pwd)":/workspace compiscript-fase3
```

La imagen incluye Java, Python, Graphviz y SPIM. Con la parte 2 integrada:

```bash
docker run --rm -p 5001:5001 -e IDE_HOST=0.0.0.0 \
  -v "$(pwd)":/workspace compiscript-fase3 python ide/app.py
```

## Referencias del curso

- [Lenguaje Compiscript](https://github.com/gbrolo/compilers-2026/blob/main/compiscript/README.md)
- [Gramática ANTLR](https://github.com/gbrolo/compilers-2026/blob/main/compiscript/program/Compiscript.g4)
- [Requisitos de generación de código](https://github.com/gbrolo/compilers-2026/blob/main/compiscript/README_CODE_GENERATION.md)
