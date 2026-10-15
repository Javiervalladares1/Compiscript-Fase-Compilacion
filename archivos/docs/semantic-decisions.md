# Decisiones semánticas e inconsistencias detectadas

Este documento registra las contradicciones encontradas entre la gramática
(`program/Compiscript.g4`), el README del lenguaje, los requisitos de la fase
(`docs/README_SEMANTIC_ANALYSIS.md`) y el programa de ejemplo
(`program/program.cps`), junto con la decisión tomada en cada caso.

No se oculta ninguna contradicción: cuando una fuente dice una cosa y otra dice
lo contrario, se indica explícitamente cuál se siguió y por qué.

---

## D1. El tipo `float` no existía en la gramática

**Inconsistencia.** Los requisitos piden verificar operaciones aritméticas cuyos
operandos sean *"de tipo `integer` o `float`"*, pero la gramática original solo
declara `baseType: 'boolean' | 'integer' | 'string' | Identifier` y el único
literal numérico es `IntegerLiteral: [0-9]+`. El README del lenguaje tampoco
menciona `float`.

**Decisión: añadir soporte real para `float`.** Se prefirió cumplir el requisito
explícito antes que la omisión de la gramática.

Cambios en `program/Compiscript.g4`:

```antlr
baseType: 'boolean' | 'integer' | 'float' | 'string' | 'void' | Identifier;

Literal
  : FloatLiteral      // primero, para que '10.5' sea un solo token
  | IntegerLiteral
  | StringLiteral
  ;

FloatLiteral: [0-9]+ '.' [0-9]+;
IntegerLiteral: [0-9]+;
```

**Sobre el lexado de `10.5`.** `FloatLiteral` se declara antes que
`IntegerLiteral` dentro de la regla compuesta `Literal`. ANTLR aplica la regla
de coincidencia más larga, así que `10.5` produce un único token `Literal` de
5 caracteres y nunca la secuencia `10` `.` `5`. Está verificado en
`tests/test_types.py::test_float_literal_no_se_lexa_como_dos_tokens`.

**Semántica adoptada:**

- `integer` se promueve a `float` en asignaciones, argumentos, retornos,
  operaciones y elementos de arreglo.
- `float` **no** se degrada a `integer`: `let x: integer = 1.5;` es `SEM012`.
- Una operación aritmética con al menos un `float` produce `float`.

**Impacto en la compatibilidad.** `float` y `void` pasan a ser palabras
reservadas y no pueden usarse como identificadores. Ningún programa del
repositorio los usaba como nombres.

---

## D2. `Literal` es un token compuesto

**Situación.** La gramática agrupa los tres literales bajo un único token
(`Literal: FloatLiteral | IntegerLiteral | StringLiteral`). En ANTLR, las reglas
referenciadas por otra regla léxica quedan absorbidas: el parser solo ve
`Literal`, nunca `IntegerLiteral` ni `StringLiteral`.

**Decisión: conservar la estructura original y distinguir la variante por el
texto del token**, en una única función acotada
(`ASTBuilder._literal_from_text`):

- empieza por `"` → `StringLiteral`;
- contiene `.` → `FloatLiteral`;
- en otro caso → `IntegerLiteral`.

Se descartó dividir `Literal` en tres tokens del parser porque habría cambiado
la gramática más de lo necesario y roto la correspondencia con
`Compiscript.bnf`. El AST sí produce tres nodos distintos, así que el resto del
compilador nunca vuelve a inspeccionar texto.

---

## D3. `const x: integer;` era un error de sintaxis, no semántico

**Inconsistencia.** Los requisitos exigen validar la *"inicialización
obligatoria de constantes (`const`) en su declaración"* y listan
`const value: integer;` como ejemplo de código inválido que el **analizador
semántico** debe rechazar. Pero la gramática original obliga al inicializador:

```antlr
constantDeclaration: 'const' Identifier typeAnnotation? '=' expression ';';
```

Con esa regla, `const value: integer;` nunca llega al analizador semántico: el
parser aborta con un error de sintaxis genérico y la regla semántica pedida
sería inalcanzable.

**Decisión: hacer opcional el inicializador en la gramática y reportar el error
en el análisis semántico** con un mensaje claro:

```antlr
constantDeclaration: 'const' Identifier typeAnnotation? ('=' expression)? ';';
```

```text
programa.cps:1:1 [SEM007] La constante 'SIN_VALOR' debe inicializarse en su declaracion.
```

