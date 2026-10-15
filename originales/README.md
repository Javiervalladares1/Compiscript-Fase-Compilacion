# 🧪 Compiscript — Análisis Semántico

Frontend completo para el lenguaje **Compiscript**: análisis léxico, análisis
sintáctico con ANTLR, AST propio, tabla de símbolos con ámbitos anidados,
sistema de tipos, analizador semántico, visualización del AST e IDE web.

---

## Inicio rápido

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./scripts/generate_parser.sh
cd program && python3 Driver.py program.cps
```

Salida esperada:

```text
aviso: program.cps:58:32 [SEM-W005] El indice 10 esta fuera del rango del arreglo (tamano 5); la comprobacion definitiva ocurre en tiempo de ejecucion.
Compilacion exitosa: program.cps (1 advertencia(s))
```

Para abrir el IDE:

```bash
python3 ide/app.py
```

y visitar <http://127.0.0.1:5000>.

> En macOS el puerto 5000 lo ocupa «AirPlay Receiver». Use otro puerto:
> `python3 ide/app.py --port 5050`.

---

## Requisitos

| Herramienta | Versión | Necesaria para |
| --- | --- | --- |
| Python | 3.10 o superior | Todo |
| Java | 11 o superior | Regenerar el parser con ANTLR |
| Graphviz (`dot`) | cualquiera | **Opcional**: convertir el AST a PNG/SVG |

Dependencias de Python (`requirements.txt`):

- `antlr4-python3-runtime==4.13.1` — debe coincidir con el JAR
  `antlr-4.13.1-complete.jar` incluido en el repositorio.
- `pytest>=8` — batería de pruebas.
- `Flask>=3` — IDE web (el compilador funciona sin él).

---

## Generar el lexer y el parser

```bash
./scripts/generate_parser.sh
```

El script se ejecuta **desde cualquier ubicación** y equivale a lanzar, dentro
de `program/`:

```bash
antlr -Dlanguage=Python3 -visitor Compiscript.g4
```

Usa el comando `antlr` si existe (es el caso dentro del contenedor Docker) y en
caso contrario el JAR incluido en la raíz. Además comprueba que la versión del
generador coincida con la fijada en `requirements.txt`.

Genera en `program/`: `CompiscriptLexer.py`, `CompiscriptParser.py`,
`CompiscriptVisitor.py`, `CompiscriptListener.py`, `*.interp` y `*.tokens`.

> ⚠️ **Estos archivos no se editan a mano.** Toda la lógica propia vive en
> `compiler/`. Tras modificar `Compiscript.g4` hay que volver a ejecutar el
> script.

---

## Usar el compilador

```bash
cd program
python3 Driver.py program.cps
```

### Opciones

| Comando | Efecto |
| --- | --- |
| `python3 Driver.py program.cps` | Analiza e imprime los diagnósticos |
| `python3 Driver.py program.cps --ast` | Imprime el AST y escribe `ast.dot` |
| `python3 Driver.py program.cps --symbols` | Imprime el árbol de la tabla de símbolos |
| `python3 Driver.py program.cps --ast --symbols` | Ambas cosas a la vez |
| `python3 Driver.py program.cps --ast ast.dot` | Exporta el AST en Graphviz DOT a la ruta indicada |
| `python3 Driver.py program.cps --ast-json ast.json` | Exporta el AST como JSON jerárquico |
| `python3 Driver.py program.cps --ast-image ast.png` | Renderiza el AST (requiere Graphviz) |
| `python3 Driver.py program.cps --symbols symbols.json` | Exporta la tabla de símbolos a JSON |
| `python3 Driver.py program.cps --symbols-text` | Imprime la tabla en formato tabular |
| `python3 Driver.py program.cps --diagnostics json` | Diagnósticos en JSON |
| `python3 Driver.py program.cps --strict` | Trata las advertencias como errores |
| `python3 Driver.py program.cps --syntax-only` | Solo análisis léxico y sintáctico |
| `python3 Driver.py program.cps --quiet` | Omite el mensaje de éxito |

**Códigos de salida:** `0` sin errores · `1` con errores (o advertencias en
`--strict`) · `2` si el archivo no existe.

### Formato de los diagnósticos

```text
program.cps:4:8  [SEM001] Identificador no declarado: 'total'.
program.cps:9:14 [SEM012] Asignacion incompatible en 'x': se esperaba 'integer' y se recibio 'string'.
program.cps:15:5 [SEM024] 'return' solo puede utilizarse dentro de una funcion o metodo.
```

Todos incluyen archivo, línea y columna (1-based), un código estable y —cuando
aplica— el tipo esperado y el recibido. El análisis nunca se detiene en el
primer error y los diagnósticos se ordenan por ubicación.

---

## IDE

```bash
python3 ide/app.py
# http://127.0.0.1:5000
```

El puerto y la interfaz son configurables (útil en macOS, donde «AirPlay
Receiver» ocupa el 5000):

```bash
python3 ide/app.py --port 5050
```

También se aceptan las variables de entorno `IDE_PORT`, `PORT` e `IDE_HOST`.

Incluye:

- Editor con numeración de líneas y marcado de las que tienen error.
- Botón **Compilar** (o `Ctrl`/`Cmd` + `Enter`) y **Cargar ejemplo**.
- Indicador de compilación exitosa o fallida.
- Panel de **diagnósticos** con línea, columna, código y tipos; al hacer clic
  el cursor salta a la posición del error.
- Panel del **AST** como árbol plegable con el tipo resuelto de cada nodo.
- Panel de la **tabla de símbolos** con ámbito, categoría, tipo y detalles.
- Interruptor de **modo estricto**.

El IDE es una capa delgada sobre `compile_source()`: no contiene lógica
semántica, no lee rutas del disco indicadas por el usuario y no ejecuta
comandos. El compilador funciona sin iniciar el IDE.

---

## Pruebas

```bash
python3 -m pytest
```

407 pruebas: unitarias por regla semántica más 24 programas `.cps` completos
(`examples/`) y el `program.cps` del curso. Detalles en [docs/testing.md](docs/testing.md).

---

## API interna

CLI e IDE usan la misma función:

```python
from compiler import compile_source, CompileOptions

