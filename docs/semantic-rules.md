# Reglas semánticas de Compiscript

Documento de referencia de las reglas que implementa el analizador. Cada regla
indica el código de diagnóstico que emite cuando se incumple. Los códigos son
estables: las pruebas verifican por código, no por el texto del mensaje.

---

## 1. Tipos

### 1.1 Tipos del lenguaje

| Tipo | Escribible | Descripción |
| --- | --- | --- |
| `integer` | Sí | Entero con signo |
| `float` | Sí | Punto flotante (extensión, ver `semantic-decisions.md`) |
| `string` | Sí | Cadena de texto |
| `boolean` | Sí | `true` / `false` |
| `void` | Sí | Ausencia de valor; solo válido como tipo de retorno |
| `null` | No (solo el literal) | Tipo del literal `null` |
| `T[]` | Sí | Arreglo de `T`, anidable (`integer[][]`) |
| `C` | Sí | Instancia de la clase `C` |
| `unknown` | No | Interno: elemento de `[]` sin resolver |
| `error` | No | Interno: algo ya reportado; absorbe operaciones |

`unknown` y `error` son compatibles con todo. Esto evita que un único error
produzca una cascada de diagnósticos derivados.

### 1.2 Asignabilidad — `is_assignable(source, target)`

| Origen \ Destino | `integer` | `float` | `string` | `boolean` | `C` | `T[]` |
| --- | --- | --- | --- | --- | --- | --- |
| `integer` | ✅ | ✅ promoción | ❌ | ❌ | ❌ | ❌ |
| `float` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `string` | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `boolean` | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| `null` | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| `D` (subclase de `C`) | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `C` (superclase de `D`) | ❌ | ❌ | ❌ | ❌ | ❌ (hacia `D`) | ❌ |
| `U[]` | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ solo si `U == T` |
| `unknown[]` (`[]`) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

Reglas clave:

- **Promoción `integer` → `float`**: permitida en asignaciones, argumentos,
  retornos y operaciones. La conversión inversa **no** es implícita (`SEM012`).
- **Arreglos invariantes**: `integer[]` no es asignable a `float[]`, porque
  escribir un `float` a través del alias corrompería el arreglo original.
  Un **literal** escrito en el lugar de la asignación sí adopta el tipo destino:
  `let x: float[] = [1, 2];` es válido (tipado contextual).
- **Clases covariantes**: una subclase es asignable a cualquiera de sus
  ancestros; nunca al revés.
- **Incumplimiento**: `SEM012`.

### 1.3 Inferencia

| Situación | Resultado |
| --- | --- |
| `let x: T = e;` | `T`; se comprueba `e` contra `T` |
| `let x = e;` | El tipo de `e` |
| `let x;` | `SEM010`: no hay información suficiente |
| `let x = [];` | `SEM033`: el arreglo vacío no tiene contexto |
| `let x = null;` | `SEM010`: `null` no determina un tipo |
| `let x: T[] = [];` | `T[]` (el tipo declarado concreta `unknown`) |
| `function f() {…}` | Ver §3.3 |

---

## 2. Operadores

### 2.1 `+` (sobrecargado)

`+` es el único operador sobrecargado: suma numérica **o** concatenación.

| Izquierda | Derecha | Resultado | Código si falla |
| --- | --- | --- | --- |
| `integer` | `integer` | `integer` | — |
| `integer`/`float` | `float`/`integer` | `float` | — |
| `string` | `string`, `integer`, `float`, `boolean`, `null` | `string` | — |
| cualquiera de los anteriores | `string` | `string` | — |
| `string` | `T[]`, clase, `void` | — | `SEM047` |
| `null` | numérico | — | `SEM048` |
| otros | otros | — | `SEM013` |

Si **al menos un** operando es `string`, `+` concatena. En caso contrario ambos
operandos deben ser numéricos.

### 2.2 `-`, `*`, `/`, `%`

