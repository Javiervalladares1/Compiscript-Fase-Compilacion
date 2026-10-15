// Ambito global, bloques anidados y sombreado valido.
let compartida: integer = 1;

{
  let compartida: string = "sombra";   // sombreado valido en bloque interior
  print(compartida);
  {
    let compartida: boolean = true;    // otro nivel de sombreado
    print(compartida);
  }
}

function usaGlobal(): integer {
  return compartida + 1;               // acceso a la global desde una funcion
}

print(usaGlobal());