El lenguaje aceptado no cambia: `const x: integer;` sigue siendo inválido, pero
ahora con un diagnóstico útil en lugar de *"mismatched input ';'"*.

---

## D4. Sobrecarga del operador `+`

**Situación.** `program.cps` concatena cadenas con enteros en varias líneas
(`print("5 + 1 = " + addFive);`, `print("Number: " + n);`), pero los requisitos
solo dicen que los operandos aritméticos deben ser numéricos.

**Decisión: `+` está sobrecargado.**

| Caso | Resultado |
| --- | --- |
| `integer + integer` | `integer` |
| operación numérica con algún `float` | `float` |
| al menos un operando `string` | `string` (concatenación) |
| `-`, `*`, `/`, `%` | solo numéricos |

Un operando `string` "gana": la operación pasa a ser concatenación. El otro
operando debe ser **concatenable**: `string`, `integer`, `float`, `boolean` o
`null`. Se rechaza concatenar arreglos, instancias de clase y `void`
(`SEM047`), porque el lenguaje no define su representación textual.

---

## D5. `/` entre enteros produce `integer`

**Ambigüedad.** Los requisitos no especifican el tipo de `7 / 2`.

**Decisión: división entera.** `integer / integer` → `integer`. Si algún
operando es `float`, el resultado es `float`.

**Motivo.** Mantiene el álgebra de tipos cerrada sobre `integer` y evita que
`let promedio: integer = suma / cantidad;` falle con operandos enteros. Para un
cociente flotante basta con escribir `suma / 2.0` o declarar un operando como
`float`.

---

## D6. Semántica de `switch`

**Inconsistencia.** Los requisitos incluyen `switch` en la lista de estructuras
*"cuyas condiciones deben evaluar expresiones de tipo `boolean`"*. Pero tanto el
README del lenguaje como `program.cps` usan `switch (addFive)` con un entero, y
exigir un selector booleano haría inútil la construcción.

**Decisión: el selector de `switch` NO tiene que ser `boolean`.** Se aplica en
su lugar una regla de comparabilidad:

1. El selector debe tener un tipo con igualdad por valor: `integer`, `float`,
   `string` o `boolean` (`SEM045`). Se rechazan arreglos y objetos.
2. Cada expresión de `case` debe ser comparable con el selector, con las mismas
   reglas que `==` (`SEM043`). Se permite mezclar `integer` y `float`.
3. Los `case` con el mismo valor literal se reportan como duplicados
   (`SEM044`), indicando la línea de la primera aparición.
4. Cuando el selector es inválido se degrada a `error` para **no** encadenar un
   `SEM043` por cada `case`.
5. Un único `default`, y al final: ya lo garantiza la gramática
   (`switchCase* defaultCase?`).

Cada `case` recibe su propio ámbito de bloque, de modo que dos casos pueden
declarar una variable con el mismo nombre sin colisionar.

---

## D7. `break` dentro de `switch` (extensión documentada)

**Inconsistencia.** Los requisitos dicen literalmente que `break` y `continue`
solo pueden usarse *"dentro de bucles"*. Sin embargo, el README del lenguaje
presenta `switch` con la forma habitual de C/TypeScript, donde `break` es la
manera natural de cerrar un caso.

**Decisión: se permite `break` dentro de un `switch`, además de dentro de
bucles.** `continue` sigue siendo estrictamente exclusivo de los bucles.

Es una **extensión** consciente sobre la letra del requisito, con pruebas
separadas que la cubren:

- `tests/test_control_flow.py::test_break_dentro_de_switch_es_valido`
- `tests/test_control_flow.py::test_continue_dentro_de_switch_sin_bucle_es_invalido`
- `tests/test_control_flow.py::test_break_fuera_de_bucle`

Implementación: `Scope.is_inside_breakable()` acepta `LOOP` y `SWITCH`;
`Scope.is_inside_loop()` solo acepta `LOOP`. Ambas se detienen en la frontera de
una función, así que un `break` dentro de una función anidada declarada en un
bucle sigue siendo un error.

*Si el criterio del curso fuera estrictamente el literal del requisito, basta con
quitar `ScopeKind.SWITCH` de `BREAKABLE_SCOPES` en `compiler/symbols/scope.py`;
es un cambio de una línea.*

---

## D8. Tipo semántico de `null`

