// Operador ternario y semantica de null.
class Caja { let valor: integer; }

let condicion: boolean = true;
let entero: integer = 1;
let flotante: float = 2.5;

let comun: float = condicion ? entero : flotante;   // tipo comun = float
let mismo: integer = condicion ? 1 : 2;

let caja: Caja = null;                              // null en tipo de clase
let lista: integer[] = null;                        // null en arreglo
let cadena: string = null;                          // string es de referencia
let esNulo: boolean = caja == null;
let noEsNulo: boolean = lista != null;
print("" + comun + mismo + esNulo + noEsNulo + cadena);
