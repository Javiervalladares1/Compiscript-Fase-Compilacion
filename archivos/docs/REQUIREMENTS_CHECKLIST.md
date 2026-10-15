# Matriz de cumplimiento

Estado de cada requisito de `README_SEMANTIC_ANALYSIS.md` frente a la
implementación de este repositorio.

Un requisito solo se marca ✅ cuando **está implementado y cubierto por pruebas
que fallan si se rompe**. La columna «Tests» apunta al archivo y a la prueba
concreta que lo verifica.

**Resultado de la suite:** `407 passed` (`python3 -m pytest`).
Comprobado con ANTLR regenerado desde cero.

---

## 1. Sistema de tipos

| Requisito | Implementación | Tests | Estado |
| --- | --- | --- | --- |
| Aritmética `+`, `-`, `*`, `/` con operandos numéricos | `semantic/type_checker.py` (`_check_binary`), `types/compatibility.py` | `test_types.py::test_suma_de_enteros_produce_integer`, `::test_resta_con_string_es_invalida` | ✅ |
| Operador `%` (presente en la gramática, ausente de la lista oficial) | `type_checker.py` — `_ARITHMETIC_OPERATORS` | `test_types.py::test_modulo_requiere_numericos`, `::test_division_entera_produce_integer` | ✅ |
| Tipo `float` y promoción `integer` → `float` | `types/types.py`, `types/compatibility.py`; gramática ampliada (D1) | `test_types.py::test_promocion_de_integer_a_float`, `::test_float_no_se_degrada_a_integer` | ✅ |
| Concatenación con `+` cuando hay un `string` (D4) | `type_checker.py` — `_concatenation_type` | `test_types.py::test_concatenacion_string_mas_integer`, `::test_concatenacion_con_arreglo_es_invalida` | ✅ |
| Operaciones lógicas `&&`, `\|\|`, `!` con booleanos | `type_checker.py` — `_check_logical`, `_check_unary` | `test_types.py::test_operaciones_logicas_validas`, `::test_operacion_logica_con_entero_es_invalida` | ✅ |
| Comparaciones `==`, `!=`, `<`, `<=`, `>`, `>=` compatibles | `types/compatibility.py` — `comparable`, `orderable` | `test_types.py::test_comparacion_numerica_mixta_es_valida`, `::test_igualdad_entre_tipos_incompatibles` | ✅ |
| El resultado de una comparación es `boolean` | `type_checker.py` — `_check_comparison` | `test_types.py::test_comparacion_numerica_mixta_es_valida` | ✅ |
| Tipos en asignaciones (statement, `AssignExpr` y propiedades) | `type_checker.py` — `_check_assignment`, `_assignable_expression` | `test_types.py::test_asignacion_incompatible`, `test_expressions.py` (19 pruebas) | ✅ |
| Inicialización obligatoria de constantes | `semantic/declarations.py`; gramática ampliada (D3) | `test_types.py::test_constante_sin_inicializar` | ✅ |
| Constantes no reasignables | `symbols/symbols.py` (`mutable`), `type_checker.py` | `test_types.py::test_constante_no_se_reasigna` | ✅ |
| Inferencia de tipos (`let x = 10;`) | `type_checker.py` — `_declare_variable` | `test_types.py::test_inferencia_desde_el_inicializador` | ✅ |
| Tipos en listas (homogeneidad y arreglos vacíos) | `type_checker.py` — `_check_array_literal` (D9, D10) | `test_arrays.py` (29 pruebas) | ✅ |
| Tipo `null` y sus reglas (D8) | `types/types.py`, `types/compatibility.py` | `test_types.py::test_null_en_tipos_de_referencia`, `::test_null_no_es_asignable_a_valor` | ✅ |
| Ternario: condición booleana y ramas compatibles | `type_checker.py` — `_check_ternary` | `test_types.py::test_ternario_valido_con_tipo_comun`, `::test_ternario_con_ramas_incompatibles` | ✅ |

## 2. Manejo de ámbito