**Situación.** El README muestra `let d = null;` sin más detalle y la gramática
solo tiene el literal.

**Decisión: `null` es un tipo semántico propio (`PrimitiveType(NULL)`) con estas
reglas:**

- Asignable a **tipos de referencia**: clases, arreglos y `string`.
- **No** asignable a `integer`, `float` ni `boolean` (`SEM012`).
- `==` y `!=` contra una referencia son válidos; contra un tipo de valor no
  (`SEM016`).
- Prohibido en aritmética (`SEM048`) y en operaciones lógicas (`SEM014`).
- Permitido como operando de concatenación con `string`.
- `let x = null;` **sin** anotación es `SEM010`: `null` no determina un tipo.
  Lo correcto es `let x: Animal = null;`.

**`string` se considera de referencia** (y por tanto nulable). Los requisitos
solo prohíben `null` en `integer`, `float` y `boolean`; incluir `string` entre
los nulables es coherente con que sea un tipo por referencia.

---

## D9. Arreglos vacíos: `unknown[]`, no `any`

**Situación.** `let values: integer[] = [];` debe ser válido, pero un literal
vacío no tiene información de tipo por sí mismo.

**Decisión: el literal `[]` tiene tipo `unknown[]`**, un tipo interno pendiente
de resolver que se concreta con el tipo declarado del destino.

- `let values: integer[] = [];` → `values` es `integer[]`. ✅
- `let values = [];` → `SEM033`: no hay contexto para concretar el tipo.
- `let m: integer[][] = [];` → también válido.

**No se usa un tipo `any` general.** `unknown` solo aparece como elemento de un
arreglo sin resolver y nunca sirve para ocultar una incompatibilidad entre dos
tipos concretos.

---

## D10. Los arreglos son invariantes; los literales se tipan por contexto

**Ambigüedad.** ¿Debe `integer[]` ser asignable a `float[]`, dado que `integer`
sí se promueve a `float`?

**Decisión: los arreglos son invariantes.**

```cps
let xs: integer[] = [1, 2];
let ys: float[] = xs;          // SEM012 — invariancia
let zs: float[] = [1, 2];      // válido — tipado contextual del literal
```

**Motivo.** La covarianza de arreglos no es segura: si `integer[]` fuese un
`float[]`, escribir `ys[0] = 1.5;` corrompería `xs`. Es el mismo agujero que
tiene Java con los arreglos de objetos.

Para no perder ergonomía, un **literal escrito en el lugar de la asignación**
adopta el tipo destino si cada uno de sus elementos es asignable a él
(`TypeChecker._assignable_expression`, aplicado recursivamente en matrices). La
misma regla aplica a subclases: `let objs: Animal[] = [new Perro(), new Gato()];`
es válido, pero `let objs: Animal[] = perros;` no.

---

## D11. Índice literal fuera de rango: advertencia, no error

**Inconsistencia.** `program.cps` contiene deliberadamente un acceso fuera de
rango dentro de un `try`:

```cps
let numbers: integer[] = [1, 2, 3, 4, 5];
try {
  let risky: integer = numbers[10];      // fuera de rango
} catch (err) { … }
```

Si esto fuera un error, el programa de ejemplo del curso no compilaría.

**Decisión: es una advertencia (`SEM-W005`), no un error.**

- Solo se comprueba cuando el tamaño se conoce estáticamente: un literal directo
  (`[1,2,3][7]`) o una variable inicializada con un literal.
- El tamaño conocido se **invalida** en cuanto la variable se reasigna, así que
  no se producen falsos positivos.
- Con un índice variable **no se reporta nada**: la validación real corresponde
  al tiempo de ejecución.
- Con `--strict` la advertencia sí hace fallar la compilación.

---

## D12. Constructor heredado

**Situación.** `program.cps` hace `new Dog("Rex")` pero `class Dog : Animal` no
declara constructor propio; el constructor con parámetro `string` está en
`Animal`.

**Decisión: la búsqueda del constructor recorre la cadena de herencia.**
`ClassRegistry.lookup_constructor(clase)` devuelve el primer constructor
encontrado subiendo por los ancestros.

- `new Dog("Rex")` valida sus argumentos contra el constructor de `Animal`. ✅
- `new Dog()` sería `SEM021` (el constructor heredado exige un argumento).
- Si ninguna clase de la cadena declara constructor, solo se admite `new C()`
  sin argumentos; con argumentos es `SEM042`.

