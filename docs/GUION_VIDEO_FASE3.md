# Guion para el video — Proyecto 3 de Compiladores

Duración sugerida: **7–8 minutos**, incluyendo los cambios de pantalla.
El texto entre comillas se puede leer o adaptar. Las indicaciones de pantalla
son acciones para ti, no parte de la narración.

## Preparación antes de grabar

1. Abre el IDE en **http://127.0.0.1:5001**. Si el servidor está detenido,
   ejecuta desde la carpeta del proyecto:

   ```bash
   bash scripts/start_ide.sh
   ```

   Deja esa terminal abierta. Para detenerlo, usa `Ctrl+C` en esa terminal.
   El puerto 5001 evita el puerto 5000 que ocupa macOS en este equipo.

2. Abre el navegador en una ventana amplia para mostrar el editor a la izquierda
   y los resultados a la derecha. Aumenta el zoom si el código se ve pequeño.
3. En el IDE selecciona **Generar MIPS**, **Registros — getReg()** y
   **Factorial recursivo**. Pulsa **Cargar ejemplo**.
4. Ten otra terminal en la raíz del proyecto para ejecutar SPIM por separado.
   No detengas la terminal del servidor al cambiar de pantalla.
5. Ten a mano `compiler/backend/registers.py` y `compiler/backend/mips.py`
   en tu editor para mostrar la implementación.

El selector incluye seis ejemplos MIPS y el programa completo del curso.
`program/program.cps` también se ejecuta con clases, herencia y `try/catch`.
Para explicar las llamadas y retornos, comienza con el factorial.

## 0:00–0:40 · Presentación y objetivo

**Pantalla:** IDE abierto con el factorial visible.

> “En este video voy a presentar la tercera fase de nuestro compilador de
> Compiscript. En las fases anteriores ya teníamos el análisis léxico,
> sintáctico y semántico. Ahora agregamos código de tres direcciones y su
> traducción a assembler MIPS.
>
> Voy a demostrar los tres requisitos: las secuencias de llamada y retorno de
> funciones, la asignación de registros mediante getReg con respaldo en pila,
> y la ejecución del código generado en un simulador externo, que en nuestro
> caso es SPIM.”

## 0:40–1:20 · Programa fuente

**Acción:** muestra el ejemplo **Factorial recursivo** y pulsa **Compilar**.
Puedes abrir brevemente **AST** y **Tabla de simbolos** para mostrar que las
etapas anteriores siguen presentes; después pasa a **TAC**.

> “Este programa calcula factorial de cinco, seis y siete. La función tiene un
> caso base que retorna uno y una llamada recursiva que calcula factorial de
> n menos uno.
>
> La recursión nos sirve para comprobar el manejo de memoria: cada llamada
> necesita conservar su propio parámetro n y la dirección a la que debe
> regresar. Cuando termina la llamada interna, la llamada anterior todavía
> necesita su valor de n para realizar la multiplicación.”

## 1:20–2:05 · Código de tres direcciones

**Pantalla:** pestaña **TAC**. Señala `param`, `call`, temporales `_t...`,
`ifz` y `return`. No hace falta leer todo el archivo.

> “Después de validar el programa, el compilador transforma el AST en una
> representación intermedia tipada. Aquí vemos el código de tres direcciones.
>
> Las expresiones se dividen en operaciones sencillas con temporales. La
> condición utiliza una etiqueta y un salto condicional. Las llamadas muestran
> los parámetros, la instrucción call y el temporal que recibe el resultado.
> Return identifica el valor que debe devolver la función.
>
> El generador de MIPS recibe esta representación intermedia, de modo que la
> traducción a assembler es una etapa separada del análisis del programa.”

## 2:05–3:20 · Llamadas, retornos y stack pointer

**Pantalla:** pestaña **MIPS**. Desplázate hasta `_cs_fn_0_factorial:`.
En este ejemplo se observa un marco de **48 bytes** en modo de registros.
Señala estos fragmentos reales, sin recorrer las rutinas auxiliares del final:

```asm
addiu $sp, $sp, -48
sw $ra, 44($sp)
sw $fp, 40($sp)
sw $s0, 36($sp)
move $fp, $sp
```

> “Cada llamada reserva un marco de activación en la pila. Al entrar en esta
> función, se ajusta el stack pointer y se guardan la dirección de retorno,
> el frame pointer anterior y los registros preservados que utiliza la función.
>
> El frame pointer permite ubicar los parámetros, las variables locales y los
> temporales aunque el stack pointer cambie para preparar otra llamada.
> La instrucción jal realiza el salto a la función y establece la dirección
> de retorno.
>
> En la recursión se crea un marco nuevo para cada invocación. Por eso los
> parámetros de una llamada no sobrescriben los de la anterior.”

**Acción:** busca el epílogo `_cs_fn_0_factorial_return:` y señala la restauración.

> “Todos los return llegan a un epílogo común. Aquí se restauran los registros,
> se recupera el espacio de la pila y se regresa con jr ra. Para los resultados
> enteros usamos v0; para los resultados float usamos f0.”

## 3:20–4:15 · Explicación de getReg()

