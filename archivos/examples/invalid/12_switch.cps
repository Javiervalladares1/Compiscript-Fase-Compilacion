// @expect SEM043 SEM044 SEM045
// 'case' incompatible, 'case' duplicado y selector no comparable.
let numero: integer = 2;

switch (numero) {
  case 1: print("uno");
  case "dos": print("dos");      // tipo incompatible con el selector
  case 1: print("otro uno");     // literal duplicado
  default: print("otro");
}

let lista: integer[] = [1, 2];
switch (lista) {
  case 1: print("no comparable");
}
