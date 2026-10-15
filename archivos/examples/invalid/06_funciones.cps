// @expect SEM005 SEM004 SEM021 SEM022 SEM002 SEM020
// Errores de declaracion y de llamada a funciones.
function duplicados(a: integer, a: integer): integer { return a; }
function repetida(): integer { return 1; }
function repetida(): integer { return 2; }
function suma(a: integer, b: integer): integer { return a + b; }

let pocos: integer = suma(1);
let malTipo: integer = suma(1, "dos");
let inexistente: integer = noExisteFuncion(1);
let variable: integer = 5;
let noInvocable: integer = variable(1);