Ambos operandos deben ser numéricos (`SEM013`; `SEM048` si interviene `null`).

| Izquierda | Derecha | Resultado |
| --- | --- | --- |
| `integer` | `integer` | `integer` |
| cualquiera con `float` | | `float` |

**`/` entre enteros produce `integer`** (división entera). Es una decisión
explícita y documentada: mantiene el álgebra de tipos cerrada sobre `integer` y
evita que `let x: integer = a / b;` falle para operandos enteros. Para obtener
un cociente flotante basta con que un operando lo sea: `a / 2.0`.

### 2.3 Operador unario `-` y `!`

| Operador | Operando | Resultado | Código si falla |
| --- | --- | --- | --- |
| `-` | numérico | el mismo tipo | `SEM013` |
| `!` | `boolean` | `boolean` | `SEM014` |

### 2.4 Lógicos `&&`, `||`

Ambos operandos deben ser `boolean`; el resultado es `boolean` (`SEM014`).

### 2.5 Relacionales `<`, `<=`, `>`, `>=`

Solo aceptan operandos **numéricos** (se permite mezclar `integer` y `float`).
El resultado es `boolean`.

Compiscript **no** define orden lexicográfico para `string`, así que
`"a" < "b"` se **rechaza** (`SEM015`). Tampoco se ordenan `boolean`, arreglos ni
objetos.

### 2.6 Igualdad `==`, `!=`

El resultado es siempre `boolean`. Los operandos deben ser compatibles en algún
sentido (`SEM016`):

| Comparación | Válida |
| --- | --- |
| `integer` vs `float` | ✅ |
| `T` vs `T` | ✅ |
| referencia vs `null` | ✅ |
| subclase vs superclase | ✅ |
| `string` vs `integer` | ❌ |
| `void` vs cualquiera | ❌ |
| `integer` vs `null` | ❌ (`integer` no es nulable) |

### 2.7 Ternario `c ? a : b`

- `c` debe ser `boolean` (`SEM017`).
- `a` y `b` deben tener un tipo común: el más específico posible
  (`common_type`). Ejemplos: `integer`+`float` → `float`; `Perro`+`Gato` con
  base común `Animal` → `Animal`; referencia + `null` → la referencia.
- Sin tipo común: `SEM018`.

---

## 3. Funciones

### 3.1 Declaración

Se registra: nombre, parámetros **en orden** con su tipo, tipo de retorno,
ámbito de declaración, nodo del cuerpo, función contenedora y capturas.

| Regla | Código |
| --- | --- |
| No hay sobrecarga: dos funciones con el mismo nombre en el mismo ámbito | `SEM004` |
| Parámetros con nombre repetido | `SEM005` |
| Parámetro sin anotación de tipo | `SEM010` |

### 3.2 Llamadas

| Regla | Código |
| --- | --- |
| La función debe estar declarada | `SEM002` |
| El número de argumentos debe coincidir | `SEM021` |
| Cada argumento debe ser asignable a su parámetro (posicional) | `SEM022` |
| Solo se puede invocar algo invocable (no una variable ni una clase) | `SEM020` |

Las funciones se registran **antes** de analizar los cuerpos, por lo que se
admite recursión directa, recursión mutua y llamar a una función declarada más
adelante.

### 3.3 Retornos

| Regla | Código |
| --- | --- |
| `return` fuera de una función o método | `SEM024` |
| Valor no asignable al tipo declarado | `SEM023` |
| `return;` en una función con tipo de retorno no `void` | `SEM023` |
| `return e;` en una función `void` | `SEM026` |
| `return e;` en un constructor | `SEM026` |
| Existe un camino que termina sin retornar valor | `SEM025` |

**Política de inferencia** (funciones sin `: tipo`):

1. Si el cuerpo no contiene ningún `return` con valor → `void`.
2. Si los contiene, el tipo es el **tipo común** de todos los valores
   retornados (`common_type` aplicado en secuencia).
