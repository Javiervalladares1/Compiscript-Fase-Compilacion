"""Clases, objetos, miembros, constructores, `this` y herencia."""

from __future__ import annotations

from conftest import assert_error, assert_ok, codes, compile_code
from compiler.semantic.diagnostics import Code

BASE = """
class Animal {
  let nombre: string;
  let edad: integer;

  function constructor(nombre: string) {
    this.nombre = nombre;
    this.edad = 0;
  }

  function hablar(): string { return this.nombre + " hace ruido."; }
}
"""


# --- declaracion e instanciacion -------------------------------------------


def test_declaracion_de_clase():
    assert_ok(BASE)


def test_instanciacion_valida():
    assert_ok(BASE + 'let a: Animal = new Animal("Rex");')


def test_clase_inexistente():
    assert_error("let x = new NoExiste();", Code.UNDECLARED_CLASS)


def test_new_sobre_algo_que_no_es_clase():
    assert_error(
        "function f(): integer { return 1; } let x = new f();",
        Code.NEW_ON_NON_CLASS,
    )


def test_clase_no_es_un_valor():
    assert_error(BASE + "let x = Animal;", Code.NOT_A_VALUE)


def test_uso_de_la_clase_como_tipo_antes_de_declararla():
    assert_ok('let a: Animal = null;' + BASE)


# --- constructor -----------------------------------------------------------


def test_constructor_con_argumentos_correctos():
    assert_ok(BASE + 'let a: Animal = new Animal("Rex");')


def test_constructor_con_numero_incorrecto_de_argumentos():
    assert_error(BASE + "let a: Animal = new Animal();", Code.ARGUMENT_COUNT_MISMATCH)


def test_constructor_con_tipo_incorrecto_de_argumento():
    assert_error(BASE + "let a: Animal = new Animal(1);", Code.ARGUMENT_TYPE_MISMATCH)


def test_clase_sin_constructor_no_admite_argumentos():
    assert_error(
        "class C { let a: integer; } let c: C = new C(1);",
        Code.CONSTRUCTOR_MISUSE,
    )


def test_clase_sin_constructor_se_instancia_sin_argumentos():
    assert_ok("class C { let a: integer; } let c: C = new C();")


def test_constructor_no_puede_devolver_valor():
    assert_error(
        "class C { let a: integer; function constructor() { return 1; } }",
        Code.RETURN_VALUE_IN_VOID,
    )


def test_constructor_duplicado():
    assert_error(
        """
        class C {
          function constructor() { print("a"); }
          function constructor() { print("b"); }
        }
        """,
        Code.DUPLICATE_MEMBER,
    )


# --- miembros --------------------------------------------------------------


def test_acceso_a_atributo_existente():
    assert_ok(BASE + 'let a: Animal = new Animal("Rex"); let n: string = a.nombre;')


def test_acceso_a_atributo_inexistente():
    assert_error(
        BASE + 'let a: Animal = new Animal("Rex"); print(a.inexistente);',
        Code.UNKNOWN_PROPERTY,
    )


def test_llamada_a_metodo_existente():
    assert_ok(BASE + 'let a: Animal = new Animal("Rex"); print(a.hablar());')


def test_llamada_a_metodo_inexistente():
    assert_error(
        BASE + 'let a: Animal = new Animal("Rex"); a.noExiste();',
        Code.UNKNOWN_METHOD,
    )


def test_asignacion_a_atributo_con_tipo_incompatible():
    assert_error(
        BASE + 'let a: Animal = new Animal("Rex"); a.edad = "no";',
        Code.INCOMPATIBLE_ASSIGNMENT,
    )


def test_asignacion_a_atributo_valida():
    assert_ok(BASE + 'let a: Animal = new Animal("Rex"); a.edad = 5;')


def test_acceso_a_propiedad_sobre_no_objeto():
    assert_error("let x: integer = 1; print(x.campo);", Code.PROPERTY_ON_NON_OBJECT)


def test_miembros_duplicados():
    assert_error(
        """
        class C {
          let a: integer;
          let a: string;
        }
        """,
        Code.DUPLICATE_MEMBER,
    )


def test_metodo_y_atributo_con_el_mismo_nombre():
    assert_error(
        """
        class C {
          let a: integer;
          function a(): integer { return 1; }
        }
        """,
        Code.DUPLICATE_MEMBER,
    )