**Pantalla:** abre `compiler/backend/registers.py` y muestra `getReg()`,
`spill()` y `flush()`. Vuelve al IDE al terminar.

> “La asignación de registros se implementa en getReg. Primero comprueba si un
> operando ya tiene un registro y puede reutilizarlo. Si no, busca uno libre:
> los temporales prefieren registros t y las variables prefieren registros s.
>
> Si todos están ocupados, selecciona una víctima cuyo siguiente uso esté más
> lejos. Los operandos de la instrucción actual están protegidos para evitar
> reemplazarlos mientras todavía se necesitan.
>
> Si el valor de la víctima fue modificado, se guarda en su posición de memoria
> antes de reutilizar el registro. Eso es un spill. Además, antes de una llamada
> y al cambiar de bloque de control se sincronizan los valores con la memoria.
> Los registros s utilizados se guardan y restauran en la entrada y salida de
> cada función.”

No lo describas como coloreo de grafos: el asignador implementado es local,
con búsqueda de siguiente uso y respaldo conservador en memoria.

## 4:15–5:00 · Ejecución real en SPIM

**Acción:** en el IDE pulsa **Ejecutar en SPIM** y muestra **Salida SPIM**:

```text
120
720
5040
```

> “Al ejecutar, el servidor compila el programa y envía el assembler generado
> al ejecutable de SPIM. La salida es ciento veinte, setecientos veinte y
> cinco mil cuarenta, que corresponden a los factoriales esperados.
>
> También podemos separar las etapas y correr el archivo assembler
> directamente desde la terminal.”

**En la segunda terminal**, ejecuta:

```bash
.venv/bin/python program/Driver.py examples/mips/01_factorial.cps \
  --tac out/video/factorial.tac --mips out/video/factorial.asm

spim -file out/video/factorial.asm
```

El primer comando genera los archivos y el segundo ejecuta únicamente el
assembler en la herramienta externa. Muestra ambos comandos y sus resultados.

## 5:00–5:50 · Parámetros y llamadas anidadas

**Acción:** vuelve al IDE. Selecciona **Llamadas y 6 parámetros**, pulsa
**Cargar ejemplo** y luego **Ejecutar en SPIM**. La salida es:

```text
21
55
13
```

> “Este segundo ejemplo prueba una función con seis parámetros. Los primeros
> cuatro argumentos se pasan en a0 a a3 y los restantes se colocan en la pila
> del llamador.
>
> El resultado veintiuno corresponde a la suma de uno a seis. Fibonacci de diez
> da cincuenta y cinco y comprueba dos llamadas recursivas dentro de la misma
> expresión. El resultado trece corresponde a una función que conserva una
> variable local mientras llama a otra función y luego vuelve a utilizarla.”

## 5:50–6:25 · Estrategia de pila

**Acción:** carga nuevamente **Factorial recursivo**. Cambia **Asignación**
a **Pila** y pulsa **Ejecutar en SPIM**.

> “También implementamos una estrategia alternativa de pila. En este modo,
> los resultados se sincronizan con memoria después de cada instrucción
> intermedia. Los registros siguen siendo necesarios para realizar las
> operaciones MIPS, pero sus valores no se mantienen como caché entre
> instrucciones.
>
> El programa vuelve a producir los mismos tres resultados. Esto comprueba
> que ambas estrategias conservan el comportamiento del programa.”

## 6:25–7:15 · Validación y cierre

**Acción:** en la segunda terminal ejecuta:

```bash
.venv/bin/python -m pytest tests/test_mips.py tests/test_ide_phase3.py -q
```

Muestra el resultado real de la ejecución y utiliza el número que aparezca.
La batería completa se ejecuta con `python -m pytest -o addopts='' -q`.

> “La validación incluye recursión, llamadas anidadas, más de cuatro argumentos,
> presión de registros, los dos modos de asignación y comprobaciones de
> restauración del stack pointer, del frame pointer y de los registros s.
> También verificamos la integración con el IDE y los errores de ejecución.
>
> Con esta fase ya podemos pasar de un programa Compiscript validado a código
> de tres direcciones y luego a MIPS ejecutable. Las funciones y sus retornos,
> la asignación de registros y la ejecución mediante SPIM quedan demostradas.
>
> El alcance incluye funciones globales y anidadas con capturas, tipos
> escalares, arreglos, clases, herencia, métodos virtuales y try/catch. Las
> limitaciones de las extensiones adicionales están documentadas en la guía.”

## Alternativa: demostración guiada en terminal

Si prefieres no escribir los comandos durante el video:

```bash
bash scripts/demo_video.sh
```

El script pausa antes de cada sección para que puedas explicar y presionar
Enter cuando estés listo. Muestra el fuente, genera TAC y MIPS, enseña las
instrucciones de llamadas y retornos, ejecuta SPIM por separado, demuestra
seis parámetros y el modo de pila, y termina con las pruebas del backend.

Para ensayarlo completo sin pausas:

```bash
bash scripts/demo_video.sh --auto
```

Los archivos de esta demostración se guardan en `out/video/`. La carpeta está
excluida de Git porque contiene resultados que el compilador puede regenerar.
