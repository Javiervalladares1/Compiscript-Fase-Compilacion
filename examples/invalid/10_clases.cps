// @expect SEM006 SEM039 SEM041 SEM034 SEM035 SEM037 SEM003
// Errores de clases, miembros, herencia y 'this'.
class Base {
  let atributo: integer;
  function metodo(): string { return "base"; }
  function metodo(): string { return "duplicado"; }
}

class SinBase : NoExiste { }

class Mala : Base {
  function metodo(): integer { return 1; }     // firma incompatible
}

let base: Base = new Base();
print(base.inexistente);
base.metodoInexistente();

this.atributo = 1;                             // 'this' fuera de una clase
let objeto = new ClaseInexistente();
