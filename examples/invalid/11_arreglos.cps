// @expect SEM032 SEM030 SEM031 SEM012 SEM033
// Errores de homogeneidad, indices y dimensiones.
let heterogeneo = [1, "dos", true];
let valores: integer[] = [1, 2, 3];
let indiceMalo: integer = valores["cero"];
let noIndexable: integer = 5;
let acceso: integer = noIndexable[0];
let matriz: integer[][] = [[1, 2]];
let dimensionMala: integer[] = matriz;
let sinContexto = [];
