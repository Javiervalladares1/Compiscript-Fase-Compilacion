// @expect SEM013 SEM013 SEM014 SEM014 SEM015 SEM016
// Operandos con tipos incorrectos para cada familia de operadores.
let malAritmetico: integer = "a" * 2;
let malUnario: integer = -"texto";
let malLogico: boolean = 1 && true;
let malNegacion: boolean = !5;
let malRelacional: boolean = "a" < "b";     // no hay orden lexicografico
let malIgualdad: boolean = "a" == 1;