| Requisito | Implementación | Tests | Estado |
| --- | --- | --- | --- |
| Resolución de nombres local/global | `symbols/scope.py` — `resolve`, `resolve_with_scope` | `test_scopes.py::test_variable_global_visible_en_todo_el_programa` | ✅ |
| Error por variable no declarada | `type_checker.py` (SEM001/SEM009) | `test_scopes.py::test_variable_no_declarada`, `::test_asignacion_a_variable_no_declarada` | ✅ |
| Prohibir redeclaración en el mismo ámbito | `symbols/scope.py` — `declare` devuelve `False` (SEM004) | `test_scopes.py::test_redeclaracion_en_el_mismo_ambito_es_invalida` | ✅ |
| Acceso correcto en bloques anidados | `symbols/scope.py` (cadena de padres) | `test_scopes.py::test_variable_fuera_de_alcance_tras_el_bloque` | ✅ |
| Shadowing en ámbitos hijos (D16) | `symbols/scope.py` | `test_scopes.py::test_sombreado_valido_entre_ambitos` | ✅ |
| Nuevo entorno para función, clase y bloque | `symbols/table.py` — `push_scope`; `ScopeKind` con 8 clases de ámbito | `test_symbols.py::test_jerarquia_de_ambitos_con_padres_e_hijos` | ✅ |
| Ámbito propio para `for`, `foreach`, `switch`/`case`, `try`, `catch` | `semantic/type_checker.py` | `test_control_flow.py`, `test_scopes.py` | ✅ |
| `catch` no filtra su identificador (D13) | `type_checker.py` — ámbito `CATCH` | `test_scopes.py::test_identificador_de_catch_no_escapa` | ✅ |

## 3. Funciones y procedimientos

| Requisito | Implementación | Tests | Estado |
| --- | --- | --- | --- |
| Número de argumentos (coincidencia posicional) | `type_checker.py` — `_check_call` (SEM021) | `test_functions.py::test_numero_incorrecto_de_argumentos` | ✅ |
| Tipo de cada argumento | `type_checker.py` — `_check_call` (SEM022) | `test_functions.py::test_tipo_incorrecto_de_argumento` | ✅ |
| Tipo de retorno declarado | `type_checker.py` — `_check_return` (SEM023) | `test_functions.py::test_retorno_incompatible` | ✅ |
| Inferencia del tipo de retorno (D14) | `declarations.py` — `infer_return_type_placeholder` + tipo común | `test_functions.py::test_inferencia_de_retorno_sin_anotacion` | ✅ |
| `return` fuera de función (SEM024) | `type_checker.py` | `test_functions.py::test_return_fuera_de_funcion` | ✅ |
| Funciones recursivas | Símbolo registrado antes de analizar el cuerpo (`declarations.py`) | `test_functions.py::test_recursion_directa` | ✅ |
| Funciones anidadas | Ámbito de función dentro de función | `test_functions.py::test_funcion_anidada` | ✅ |
| Closures: captura del entorno léxico | `symbols/symbols.py` — `captures`/`captured`; resolución léxica | `test_functions.py::test_closure_registra_las_variables_capturadas`, `test_symbols.py` | ✅ |
| Funciones duplicadas (sin sobrecarga) | `declarations.py` (SEM004) | `test_functions.py::test_funcion_duplicada` | ✅ |
| Parámetros duplicados (SEM005) | `declarations.py` | `test_scopes.py::test_parametros_duplicados` | ✅ |
| Llamar a algo no invocable (SEM020) | `type_checker.py` | `test_functions.py::test_variable_no_es_invocable` | ✅ |
| Funciones `void` (D15) | `types/types.py`; `void` en la gramática | `test_functions.py::test_funcion_void_sin_retorno_es_valida`, `::test_uso_de_expresion_void_como_valor` | ✅ |

## 4. Control de flujo

| Requisito | Implementación | Tests | Estado |
| --- | --- | --- | --- |
| Condición booleana en `if` | `type_checker.py` — `_check_condition` (SEM017) | `test_control_flow.py::test_condicion_de_if_no_booleana` | ✅ |
| Condición booleana en `while` | idem | `test_control_flow.py::test_condicion_de_while_no_booleana` | ✅ |
| Condición booleana en `do-while` | idem | `test_control_flow.py::test_condicion_de_do_while_no_booleana` | ✅ |
| Condición booleana en `for` | idem | `test_control_flow.py::test_condicion_de_for_no_booleana` | ✅ |
| `switch`: selector comparable, no booleano (D6) | `type_checker.py` — `_check_switch` (SEM043/044/045) | `test_control_flow.py::test_switch_con_selector_entero`, `::test_case_incompatible_con_el_selector`, `::test_selector_no_comparable` | ⚠️ Desviación documentada (D6) |
| `foreach` sobre iterables e inferencia del elemento | `type_checker.py` — `_check_foreach` (SEM029) | `test_control_flow.py::test_foreach_infiere_el_tipo_del_elemento` | ✅ |
| `break` solo en bucles (+ `switch`, D7) | `symbols/scope.py` — `is_inside_breakable` (SEM027) | `test_control_flow.py::test_break_fuera_de_bucle`, `::test_break_dentro_de_switch_es_valido` | ⚠️ Extensión documentada (D7) |
| `continue` solo en bucles | `symbols/scope.py` — `is_inside_loop` (SEM028) | `test_control_flow.py::test_continue_fuera_de_bucle`, `::test_continue_dentro_de_switch_sin_bucle_es_invalido` | ✅ |
| `try`/`catch` con ámbitos correctos | `type_checker.py` | `test_control_flow.py::test_try_catch_valido` | ✅ |