def test_tipo_de_retorno_de_un_metodo_se_infiere_en_la_llamada():
    assert_error(
        BASE + 'let a: Animal = new Animal("Rex"); let n: integer = a.hablar();',
        Code.INCOMPATIBLE_ASSIGNMENT,
    )


# --- this ------------------------------------------------------------------


def test_this_valido_dentro_de_un_metodo():
    assert_ok(BASE)


def test_this_fuera_de_una_clase():
    assert_error("this.campo = 1;", Code.THIS_OUTSIDE_CLASS)


def test_this_en_funcion_global_es_invalido():
    assert_error(
        "function f(): integer { return this.x; }",
        Code.THIS_OUTSIDE_CLASS,
    )


def test_this_tiene_el_tipo_de_la_clase():
    assert_error(
        """
        class C {
          let a: integer;
          function m(): integer { return this.noExiste; }
        }
        """,
        Code.UNKNOWN_PROPERTY,
    )


# --- herencia --------------------------------------------------------------


def test_herencia_simple():
    assert_ok(BASE + "class Perro : Animal { }")


def test_clase_base_inexistente():
    assert_error("class C : NoExiste { }", Code.UNKNOWN_BASE_CLASS)


def test_ciclo_de_herencia():
    assert_error("class A : B { } class B : A { }", Code.INHERITANCE_CYCLE)


def test_acceso_a_miembro_heredado():
    assert_ok(
        BASE
        + """
        class Perro : Animal { }
        let p: Perro = new Perro("Rex");
        print(p.nombre);
        print(p.hablar());
        """
    )


def test_constructor_heredado():
    assert_ok(
        BASE
        + """
        class Perro : Animal { }
        let p: Perro = new Perro("Rex");
        """
    )


def test_constructor_heredado_valida_argumentos():
    assert_error(
        BASE + 'class Perro : Animal { } let p: Perro = new Perro();',
        Code.ARGUMENT_COUNT_MISMATCH,
    )


def test_uso_de_this_con_atributo_heredado():
    assert_ok(
        BASE
        + """
        class Perro : Animal {
          function hablar(): string { return this.nombre + " ladra."; }
        }
        """
    )


def test_sobrescritura_compatible():
    assert_ok(
        BASE
        + """
        class Perro : Animal {
          function hablar(): string { return "guau"; }
        }
        """
    )


def test_sobrescritura_con_tipo_de_retorno_incompatible():
    assert_error(
        BASE + "class Perro : Animal { function hablar(): integer { return 1; } }",
        Code.INCOMPATIBLE_OVERRIDE,
    )


def test_sobrescritura_con_aridad_incompatible():
    assert_error(
        BASE + 'class Perro : Animal { function hablar(x: integer): string { return "g"; } }',
        Code.INCOMPATIBLE_OVERRIDE,
    )


def test_subclase_asignable_a_la_clase_base():
    assert_ok(
        BASE
        + """
        class Perro : Animal { }
        let p: Perro = new Perro("Rex");
        let a: Animal = p;
        """
    )


def test_clase_base_no_asignable_a_la_subclase():
    assert_error(
        BASE
        + """
        class Perro : Animal { }
        let a: Animal = new Animal("Generico");
        let p: Perro = a;
        """,
        Code.INCOMPATIBLE_ASSIGNMENT,
    )


def test_herencia_de_tres_niveles():
    assert_ok(
        BASE
        + """
        class Perro : Animal { }
        class Cachorro : Perro { }
        let c: Cachorro = new Cachorro("Bebe");
        print(c.nombre + c.hablar());
        """
    )


def test_registro_de_clases_en_la_tabla():
    result = compile_code(BASE + "class Perro : Animal { }")
    assert result.symbol_table is not None
    perro = result.symbol_table.classes.get("Perro")
    assert perro is not None and perro.base_name == "Animal"
    assert result.symbol_table.classes.is_subclass("Perro", "Animal")
    assert not result.symbol_table.classes.is_subclass("Animal", "Perro")
    assert result.symbol_table.classes.lookup_method("Perro", "hablar") is not None
    assert result.symbol_table.classes.lookup_field("Perro", "nombre") is not None
    assert result.symbol_table.classes.lookup_constructor("Perro") is not None


def test_ciclo_de_herencia_no_cuelga_el_analisis():
    result = compile_code("class A : B { } class B : C { } class C : A { }")
    assert Code.INHERITANCE_CYCLE in codes(result)
