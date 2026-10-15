// @expect SEM017 SEM017 SEM017 SEM017 SEM027 SEM028 SEM029
// Condiciones no booleanas y break/continue fuera de contexto.
if (1) { print("no"); }
while ("cadena") { print("no"); }
do { print("no"); } while (3);
for (let i: integer = 0; i + 1; i = i + 1) { print("no"); }

break;
continue;

let numero: integer = 5;
foreach (elemento in numero) { print(elemento); }