## 5. Clases y objetos

| Requisito | Implementación | Tests | Estado |
| --- | --- | --- | --- |
| Existencia de atributos por `.` (SEM034) | `symbols/table.py` — `ClassRegistry.lookup_field` | `test_classes.py::test_acceso_a_atributo_inexistente` | ✅ |
| Existencia de métodos por `.` (SEM035) | `ClassRegistry.lookup_method` | `test_classes.py::test_llamada_a_metodo_inexistente` | ✅ |
| Propiedad sobre un no-objeto (SEM036) | `type_checker.py` | `test_classes.py::test_acceso_a_propiedad_sobre_no_objeto` | ✅ |
| Llamada correcta al constructor (SEM042/021/022) | `ClassRegistry.lookup_constructor` (D12) | `test_classes.py::test_constructor_con_numero_incorrecto_de_argumentos` | ✅ |
| `new` sobre algo que no es clase (SEM038) | `type_checker.py` | `test_classes.py::test_new_sobre_algo_que_no_es_clase` | ✅ |
| El tipo de `new C(...)` es `C` | `type_checker.py` | `test_classes.py::test_instanciacion_valida` | ✅ |
| `this` solo dentro de clase (SEM037) | `type_checker.py` — contexto de clase | `test_classes.py::test_this_fuera_de_una_clase` | ✅ |
| `this.x` resuelve atributos de la clase actual | `type_checker.py` | `test_classes.py::test_this_valido_dentro_de_un_metodo` | ✅ |
| Herencia: clase padre existente (SEM039) | `declarations.py` — `resolve_inheritance` | `test_classes.py::test_clase_base_inexistente` | ✅ |
| Herencia circular (SEM040) | `declarations.py` — `_has_cycle` | `test_classes.py::test_ciclo_de_herencia` | ✅ |
| Atributos y métodos heredados | `ClassRegistry.ancestors` | `test_classes.py::test_acceso_a_miembro_heredado`, `::test_uso_de_this_con_atributo_heredado` | ✅ |
| Sobrescritura con firma incompatible (SEM041) | `declarations.py` | `test_classes.py::test_sobrescritura_con_tipo_de_retorno_incompatible` | ✅ |
| Miembros duplicados en una clase (SEM006) | `declarations.py` — `collect_class_members` | `test_classes.py::test_miembros_duplicados` | ✅ |

## 6. Listas y estructuras de datos

| Requisito | Implementación | Tests | Estado |
| --- | --- | --- | --- |
| Tipo de los elementos (homogeneidad, SEM032) | `type_checker.py` — `_check_array_literal` | `test_arrays.py::test_arreglo_heterogeneo` | ✅ |
| Arreglos multidimensionales | `types/types.py` — `ArrayType` anidado | `test_arrays.py::test_matriz` | ✅ |
| Arreglos vacíos y tipado contextual (D9, D10) | `type_checker.py` | `test_arrays.py::test_arreglo_vacio_con_contexto`, `::test_arreglo_vacio_sin_contexto` | ✅ |
| Índice de tipo `integer` (SEM030) | `type_checker.py` — `_check_index` | `test_arrays.py::test_indice_no_entero` | ✅ |
| Indexar algo no indexable (SEM031) | `type_checker.py` | `test_arrays.py::test_acceso_a_valor_no_indexable` | ✅ |
| Tipo del elemento resultante | `types/types.py` — `ArrayType.element` | `test_arrays.py::test_indice_entero` | ✅ |
| Índice literal fuera de rango — **advertencia** (D11) | `type_checker.py` (SEM-W005) | `test_arrays.py::test_indice_literal_fuera_de_rango_es_advertencia` | ⚠️ Advertencia, no error (D11) |

