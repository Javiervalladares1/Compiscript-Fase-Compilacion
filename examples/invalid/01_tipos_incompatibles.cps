// @expect SEM012 SEM012 SEM012
// Asignaciones cuyo tipo no coincide con el declarado.
let contador: integer = "diez";
let decimal: float = 1.5;
let entero: integer = decimal;      // float no se degrada a integer
let bandera: boolean = 1;
