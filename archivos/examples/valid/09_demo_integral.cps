// Demostracion integral: recorre en un solo archivo todas las familias de
// reglas semanticas que valida el compilador. Compila sin errores y sin
// advertencias (pasa tambien en modo --strict).

// --- Tipos primitivos e inferencia ---------------------------------------
const PI: float = 3.1416;
let entero: integer = 42;
let texto: string = "Compiscript";
let bandera: boolean = true;

let inferidoEntero = 10;            // integer
let inferidoTexto = "hola";         // string
let inferidoBool = false;           // boolean
let inferidoFloat = 2.5;            // float

// --- Promocion integer -> float y concatenacion ---------------------------
let promovido: float = entero + PI;
let mensaje: string = "El valor es " + entero;

// --- Aritmetica completa, incluido el modulo ------------------------------
let suma: integer = 10 + 3;
let resta: integer = 10 - 3;
let producto: integer = 10 * 3;
let cociente: integer = 10 / 3;     // division entera (ver D5)
let residuo: integer = 10 % 3;

// --- Logica y comparaciones -----------------------------------------------
let logico: boolean = bandera && !false;
let comparacion: boolean = suma > resta;

// --- Ternario -------------------------------------------------------------
let mayor: integer = suma > resta ? suma : resta;

// --- Arreglos y matrices --------------------------------------------------
let notas: integer[] = [90, 85, 100];
let matriz: integer[][] = [[1, 2], [3, 4]];
let vacio: integer[] = [];
let primera: integer = notas[0];
let celda: integer = matriz[1][0];

// --- Ambitos anidados y shadowing ----------------------------------------
let sombra: integer = 1;
{
    let sombra: string = "otro ambito";     // shadowing permitido
    print(sombra);
}
print(sombra);

// --- Funciones, recursion, anidamiento y closures -------------------------
function factorial(n: integer): integer {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

function crearAcumulador(inicial: integer): integer {
    let total: integer = inicial;

    function acumular(cantidad: integer): integer {
        return total + cantidad;    // captura 'total' del ambito externo
    }

    return acumular(5);
}

function sinRetorno(): void {
    print("no devuelve nada");
}

// --- Control de flujo -----------------------------------------------------
if (comparacion) {
    print("suma es mayor");
} else {
    print("resta es mayor");
}

let contador: integer = 0;
while (contador < 3) {
    contador = contador + 1;
}

do {
    contador = contador - 1;
} while (contador > 0);

for (let i: integer = 0; i < 3; i = i + 1) {
    if (i == 1) {
        continue;
    }
    print(i);
}

foreach (nota in notas) {
    if (nota == 100) {
        break;
    }
    print(nota);
}

switch (entero) {
    case 42:
        print("cuarenta y dos");
        break;
    case 7:
        print("siete");
        break;
    default:
        print("otro");
}

try {
    print("intento");
} catch (err) {
    print("Error atrapado: " + err);
}

// --- Clases, herencia, this, constructor y new ----------------------------
class Animal {
    let nombre: string;

    function constructor(nombre: string) {
        this.nombre = nombre;
    }

    function hablar(): string {
        return this.nombre + " hace ruido.";
    }
}

class Perro : Animal {
    function hablar(): string {
        return this.nombre + " ladra.";
    }

    function suNombre(): string {
        return this.nombre;         // atributo heredado via this
    }
}

let perro: Perro = new Perro("Toby");   // constructor heredado de Animal
print(perro.hablar());
print(perro.suNombre());

let animal: Animal = perro;             // una subclase es asignable a su base

// --- Acceso encadenado ----------------------------------------------------
class Caja {
    let items: integer[];

    function constructor() {
        this.items = [1, 2, 3];
    }

    function misma(): Caja {
        return this;
    }
}

function crearCaja(): Caja {
    return new Caja();
}

let encadenado: integer = crearCaja().misma().items[2];

// --- Asignacion como expresion --------------------------------------------
let a: integer = 0;
let b: integer = 0;
a = b = 7;

print(factorial(5));
print(crearAcumulador(10));
print(encadenado);
print(a);
sinRetorno();