3. Si dos `return` no tienen tipo común → `SEM023`.

### 3.4 Análisis de caminos de retorno

`SEM025` se emite cuando el análisis **puede demostrar** que existe un camino
sin `return`. Es conservador: nunca reporta un falso positivo.

Un bloque "siempre retorna" si:

- Su última sentencia alcanzable es `return`.
- Es un `if`/`else` en el que **ambas** ramas siempre retornan.
- Es un `switch` con `default` en el que **todos** los casos siempre retornan.
- Es un `try`/`catch` en el que ambos bloques siempre retornan.
- Es un `do-while` cuyo cuerpo siempre retorna (se ejecuta al menos una vez).
- Es un `while (true)` sin `break` cuyo cuerpo siempre retorna.

Los `while`/`for`/`foreach` con condición no literal **no** garantizan
ejecución, así que no cuentan como camino de retorno.

### 3.5 Funciones anidadas y closures

- Una función anidada solo es visible dentro del ámbito donde se declara.
- Puede leer variables de los ámbitos externos.
- Cada variable de un ámbito de función externo que se usa dentro de una
  función anidada se registra en `FunctionSymbol.captures` y la variable se
  marca `captured = True`.
- Las variables **globales no se cuentan como capturas** (no requieren cierre).
- La recursión mutua también funciona entre funciones anidadas hermanas.

```cps
function outer(x: integer): integer {
    let offset: integer = 1;
    function inner(): integer {
        return x + offset;      // inner.captures == ["x", "offset"]
    }
    return inner();
}
```

---

## 4. Ámbitos

| Regla | Código |
| --- | --- |
| Uso de un identificador no declarado | `SEM001` |
| Asignación a un identificador no declarado | `SEM009` |
| Redeclaración en el **mismo** ámbito | `SEM004` |
| Uso de una variable antes de inicializarla (cuando se puede determinar) | `SEM046` |
| Uso de una clase como valor | `SEM019` |

Se crea un ámbito nuevo para: cada función, cada método, cada clase, cada
bloque, cada bucle (`while`, `do-while`, `for`, `foreach`), cada `catch`, cada
`switch` y cada `case`.

**Sombreado**: una declaración en un ámbito interior puede ocultar una del
exterior. **Redeclaración**: dos declaraciones del mismo nombre en el mismo
ámbito son un error.

Alcance de las variables de control:

- La variable de `for (let i …)` vive en el ámbito del bucle.
- La variable de `foreach (n in xs)` vive en el ámbito del bucle y toma el tipo
  del elemento.
- El identificador de `catch (err)` vive solo en el bloque `catch`.

**Constantes**:

| Regla | Código |
| --- | --- |
| Una constante debe inicializarse en su declaración | `SEM007` |
| Una constante no puede reasignarse | `SEM008` |

---

## 5. Arreglos

| Regla | Código |
| --- | --- |
| Los elementos de un literal deben tener un tipo común | `SEM032` |
| `[]` sin contexto de tipo | `SEM033` |
| El índice debe ser `integer` | `SEM030` |
| Solo se puede indexar un arreglo | `SEM031` |
| El valor asignado a una posición debe ser del tipo del elemento | `SEM012` |
| Índice literal fuera de un tamaño conocido estáticamente | `SEM-W005` (aviso) |

- El tipo de `xs[i]` es el tipo del elemento; encadenar accesos reduce una
  dimensión por acceso (`m[0][1]` sobre `integer[][]` da `integer`).
- Un literal vacío tiene tipo `unknown[]`, que se concreta con el tipo
  declarado del destino.
- El chequeo de rango solo se aplica cuando el tamaño se conoce estáticamente
  (literal directo o variable inicializada con un literal y no reasignada
  después). Con índices variables **no se reporta nada**: la validación real
  corresponde al tiempo de ejecución.

---

## 6. Clases, objetos y herencia

