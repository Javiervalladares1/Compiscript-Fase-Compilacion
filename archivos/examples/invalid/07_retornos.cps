// @expect SEM024 SEM023 SEM025 SEM026
// Errores relacionados con 'return'.
return 1;                              // fuera de cualquier funcion

function tipoMalo(): integer {
  return "no es entero";
}

function faltaRetorno(): integer {
  let a: integer = 1;
}

function esVoid(): void {
  return 5;
}
