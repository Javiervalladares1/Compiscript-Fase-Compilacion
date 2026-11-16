// Todas las estructuras de control con condiciones booleanas.
let numeros: integer[] = [1, 2, 3, 4, 5];
let i: integer = 0;

if (i < 3) { print("menor"); } else { print("mayor o igual"); }

while (i < 3) { i = i + 1; }

do { i = i - 1; } while (i > 0);

for (let j: integer = 0; j < 3; j = j + 1) {
  if (j == 1) { continue; }
  print("j=" + j);
}

foreach (n in numeros) {
  if (n > 3) { break; }
  print("n=" + n);
}

switch (i) {
  case 0:
    print("cero");
    break;
  case 1:
    print("uno");
  default:
    print("otro");
}

try {
  print("intentando");
} catch (err) {
  print("error: " + err);              // err se tipa como string
}