result = compile_source(codigo, filename="<editor>", options=CompileOptions(strict=False))

result.success          # bool
result.diagnostics      # list[Diagnostic]  (sintácticos + semánticos, ordenados)
result.ast              # Program | None
result.symbol_table     # SymbolTable | None
result.error_count      # int
result.warning_count    # int
result.exit_code        # 0 | 1
result.to_dict()        # estructura JSON-serializable para el IDE
```

También está disponible `compile_file(path, options)`.

---

## Estructura del proyecto

```text
.
├── program/            Gramática, archivos generados por ANTLR, Driver y program.cps
├── compiler/           Frontend: parser, ast, types, symbols, semantic, pipeline, cli
├── ide/                IDE web (Flask + HTML/CSS/JS sin dependencias externas)
├── tests/              Batería de pruebas (12 archivos, 407 pruebas)
├── examples/           Programas .cps de ejemplo: valid/ (9) e invalid/ (15)
├── scripts/            generate_parser.sh
├── docs/               Documentación
├── Dockerfile          Entorno reproducible con Java, Python y ANTLR
└── requirements.txt    Dependencias fijadas
```

---

## Docker

```bash
docker build --rm . -t csp-image
docker run --rm -ti -p 5000:5000 -v "$(pwd)":/workspace csp-image
```

Dentro del contenedor:

```bash
./scripts/generate_parser.sh
cd program && python3 Driver.py program.cps
python3 -m pytest
IDE_HOST=0.0.0.0 python3 ide/app.py     # accesible en http://localhost:5000
```

---

## Características del lenguaje soportadas

| Categoría | Elementos |
| --- | --- |
| Tipos | `integer`, `float`, `string`, `boolean`, `void`, `null`, arreglos multidimensionales, clases |
| Declaraciones | `let`, `var`, `const`, funciones, funciones anidadas, clases, herencia |
| Expresiones | Literales, aritmética, lógica, comparaciones, ternario, llamadas, `new`, `this`, acceso a propiedad, indexación, asignación como expresión |
| Control de flujo | `if`/`else`, `while`, `do-while`, `for`, `foreach`, `switch`/`case`/`default`, `try`/`catch`, `break`, `continue`, `return` |
| Análisis | Ámbitos anidados, sombreado, closures con captura registrada, recursión directa y mutua, herencia y constructor heredado, código muerto |

`float`, `void` y el inicializador opcional de `const` son extensiones sobre la
gramática original del curso; el motivo de cada una está en
[docs/semantic-decisions.md](docs/semantic-decisions.md).

---

## Documentación

| Documento | Contenido |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | Flujo de compilación, módulos, pasadas, tabla de símbolos, sistema de tipos e IDE (con diagramas Mermaid) |
| [docs/semantic-rules.md](docs/semantic-rules.md) | Todas las reglas semánticas con tablas de compatibilidad y el catálogo de códigos |
| [docs/semantic-decisions.md](docs/semantic-decisions.md) | Inconsistencias entre gramática, README y requisitos, y la decisión tomada en cada caso |
| [docs/testing.md](docs/testing.md) | Cómo ejecutar y ampliar las pruebas |
| [CONTRIBUTIONS.md](CONTRIBUTIONS.md) | Plantilla de contribuciones del equipo |
| [docs/REQUIREMENTS_CHECKLIST.md](docs/REQUIREMENTS_CHECKLIST.md) | Matriz de cumplimiento de los requisitos |
| [docs/README_SEMANTIC_ANALYSIS.md](docs/README_SEMANTIC_ANALYSIS.md) | Enunciado original de la fase |
| [docs/README_DOCKER.md](docs/README_DOCKER.md) | Guía de instalación de Docker |