---

## D13. Tipo del identificador de `catch`

**Ambigüedad.** La gramática (`'catch' '(' Identifier ')'`) no permite anotar el
tipo, y `program.cps` lo concatena con una cadena:
`print("Caught an error: " + err);`.

**Decisión: el identificador de `catch` se tipa como `string`** (el mensaje del
error).

**Motivo.** Es el tipo que hace correcto el uso de `program.cps` sin introducir
una clase interna de error que el lenguaje no puede declarar ni construir. El
símbolo es inmutable, vive en un ámbito `CATCH` propio y no se filtra fuera del
bloque.

Si en una fase posterior se añade una jerarquía de excepciones, basta con
cambiar la constante `CATCH_ERROR_TYPE` en
`compiler/semantic/type_checker.py`.

---

## D14. Política de inferencia del tipo de retorno

**Ambigüedad.** La gramática permite `function f() { … }` sin `: tipo`, pero
ninguna fuente indica qué tipo tiene.

**Decisión:**

1. Sin ningún `return` con valor → `void`.
2. Con `return` de valores → el **tipo común** de todos ellos, calculado con
   `common_type` en secuencia (`integer` + `float` → `float`; `Perro` + `Gato`
   con base `Animal` → `Animal`).
3. Si dos `return` no tienen tipo común → `SEM023`.

Los **parámetros** sí exigen anotación (`SEM010`): inferirlos requeriría
análisis interprocedural, fuera del alcance de esta fase.

---

## D15. `void` como tipo escribible

**Decisión.** Se añadió `void` a `baseType` para poder escribir
`function f(): void { … }` explícitamente, como pide el requisito de *"funciones
con retorno `void`"*.

- `void` solo tiene sentido como tipo de retorno.
- `let x: void;` es `SEM049`.
- Usar el valor de una llamada a una función `void` es `SEM049`.

---

## D16. Acceso a atributos sin `this`

**Ambigüedad.** El README siempre escribe `this.nombre` dentro de los métodos,
pero no dice si `nombre` a secas es válido.

**Decisión: se acepta**, como consecuencia natural de que el ámbito de la clase
sea el padre del ámbito del método (lo que además da la jerarquía
Global → Clase → Método que pide el requisito de la tabla de símbolos).

Un parámetro con el mismo nombre sombrea al atributo, que es justo lo que hace
que el patrón habitual funcione:

```cps
function constructor(nombre: string) {
    this.nombre = nombre;   // 'nombre' es el parámetro; 'this.nombre' el atributo
}
```

Los atributos **heredados** solo son accesibles mediante `this.` o `obj.`,
porque el ámbito de la clase base no es padre del ámbito de la subclase; la
búsqueda por la cadena de herencia se hace en `ClassRegistry`.

---

## D17. Columnas 1-based

**Situación.** ANTLR entrega las columnas empezando en 0 y las líneas en 1.

**Decisión: todos los diagnósticos usan línea y columna 1-based**, que es lo que
esperan los editores y lo que hace que el panel del IDE salte al punto correcto.
La conversión se hace una sola vez, al construir el `SourceSpan` y en el
`ErrorListener`.

---

## D18. El análisis semántico no se ejecuta si hay errores sintácticos

**Decisión.** Cuando el parser reporta al menos un error, `compile_source`
devuelve el resultado con los diagnósticos sintácticos y **sin** AST ni tabla de
símbolos.

**Motivo.** ANTLR construye árboles con nodos de error para poder recuperarse;
analizarlos semánticamente produce decenas de diagnósticos falsos que ocultan el
error real. Los errores sintácticos sí se acumulan entre sí gracias a la
recuperación del parser.

---

## Resumen de los cambios a la gramática

Los únicos cambios a `program/Compiscript.g4` respecto del original del curso:

| Cambio | Justificación |
| --- | --- |
| `float` en `baseType` | D1 — requisito explícito de la fase |
| `void` en `baseType` | D15 — funciones con retorno `void` |
| `FloatLiteral` y su entrada en `Literal` | D1 — literales decimales |
| Inicializador opcional en `constantDeclaration` | D3 — hacer alcanzable `SEM007` |

Todo lo demás (precedencias, sufijos, clases, `switch`, `try/catch`, sentencias)
se mantiene **idéntico** al original. `program/Compiscript.bnf` se actualizó en
paralelo para no quedar desincronizado.
