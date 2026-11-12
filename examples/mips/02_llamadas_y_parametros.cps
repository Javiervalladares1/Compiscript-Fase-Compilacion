// Salida: 21, 55, 13. Hay argumentos en registros y en pila.
function sumar6(a: integer, b: integer, c: integer,
                d: integer, e: integer, f: integer): integer {
  return a + b + c + d + e + f;
}

function fibonacci(n: integer): integer {
  if (n <= 1) { return n; }
  return fibonacci(n - 1) + fibonacci(n - 2);
}

function doble(n: integer): integer { return n * 2; }
function combinar(n: integer): integer {
  let antes: integer = n + 1;
  let resultado: integer = doble(n);
  return antes + resultado;
}

print(sumar6(1, 2, 3, 4, 5, 6));
print(fibonacci(10));
print(combinar(4));
