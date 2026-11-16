// Funciones anidadas que capturan variables del entorno donde se definen.
function outer(x: integer): integer {
  let offset: integer = 1;

  function inner(): integer {
    return x + offset;                 // captura x y offset
  }

  return inner();
}

function contador(inicio: integer): integer {
  let actual: integer = inicio;

  function siguiente(): integer {
    return actual + 1;                 // captura actual
  }

  return siguiente();
}

print("" + outer(10) + contador(5));
