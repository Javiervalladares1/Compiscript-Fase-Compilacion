// Salida: 12, 14. Las dos llamadas comparten la misma variable capturada.
function contador(inicio: integer, paso: integer): integer {
  let actual: integer = inicio;
  function siguiente(): integer {
    actual = actual + paso;
    return actual;
  }
  print(siguiente());
  return siguiente();
}
print(contador(10, 2));
