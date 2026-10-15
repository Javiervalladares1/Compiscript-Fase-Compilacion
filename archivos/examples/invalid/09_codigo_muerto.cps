// @expect SEM-W001 SEM-W002 SEM-W003
// Instrucciones inalcanzables (advertencias).
function conRetorno(): integer {
  return 1;
  print("inalcanzable");
}

while (true) {
  break;
  print("inalcanzable");
}

for (let i: integer = 0; i < 3; i = i + 1) {
  continue;
  print("inalcanzable");
}
