// Arreglos homogeneos, matrices, indexacion y arreglo vacio con contexto.
let valores: integer[] = [1, 2, 3];
let matriz: integer[][] = [[1, 2], [3, 4]];
let vacio: integer[] = [];             // el tipo declarado concreta unknown[]
let flotantes: float[] = [1.5, 2.5];
let mixtoValido: float[] = [1, 2.5];   // integer se promueve a float

let primero: integer = valores[0];
let fila: integer[] = matriz[0];
let celda: integer = matriz[0][1];

valores[0] = 99;                       // asignacion a posicion de arreglo
matriz[1][0] = 7;

function multiplos(n: integer): integer[] {
  return [n * 1, n * 2, n * 3];
}

let devueltos: integer[] = multiplos(2);
print("" + primero + fila[1] + celda + devueltos[2] + flotantes[0] + mixtoValido[1]);
print("" + valores[0] + matriz[1][0]);