| Regla | Código |
| --- | --- |
| Miembro duplicado dentro de una clase | `SEM006` |
| Más de un constructor | `SEM006` |
| La clase base debe existir | `SEM039` |
| Ciclos de herencia | `SEM040` |
| La propiedad accedida con `.` debe existir | `SEM034` |
| El método invocado con `.` debe existir | `SEM035` |
| `.` sobre un valor que no es objeto | `SEM036` |
| `this` fuera de una clase | `SEM037` |
| `new` sobre algo que no es una clase | `SEM038` |
| Clase inexistente en `new` | `SEM003` |
| Argumentos del constructor | `SEM021` / `SEM022` |
| Clase sin constructor instanciada con argumentos | `SEM042` |
| Sobrescritura con firma incompatible | `SEM041` |

**Resolución de `dog.speak()`**:

1. Se resuelve el símbolo `dog` en la cadena de ámbitos.
2. Se obtiene su tipo, que debe ser un `ClassType`.
3. Se busca `speak` entre los métodos de esa clase.
4. Si no está, se recorre la cadena de herencia hacia arriba.
5. Se validan número y tipo de los argumentos.
6. El tipo de la expresión es el tipo de retorno del método.

**Constructor heredado**: si una clase no declara constructor propio, se busca
en su cadena de ancestros y se usa el primero encontrado. Así
`class Dog : Animal {}` admite `new Dog("Rex")` con el constructor de `Animal`.
Si no hay constructor en ninguna clase de la cadena, solo se admite `new C()`
sin argumentos.

**Sobrescritura compatible**: misma aridad, mismos tipos de parámetro y mismo
tipo de retorno que el método de la clase base.

**`this`**: solo válido dentro de métodos y del constructor; su tipo es el de la
clase que contiene el método.

---

## 7. Control de flujo

| Estructura | Regla | Código |
| --- | --- | --- |
| `if` | condición `boolean` | `SEM017` |
| `while` | condición `boolean` | `SEM017` |
| `do-while` | condición `boolean` | `SEM017` |
| `for` | condición central `boolean` (si existe) | `SEM017` |
| `foreach` | la expresión recorrida debe ser un arreglo | `SEM029` |
| `break` | dentro de un bucle **o de un `switch`** | `SEM027` |
| `continue` | dentro de un bucle | `SEM028` |
| `return` | dentro de una función o método | `SEM024` |

Ni `break` ni `continue` atraviesan la frontera de una función anidada: un
`break` dentro de una función declarada en un bucle es un error.

**`switch`** (ver `semantic-decisions.md`):

| Regla | Código |
| --- | --- |
| El selector debe ser `integer`, `float`, `string` o `boolean` | `SEM045` |
| Cada `case` debe ser comparable con el selector | `SEM043` |
| Los `case` con literal repetido | `SEM044` |

El selector **no** tiene que ser `boolean`: `switch (numero)` es el caso normal.
La gramática ya garantiza un único `default` y que aparezca al final.

**`try`/`catch`**: el bloque `try` y el `catch` tienen ámbitos independientes.
El identificador del `catch` se tipa como `string` (el mensaje del error), es
inmutable y no existe fuera del bloque `catch`.

---

## 8. `null`

| Operación | Válida |
| --- | --- |
| Asignar a clase, arreglo o `string` | ✅ |
| Asignar a `integer`, `float`, `boolean` | ❌ `SEM012` |
| `== null` / `!= null` sobre una referencia | ✅ |
| `== null` sobre `integer`/`float`/`boolean` | ❌ `SEM016` |
| Aritmética (`+ - * / %`) | ❌ `SEM048` |
| Lógica (`&& || !`) | ❌ `SEM014` |
| Comparación relacional | ❌ `SEM015` |
| Concatenación con `string` | ✅ (produce `string`) |
| `let x = null;` sin anotación | ❌ `SEM010` |

---

## 9. Código muerto

Se reporta como **advertencia**: no impide la compilación, pero con `--strict`
provoca un código de salida distinto de cero.

