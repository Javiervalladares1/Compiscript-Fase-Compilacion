// Salida: suma=12, true, 3.75000000, 7, 1.
let numeros: integer[] = [1, 2, 3, 4, 5];
let suma: integer = 0;
foreach (numero in numeros) {
  if (numero == 3) { continue; }
  suma = suma + numero;
}
print("suma=" + suma);

function esPar(n: integer): boolean {
  if (n == 0) { return true; }
  return esImpar(n - 1);
}
function esImpar(n: integer): boolean {
  if (n == 0) { return false; }
  return esPar(n - 1);
}
print(esPar(8));

function promedio(a: float, b: float): float { return (a + b) / 2; }
print(promedio(2, 5.5));

let elegido: integer = suma > 10 ? 7 : 9;
print(elegido);
let vueltas: integer = 0;
while (vueltas < 5) {
  vueltas = vueltas + 1;
  if (vueltas == 1) { break; }
}
print(vueltas);
