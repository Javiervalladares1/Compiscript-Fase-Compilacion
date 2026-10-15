"""Expresiones compuestas: acceso encadenado y asignaciones como expresion.

Cubre las dos construcciones que la gramatica permite anidar sin limite:

* ``leftHandSide (suffixOp)*`` — cadenas de ``()``, ``[]`` y ``.``;
* ``assignmentExpr`` — asignaciones que devuelven valor y se encadenan.
"""

from __future__ import annotations

from conftest import assert_error, assert_ok, compile_code
from compiler.semantic.diagnostics import Code

# Base reutilizada por las pruebas de acceso encadenado.
CAJA = """
class Caja {
    let items: integer[];
    let etiqueta: string;

    function constructor() {
        this.items = [1, 2, 3];
        this.etiqueta = "c";
    }

    function misma(): Caja { return this; }
    function valor(): integer { return 42; }
}

function crear(): Caja { return new Caja(); }
"""


# --- acceso encadenado: llamada -> propiedad -> indice -> llamada ----------


def test_cadena_llamada_metodo_llamada():
    assert_ok(CAJA + "let n: integer = crear().misma().valor();")


def test_cadena_llamada_propiedad_indice():
    assert_ok(CAJA + "let n: integer = crear().items[0];")


def test_cadena_larga_de_sufijos():
    assert_ok(CAJA + "let n: integer = crear().misma().misma().items[2];")


def test_la_cadena_propaga_el_tipo_final():
    """El tipo del ultimo sufijo es el que se comprueba en la asignacion."""
    result = assert_error(
        CAJA + "let s: string = crear().misma().valor();",
        Code.INCOMPATIBLE_ASSIGNMENT,
    )
    diagnostic = result.errors[0]
    assert diagnostic.expected_type == "string"
    assert diagnostic.actual_type == "integer"


def test_propiedad_inexistente_en_medio_de_la_cadena():
    assert_error(CAJA + "let n = crear().misma().noExiste;", Code.UNKNOWN_PROPERTY)


def test_metodo_inexistente_en_medio_de_la_cadena():
    assert_error(CAJA + "let n = crear().misma().noExiste();", Code.UNKNOWN_METHOD)


def test_indexar_el_resultado_no_indexable_de_una_cadena():
    assert_error(CAJA + "let n = crear().valor()[0];", Code.NOT_INDEXABLE)


def test_indice_no_entero_en_una_cadena():
    assert_error(CAJA + 'let n = crear().items["x"];', Code.NON_INTEGER_INDEX)


def test_la_cadena_no_encadena_errores_derivados():
    """Un unico fallo en la cadena produce un unico diagnostico."""
    result = compile_code(CAJA + "let n = crear().misma().noExiste;")
    assert result.error_count == 1


# --- asignacion como expresion --------------------------------------------


def test_asignacion_encadenada():
    assert_ok(
        """
        let a: integer = 0;
        let b: integer = 0;
        a = b = 10;
        """
    )


def test_la_asignacion_devuelve_el_tipo_asignado():
    assert_ok(
        """
        let b: integer = 0;
        let c: integer = (b = 10);
        """
    )


def test_el_tipo_devuelto_por_la_asignacion_se_comprueba():
    assert_error(
        """
        let b: integer = 0;
        let c: string = (b = 10);
        """,
        Code.INCOMPATIBLE_ASSIGNMENT,
    )


def test_asignacion_encadenada_con_tipo_incompatible():
    assert_error(
        """
        let a: integer = 0;
        let b: string = "";
        a = b = "x";
        """,
        Code.INCOMPATIBLE_ASSIGNMENT,
    )


def test_no_se_puede_asignar_a_una_constante_dentro_de_una_expresion():
    """La mutabilidad se comprueba tambien en la forma de expresion."""
    assert_error(
        """
        const C: integer = 1;
        let a: integer = 0;
        a = C = 5;
        """,
        Code.CONST_REASSIGNMENT,
    )


def test_asignacion_a_identificador_no_declarado_en_expresion():
    """El destino no declarado usa SEM009, mas especifico que SEM001."""
    assert_error(
        """
        let a: integer = 0;
        a = noDeclarada = 1;
        """,
        Code.ASSIGN_TO_UNDECLARED,
    )


# --- asignacion de propiedades --------------------------------------------


def test_asignacion_de_propiedad_valida():
    assert_ok(
        """
        class A { let x: integer; }
        let o: A = new A();
        o.x = 5;
        """
    )


def test_asignacion_de_propiedad_con_tipo_incompatible():
    assert_error(
        """
        class A { let x: integer; }
        let o: A = new A();
        o.x = "s";
        """,
        Code.INCOMPATIBLE_ASSIGNMENT,
    )


def test_asignacion_a_propiedad_inexistente():
    assert_error(
        """
        class A { let x: integer; }
        let o: A = new A();
        o.noExiste = 5;
        """,
        Code.UNKNOWN_PROPERTY,
    )


def test_asignacion_de_propiedad_sobre_un_no_objeto():
    assert_error(
        """
        let n: integer = 1;
        n.x = 5;
        """,
        Code.PROPERTY_ON_NON_OBJECT,
    )
