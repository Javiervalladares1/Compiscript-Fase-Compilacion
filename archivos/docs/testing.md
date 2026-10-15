# Pruebas

## Ejecutar la batería completa

Un solo comando ejecuta todas las pruebas:

```bash
python3 -m pytest
```

Variantes útiles:

```bash
python3 -m pytest -v                        # detalle por prueba
python3 -m pytest tests/test_classes.py     # un solo módulo
python3 -m pytest -k closure                # por nombre
python3 -m pytest tests/test_programs.py -v # solo los programas .cps completos
```

La configuración vive en `pytest.ini`: fija `testpaths = tests` y añade la raíz
del repositorio a `pythonpath`, de modo que no hace falta instalar nada ni
exportar `PYTHONPATH`.

> Requisito previo: el lexer/parser debe estar generado. Si el repositorio se
> acaba de clonar y `program/CompiscriptParser.py` no existe, ejecute primero
> `./scripts/generate_parser.sh`.

---

## Organización

```text
tests/
├── conftest.py            # utilidades compartidas (assert_ok, assert_error, …)
├── test_types.py          # sistema de tipos, operadores, null, ternario
├── test_scopes.py         # ámbitos, sombreado, redeclaración, visibilidad
├── test_functions.py      # firmas, llamadas, retornos, recursión, closures
├── test_control_flow.py   # condiciones, bucles, switch, break/continue, código muerto
├── test_classes.py        # clases, miembros, constructores, this, herencia
├── test_arrays.py         # homogeneidad, dimensiones, índices, asignaciones
├── test_ast.py            # construcción, ubicaciones, serialización, DOT
├── test_symbols.py        # jerarquía de ámbitos, contenido y exportación
├── test_cli.py            # API compile_source, diagnósticos y CLI
├── test_ide.py            # endpoints del IDE y contrato JSON
├── test_expressions.py    # acceso encadenado y asignaciones como expresión
└── test_programs.py       # programas .cps completos + program/program.cps

examples/
├── valid/                 # 9 programas que deben compilar sin errores
└── invalid/               # 15 programas con errores esperados
```

### Dos niveles de prueba

1. **Unitarias por regla** (`test_types.py`, `test_scopes.py`, …): fragmentos
   pequeños compilados en memoria, uno por regla semántica, con su caso exitoso
   y su caso fallido.
2. **Programas completos** (`examples/`): archivos `.cps` reales, uno por
   categoría, que se compilan de principio a fin. Evitan que las reglas
   funcionen aisladas pero fallen al combinarse.

---

## Qué cubre cada grupo

| Módulo | Reglas cubiertas |
| --- | --- |
| `test_types.py` | Aritmética, `float` y promoción, concatenación, lógica, relacionales, igualdad, asignaciones, constantes, ternario, `null`, y la API de `compatibility.py` |
| `test_scopes.py` | Global/local, bloques anidados, sombreado válido, redeclaración, no declarados, parámetros duplicados, ámbitos de `catch` y `foreach`, jerarquía de ámbitos |
| `test_functions.py` | Aridad y tipos de argumentos, retornos, `return` fuera de función, caminos sin retorno, `void`, inferencia de retorno, duplicados, recursión directa y mutua, anidamiento y closures |
| `test_control_flow.py` | Condiciones booleanas de `if`/`while`/`do-while`/`for`, `foreach` iterable, `break`/`continue`, `switch` (compatibilidad, duplicados, selector), `try`/`catch`, código muerto y modo estricto |
| `test_classes.py` | Declaración e instanciación, constructor (propio y heredado), atributos y métodos, `this`, herencia, ciclos, sobrescritura y asignabilidad entre clases |
| `test_arrays.py` | Homogeneidad, arreglo vacío con y sin contexto, matrices, índices, encadenamiento, rango estático, asignación a posiciones e invariancia |
| `test_ast.py` | Independencia de ANTLR, ubicaciones, cobertura de todos los tipos de nodo, precedencia y asociatividad, tipos resueltos, JSON y DOT |
| `test_symbols.py` | Jerarquía padre/hijo, nombres calificados, contenido de cada categoría de símbolo, capturas, herencia, exportación JSON y tabular |
| `test_cli.py` | `compile_source`/`compile_file`, fases de diagnóstico, orden y no duplicación, errores léxicos y sintácticos, todas las opciones del CLI y códigos de salida |
| `test_ide.py` | `/`, `/api/example`, `/api/compile`, contrato JSON, modo estricto y límites de seguridad |
| `test_expressions.py` | Cadenas de `()`, `[]` y `.`; asignaciones encadenadas, mutabilidad del destino y asignación de propiedades |
| `test_programs.py` | Los 24 programas `.cps` de `examples/` y `program/program.cps` |

---

## Programas `.cps` de prueba

### Válidos — `examples/valid/`

Deben compilar **sin errores y sin advertencias** (se verifican también con
`--strict`).