## 7. Generales

| Requisito | Implementación | Tests | Estado |
| --- | --- | --- | --- |
| Código muerto tras `return` (SEM-W001) | `semantic/control_flow.py` | `test_control_flow.py::test_codigo_muerto_tras_return` | ✅ (advertencia) |
| Código muerto tras `break` (SEM-W002) | `semantic/control_flow.py` | `test_control_flow.py::test_codigo_muerto_tras_break` | ✅ (advertencia) |
| Código muerto tras `continue` (SEM-W003) | `semantic/control_flow.py` | `test_control_flow.py` | ✅ (advertencia) |
| Expresiones sin sentido semántico | Sistema de tipos completo (`types/compatibility.py`) | `test_types.py`, `test_expressions.py` | ✅ |
| Declaraciones duplicadas (variables, parámetros, miembros) | SEM004 / SEM005 / SEM006 | `test_scopes.py`, `test_functions.py`, `test_classes.py` | ✅ |
| Acceso encadenado `foo().bar[0].baz()` | `type_checker.py` — propagación por sufijos | `test_expressions.py` (9 pruebas de cadenas) | ✅ |
| Uso antes de inicializar (SEM046) | `type_checker.py` | `test_scopes.py::test_uso_de_variable_declarada_sin_inicializar` | ✅ |

## 8. Infraestructura y entregables

| Requisito | Implementación | Tests | Estado |
| --- | --- | --- | --- |
| Parser con ANTLR regenerable | `program/Compiscript.g4`, `scripts/generate_parser.sh` | Verificado: regeneración desde cero + suite completa | ✅ |
| Errores sintácticos detectados y con ubicación | `parser/error_listener.py` | `test_cli.py::test_error_sintactico_con_ubicacion` | ✅ |
| AST propio (no el parse tree de ANTLR) | `ast/nodes.py` (45+ nodos), `ast/builder.py` (Visitor) | `test_ast.py` (28 pruebas) | ✅ |
| Cada nodo conserva línea, columna y span | `ast/nodes.py` — `SourceSpan` | `test_ast.py::test_todos_los_nodos_tienen_ubicacion` | ✅ |
| Recorrido con **Visitor** | `ast/builder.py` extiende `CompiscriptVisitor` | `test_ast.py` | ✅ |
| Representación visual del AST (DOT) | `ast/visualizer.py` — `write_dot` | `test_ast.py::test_escritura_del_archivo_dot` | ✅ |
| Imagen PNG/SVG del AST | `ast/visualizer.py` — `render_image` | `test_ast.py::test_dot_generado_es_valido_para_graphviz` | ✅ |
| AST como árbol de texto | `ast/nodes.py` — `Node.to_tree` | `test_ast.py::test_to_tree_usa_conectores_y_ubicaciones` | ✅ |
| Tabla de símbolos jerárquica | `symbols/table.py`, `symbols/scope.py`, `symbols/symbols.py` | `test_symbols.py` (25 pruebas) | ✅ |
| Símbolos con nombre, categoría, tipo, ámbito, mutabilidad, ubicación | `symbols/symbols.py` (8 categorías) | `test_symbols.py::test_simbolo_de_variable` | ✅ |
| Tabla de símbolos visible (árbol de ámbitos) | `symbols/table.py` — `to_tree`, `to_text`, `to_dict` | `test_symbols.py::test_to_tree_anida_los_parametros_dentro_de_su_funcion` | ✅ |
| Sistema centralizado de errores con línea y columna | `semantic/diagnostics.py` — `Diagnostic`, `DiagnosticBag`, 55 códigos | `test_cli.py::test_los_diagnosticos_incluyen_linea_y_columna` | ✅ |
| El análisis no se detiene en el primer error | `DiagnosticBag` acumula; `ErrorType` evita cascadas | `test_cli.py::test_el_analisis_no_se_detiene_en_el_primer_error` | ✅ |
| Driver con `--ast`, `--symbols` y combinados | `compiler/cli.py`, `program/Driver.py` | `test_cli.py::test_cli_ast_y_symbols_combinados` (+7 más) | ✅ |
| IDE funcional que usa el mismo pipeline | `ide/app.py` (Flask) → `compiler.compile_source` | `test_ide.py` (14 pruebas) | ✅ |
| IDE muestra errores, AST y tabla de símbolos | `ide/templates/index.html`, `ide/static/app.js` | `test_ide.py`; verificado en navegador | ✅ |
| Batería de tests positivos y negativos por regla | `tests/` (12 archivos, 407 pruebas) | `python3 -m pytest` | ✅ |
| Programas `.cps` de ejemplo válidos e inválidos | `examples/valid/` (9), `examples/invalid/` (15) | `test_programs.py` (76 pruebas parametrizadas) | ✅ |
| Documentación de arquitectura | `docs/architecture.md` | — | ✅ |
| Documentación de ejecución | `README.md` (comandos verificados) | — | ✅ |
| Documentación de decisiones e inconsistencias | `docs/semantic-decisions.md` (18 decisiones) | — | ✅ |
| Docker conserva el flujo original | `Dockerfile`, `commands/antlr` | Verificado: build + tests dentro del contenedor | ✅ |
| BNF sincronizada con la gramática | `program/Compiscript.bnf` | Revisión manual (§55) | ✅ |