| Situación | Código |
| --- | --- |
| Sentencias después de `return` | `SEM-W001` |
| Sentencias después de `break` | `SEM-W002` |
| Sentencias después de `continue` | `SEM-W003` |
| Bloque inalcanzable por condición literal (`if (false)`, `while (false)`) | `SEM-W004` |
| Índice literal fuera del rango conocido | `SEM-W005` |

Solo se advierte de la **primera** sentencia inalcanzable de cada secuencia.
Un `return`/`break`/`continue` que ya es un error por estar fuera de contexto
**no** marca como muerto el código que le sigue.

---

## 10. Catálogo completo de códigos

### Léxico y sintáctico

| Código | Significado |
| --- | --- |
| `SYN001` | Error sintáctico |
| `SYN002` | Error léxico |

### Errores semánticos

| Código | Significado |
| --- | --- |
| `SEM001` | Identificador no declarado |
| `SEM002` | Función no declarada |
| `SEM003` | Clase no declarada |
| `SEM004` | Redeclaración en el mismo ámbito |
| `SEM005` | Parámetro duplicado |
| `SEM006` | Miembro duplicado en una clase |
| `SEM007` | Constante sin inicializador |
| `SEM008` | Reasignación de una constante |
| `SEM009` | Asignación a un identificador no declarado |
| `SEM010` | No se puede inferir el tipo |
| `SEM011` | Nombre de tipo desconocido |
| `SEM012` | Asignación incompatible |
| `SEM013` | Operando no numérico |
| `SEM014` | Operando no booleano |
| `SEM015` | Comparación relacional inválida |
| `SEM016` | Igualdad entre tipos incompatibles |
| `SEM017` | Condición no booleana |
| `SEM018` | Ramas del ternario incompatibles |
| `SEM019` | Identificador no evaluable como valor |
| `SEM020` | La expresión no es invocable |
| `SEM021` | Número de argumentos incorrecto |
| `SEM022` | Tipo de argumento incompatible |
| `SEM023` | Tipo de retorno incompatible |
| `SEM024` | `return` fuera de una función |
| `SEM025` | Camino sin retorno en función con tipo declarado |
| `SEM026` | `return` con valor en función `void` o constructor |
| `SEM027` | `break` fuera de un bucle o `switch` |
| `SEM028` | `continue` fuera de un bucle |
| `SEM029` | `foreach` sobre un valor no iterable |
| `SEM030` | Índice de arreglo no entero |
| `SEM031` | Valor no indexable |
| `SEM032` | Elementos de arreglo heterogéneos |
| `SEM033` | Arreglo vacío sin contexto de tipo |
| `SEM034` | Propiedad inexistente |
| `SEM035` | Método inexistente |
| `SEM036` | Acceso a propiedad sobre un no-objeto |
| `SEM037` | `this` fuera de una clase |
| `SEM038` | `new` sobre algo que no es una clase |
| `SEM039` | Clase base inexistente |
| `SEM040` | Ciclo de herencia |
| `SEM041` | Sobrescritura con firma incompatible |
| `SEM042` | Uso incorrecto del constructor |
| `SEM043` | `case` incompatible con el selector |
| `SEM044` | `case` literal duplicado |
| `SEM045` | Selector de `switch` no comparable |
| `SEM046` | Uso antes de la inicialización |
| `SEM047` | Concatenación inválida |
| `SEM048` | Operación aritmética con `null` |
| `SEM049` | `void` usado como valor |
| `SEM050` | Destino de asignación inválido |

### Advertencias

| Código | Significado |
| --- | --- |
| `SEM-W001` | Código inalcanzable después de `return` |
| `SEM-W002` | Código inalcanzable después de `break` |
| `SEM-W003` | Código inalcanzable después de `continue` |
| `SEM-W004` | Bloque inalcanzable por condición literal |
| `SEM-W005` | Índice literal fuera de rango |