| Archivo | Qué demuestra |
| --- | --- |
| `01_tipos_basicos.cps` | Todos los tipos, promoción y concatenación |
| `02_ternario_y_null.cps` | Ternario con tipo común y `null` en referencias |
| `03_ambitos_y_bloques.cps` | Sombreado en bloques anidados y acceso a globales |
| `04_funciones_y_recursion.cps` | Recursión directa y mutua, inferencia, `void` |
| `05_closures.cps` | Funciones anidadas que capturan su entorno |
| `06_control_de_flujo.cps` | Todas las estructuras de control |
| `07_clases_y_herencia.cps` | Constructor heredado, sobrescritura, miembros heredados |
| `08_arreglos_y_matrices.cps` | Matrices, arreglo vacío con contexto, indexación |
| `09_demo_integral.cps` | Demostración integral: recorre todas las familias de reglas en un solo archivo |

### Inválidos — `examples/invalid/`

Cada archivo declara en su **primera línea** los códigos que debe producir, en
orden de aparición:

```cps
// @expect SEM012 SEM012 SEM012
// Asignaciones cuyo tipo no coincide con el declarado.
let contador: integer = "diez";
```

La prueba compara la lista completa de códigos obtenidos con la esperada, así
que también detecta **diagnósticos de más** (cascadas indeseadas).

| Archivo | Códigos esperados |
| --- | --- |
| `01_tipos_incompatibles.cps` | `SEM012` ×3 |
| `02_operaciones_invalidas.cps` | `SEM013` ×2, `SEM014` ×2, `SEM015`, `SEM016` |
| `03_constantes.cps` | `SEM007`, `SEM008` |
| `04_ternario_incompatible.cps` | `SEM017`, `SEM018` |
| `05_ambitos.cps` | `SEM001`, `SEM004`, `SEM009`, `SEM001` |
| `06_funciones.cps` | `SEM005`, `SEM004`, `SEM021`, `SEM022`, `SEM002`, `SEM020` |
| `07_retornos.cps` | `SEM024`, `SEM023`, `SEM025`, `SEM026` |
| `08_control_de_flujo.cps` | `SEM017` ×4, `SEM027`, `SEM028`, `SEM029` |
| `09_codigo_muerto.cps` | `SEM-W001`, `SEM-W002`, `SEM-W003` |
| `10_clases.cps` | `SEM006`, `SEM039`, `SEM041`, `SEM034`, `SEM035`, `SEM037`, `SEM003` |
| `11_arreglos.cps` | `SEM032`, `SEM030`, `SEM031`, `SEM012`, `SEM033` |
| `12_switch.cps` | `SEM043`, `SEM044`, `SEM045` |
| `13_inicializacion.cps` | `SEM046`, `SEM010`, `SEM011` |
| `14_sintaxis.cps` | `SYN001` |
| `15_errores_multiples.cps` | `SEM004`, `SEM008`, `SEM013`, `SEM001`, `SEM017`, `SEM021`, `SEM022`, `SEM023`, `SEM034`, `SEM037`, `SEM027`, `SEM030` |

---

## Cómo agregar casos

### Una prueba unitaria

Use los ayudantes de `tests/conftest.py`:

```python
from conftest import assert_error, assert_ok
from compiler.semantic.diagnostics import Code

def test_mi_regla_valida():
    assert_ok("let x: float = 1;")

def test_mi_regla_invalida():
    assert_error("let x: integer = 1.5;", Code.INCOMPATIBLE_ASSIGNMENT)
```

| Ayudante | Uso |
| --- | --- |
| `assert_ok(src)` | El código compila sin errores |
| `assert_error(src, *codigos)` | Falla y aparecen esos códigos |
| `assert_no_code(src, *codigos)` | Esos códigos **no** aparecen |
| `compile_code(src, strict=False)` | Devuelve el `CompilationResult` completo |
| `codes(result)` | Lista de códigos del resultado |

**Verifique siempre por código, no por el texto del mensaje**: los mensajes
pueden reformularse; los códigos son estables.

### Un programa `.cps`

1. Cree el archivo en `examples/valid/` o `examples/invalid/` con un
   nombre descriptivo (`NN_tema.cps`).
2. Si es inválido, añada la primera línea `// @expect COD1 COD2 …` con los
   códigos **en orden de línea/columna**. Para conocerlos:

   ```bash
   python3 program/Driver.py examples/invalid/mi_caso.cps
   ```

3. No hace falta registrar nada más: `test_programs.py` descubre los archivos
   automáticamente con `parametrize`.
4. Un programa por categoría; no concentre casos no relacionados en un archivo.

---

## Verificación manual complementaria

```bash
# Programa de ejemplo del curso
cd program && python3 Driver.py program.cps

# Diagnósticos en JSON (lo que consume el IDE)
python3 program/Driver.py examples/invalid/06_funciones.cps --diagnostics json

# AST y tabla de símbolos
python3 program/Driver.py program/program.cps --ast out/ast.dot --symbols out/symbols.json

# Modo estricto
python3 program/Driver.py examples/invalid/09_codigo_muerto.cps --strict
```