---

## Desviaciones deliberadas

Tres puntos NO siguen la letra literal del requisito. Los tres están razonados
en `docs/semantic-decisions.md`, tienen pruebas propias y son reversibles:

| # | Requisito literal | Comportamiento implementado | Motivo | Reversión |
| --- | --- | --- | --- | --- |
| D6 | «Las condiciones en `if`, `while`, `do-while`, `for`, **`switch`** deben evaluar expresiones de tipo `boolean`» | El selector de `switch` debe ser **comparable** (`integer`, `float`, `string`, `boolean`), no booleano | El README oficial y `program.cps` usan `switch (x)` con un entero; exigir un booleano haría inútil la construcción | Cambiar `_check_switch` para exigir `boolean` |
| D7 | «`break` y `continue` sólo dentro de bucles» | `break` se permite también dentro de `switch`; `continue` sigue siendo exclusivo de bucles | El README presenta `switch` con la forma habitual de C/TypeScript | Quitar `ScopeKind.SWITCH` de `BREAKABLE_SCOPES` (una línea) |
| D11 | «Validación de índices (acceso válido a listas)» | Índice literal fuera de rango es **advertencia**, no error | `program.cps` del curso contiene deliberadamente `numbers[10]` dentro de un `try`; como error, el ejemplo oficial no compilaría | Usar `--strict`, que ya convierte la advertencia en error |

## Inconsistencias entre fuentes oficiales

Detectadas al contrastar `README.md`, `README_SEMANTIC_ANALYSIS.md`,
`Compiscript.g4` y `Compiscript.bnf`. El detalle completo y la resolución de
cada una están en `docs/semantic-decisions.md`.

| # | Inconsistencia | Resolución |
| --- | --- | --- |
| 1 | Los requisitos exigen `float`, pero la gramática solo tiene `boolean \| integer \| string` y `IntegerLiteral` | Se añadieron `float`, `FloatLiteral` y `void` a la gramática (D1, D15) |
| 2 | Los requisitos piden validar «const sin inicializador» pero la gramática lo hace imposible (error de sintaxis) | Inicializador opcional en la gramática; el error pasa a ser semántico SEM007 (D3) |
| 3 | Los requisitos limitan `+` a operandos numéricos, pero el README usa `"Hola " + nombre` | `+` sobrecargado: concatenación si algún operando es `string` (D4) |
| 4 | El requisito pide selector booleano en `switch`; el README lo usa con enteros | Regla de comparabilidad (D6) |
| 5 | El requisito limita `break` a bucles; el README lo usa en `switch` | `break` permitido en `switch` (D7) |
| 6 | La gramática incluye `%`, ausente de la lista oficial de operadores aritméticos | Implementado con las mismas reglas que `*` y `/` |
| 7 | La gramática permite ternarios, asignaciones como expresión y cadenas de sufijos, no mencionados en los requisitos | Implementados y probados (`test_expressions.py`) |
| 8 | El tipo del identificador de `catch` no está definido en ninguna fuente | Se tipa como `string` (D13) |
| 9 | El tipo de `integer / integer` no está especificado | División entera (D5) |
| 10 | El README no define si `null` es asignable a `string` | `string` se considera tipo de referencia y admite `null` (D8) |
