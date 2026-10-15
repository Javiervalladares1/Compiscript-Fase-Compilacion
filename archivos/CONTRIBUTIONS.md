# Contribuciones del equipo

> **Plantilla por completar.** Cada integrante debe rellenar su propia sección
> con datos reales. No se han precargado nombres, carnés, ramas ni commits.
>
> El curso valida los commits y contribuciones de cada integrante: **no se
> permite compartir commits**. Debe notarse claramente qué porción de código
> implementó cada persona, así que la separación de commits la realiza cada
> estudiante en su propia rama.

---

## Integrante 1

- **Nombre completo:**
- **Carné:**
- **Rama de trabajo:**
- **Componentes implementados:**
  <!-- Ej.: compiler/types/, compiler/symbols/ -->
- **Commits principales:**

  | Hash | Fecha | Descripción |
  | --- | --- | --- |
  |  |  |  |

- **Pruebas desarrolladas:**
  <!-- Ej.: tests/test_types.py, examples/valid/01_tipos_basicos.cps -->

---

## Integrante 2

- **Nombre completo:**
- **Carné:**
- **Rama de trabajo:**
- **Componentes implementados:**
- **Commits principales:**

  | Hash | Fecha | Descripción |
  | --- | --- | --- |
  |  |  |  |

- **Pruebas desarrolladas:**

---

## Integrante 3

- **Nombre completo:**
- **Carné:**
- **Rama de trabajo:**
- **Componentes implementados:**
- **Commits principales:**

  | Hash | Fecha | Descripción |
  | --- | --- | --- |
  |  |  |  |

- **Pruebas desarrolladas:**

---

## Mapa de componentes

Referencia para repartir el trabajo y documentar quién hizo qué. La columna
"Responsable" debe completarla el equipo.

| Componente | Archivos | Responsable |
| --- | --- | --- |
| Gramática y generación del parser | `program/Compiscript.g4`, `program/Compiscript.bnf`, `scripts/generate_parser.sh` | |
| Manejo de errores sintácticos | `compiler/parser/error_listener.py`, `compiler/parser/antlr_runtime.py` | |
| Nodos del AST | `compiler/ast/nodes.py` | |
| Constructor del AST | `compiler/ast/builder.py` | |
| Serialización y visualización del AST | `compiler/ast/serializer.py`, `compiler/ast/visualizer.py` | |
| Sistema de tipos | `compiler/types/types.py`, `compiler/types/compatibility.py` | |
| Símbolos y ámbitos | `compiler/symbols/symbols.py`, `compiler/symbols/scope.py` | |
| Tabla de símbolos y exportación | `compiler/symbols/table.py` | |
| Diagnósticos | `compiler/semantic/diagnostics.py` | |
| Pasadas de declaración | `compiler/semantic/declarations.py`, `compiler/semantic/type_resolver.py` | |
| Verificador de tipos y ámbitos | `compiler/semantic/type_checker.py` | |
| Análisis de flujo de control | `compiler/semantic/control_flow.py` | |
| Orquestador y API interna | `compiler/semantic/analyzer.py`, `compiler/pipeline.py`, `compiler/result.py` | |
| CLI | `compiler/cli.py`, `program/Driver.py` | |
| IDE — backend | `ide/app.py` | |
| IDE — frontend | `ide/templates/`, `ide/static/` | |
| Pruebas de tipos y operadores | `tests/test_types.py` | |
| Pruebas de ámbitos | `tests/test_scopes.py` | |
| Pruebas de funciones | `tests/test_functions.py` | |
| Pruebas de control de flujo | `tests/test_control_flow.py` | |
| Pruebas de clases | `tests/test_classes.py` | |
| Pruebas de arreglos | `tests/test_arrays.py` | |
| Pruebas de AST y símbolos | `tests/test_ast.py`, `tests/test_symbols.py` | |
| Pruebas de expresiones compuestas | `tests/test_expressions.py` | |
| Pruebas de CLI e IDE | `tests/test_cli.py`, `tests/test_ide.py` | |
| Programas `.cps` de prueba | `examples/` | |
| Documentación | `docs/`, `README.md` | |
| Docker y dependencias | `Dockerfile`, `requirements.txt` | |

---

## Cómo registrar las contribuciones

1. Cada integrante trabaja en su propia rama:

   ```bash
   git checkout -b nombre-apellido/componente
   ```

2. Commits pequeños y descriptivos, con el componente en el mensaje:

   ```bash
   git commit -m "types: agregar promocion de integer a float en is_assignable"
   ```

3. Al integrar, use *merge* (no *squash*) para conservar la autoría de cada
   commit.

4. Para obtener los datos de esta tabla:

   ```bash
   git log --author="Nombre" --oneline
   git shortlog -sne
   ```
