// Funciones, recursion directa, recursion mutua e inferencia de retorno.
function factorial(n: integer): integer {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}

function esPar(n: integer): boolean {
  if (n == 0) { return true; }
  return esImpar(n - 1);
}

function esImpar(n: integer): boolean {
  if (n == 0) { return false; }
  return esPar(n - 1);
}

function sinAnotacion() {              // el tipo de retorno se infiere
  return 42;
}

function procedimiento(): void {       // funcion void
  print("sin retorno");
  return;
}

let f: integer = factorial(5);
let inferido: integer = sinAnotacion();
procedimiento();
print("" + f + esPar(4) + esImpar(3) + inferido);
