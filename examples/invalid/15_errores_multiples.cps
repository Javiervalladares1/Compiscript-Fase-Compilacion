// @expect SEM004 SEM008 SEM013 SEM001 SEM017 SEM021 SEM022 SEM023 SEM034 SEM037 SEM027 SEM030
// Programa de demostracion: reune un error de cada familia semantica en un
// solo archivo para mostrar que el analizador NO se detiene en el primero y
// que cada diagnostico conserva su linea y su columna.
//
// El orden de los codigos de la cabecera es el orden de aparicion en el
// archivo, que es el mismo en el que el compilador los reporta.

// --- Ambitos y declaraciones ---------------------------------------------
let repetida: integer = 1;
let repetida: integer = 2;          // SEM004 redeclaracion en el mismo ambito

const LIMITE: integer = 10;
LIMITE = 20;                        // SEM008 reasignacion de constante

// --- Tipos y operadores ---------------------------------------------------
let bandera: boolean = true;
let mezcla = repetida * bandera;    // SEM013 operando no numerico

print(nuncaDeclarada);              // SEM001 identificador no declarado

// --- Control de flujo -----------------------------------------------------
if (repetida) {                     // SEM017 la condicion debe ser boolean
    print("no importa");
}

// --- Funciones ------------------------------------------------------------
function suma(a: integer, b: integer): integer {
    return a + b;
}

let pocos: integer = suma(1);       // SEM021 numero de argumentos
let malTipo: integer = suma("x", 2); // SEM022 tipo de argumento

function devuelveTexto(): integer {
    return "no es un entero";       // SEM023 tipo de retorno incompatible
}

// --- Clases ---------------------------------------------------------------
class Persona {
    let nombre: string;

    function constructor(nombre: string) {
        this.nombre = nombre;
    }
}

let p: Persona = new Persona("Ana");
print(p.edad);                      // SEM034 atributo inexistente

// --- this fuera de clase --------------------------------------------------
function fueraDeClase(): string {
    return this.nombre;             // SEM037 'this' fuera de una clase
}

// --- break fuera de bucle -------------------------------------------------
break;                              // SEM027 break fuera de bucle/switch

// --- Arreglos -------------------------------------------------------------
let numeros: integer[] = [1, 2, 3];
let malIndice: integer = numeros["dos"];  // SEM030 indice no entero
