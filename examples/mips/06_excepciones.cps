// Los errores se capturan incluso cuando ocurren dentro de otra funcion.
function dividir(a: integer, b: integer): integer {
  return a / b;
}
try {
  print(dividir(10, 0));
} catch (error) {
  print("Error atrapado: " + error);
}
let valores: integer[] = [1, 2];
try {
  print(valores[3]);
} catch (error) {
  print(error);
}
print("Continuamos");
