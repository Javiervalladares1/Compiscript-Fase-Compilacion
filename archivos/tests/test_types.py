"""Sistema de tipos: aritmetica, float, concatenacion, logica y comparaciones."""

from __future__ import annotations

import pytest

from conftest import assert_error, assert_ok, compile_code
from compiler.semantic.diagnostics import Code
from compiler.types import compatibility as compat
from compiler.types.types import BOOLEAN, FLOAT, INTEGER, NULL, STRING, ArrayType, ClassType


# --- aritmetica y float ----------------------------------------------------


def test_suma_de_enteros_produce_integer():
    result = assert_ok("let x: integer = 1 + 2;")
    assert result.ast is not None


def test_operaciones_con_float():
    assert_ok(
        """
        let a: float = 1.5;
        let b: float = a * 2.0;
        let c: float = a - 0.5;
        let d: float = a / 2.0;
        """
    )


def test_promocion_de_integer_a_float():
    assert_ok(
        """
        let entero: integer = 3;
        let flotante: float = entero;
        let mezcla: float = entero + 1.5;
        """
    )


def test_float_no_se_degrada_a_integer():
    assert_error("let x: integer = 1.5;", Code.INCOMPATIBLE_ASSIGNMENT)


def test_float_literal_no_se_lexa_como_dos_tokens():
    result = assert_ok("let x: float = 10.5;")
    assert not result.syntax_diagnostics


def test_division_entera_produce_integer():
    assert_ok("let x: integer = 7 / 2;")


def test_division_con_float_produce_float():
    assert_error("let x: integer = 7 / 2.0;", Code.INCOMPATIBLE_ASSIGNMENT)


def test_modulo_requiere_numericos():
    assert_error('let x: integer = "a" % 2;', Code.NON_NUMERIC_OPERAND)


# --- concatenacion ---------------------------------------------------------


def test_concatenacion_string_mas_integer():
    assert_ok('let x: string = "n=" + 5;')


def test_concatenacion_integer_mas_string():
    assert_ok('let x: string = 5 + "=n";')


def test_concatenacion_con_float_y_boolean():
    assert_ok('let x: string = "v=" + 1.5 + true;')


def test_concatenacion_con_arreglo_es_invalida():
    assert_error('let x: string = "v=" + [1, 2];', Code.INVALID_CONCATENATION)


def test_resta_con_string_es_invalida():
    assert_error('let x: integer = "a" - 1;', Code.NON_NUMERIC_OPERAND)


# --- logica ----------------------------------------------------------------


def test_operaciones_logicas_validas():
    assert_ok("let x: boolean = true && (false || !true);")


def test_operacion_logica_con_entero_es_invalida():
    assert_error("let x: boolean = 1 && true;", Code.NON_BOOLEAN_OPERAND)


def test_negacion_de_entero_es_invalida():
    assert_error("let x: boolean = !1;", Code.NON_BOOLEAN_OPERAND)


def test_menos_unario_sobre_string_es_invalido():
    assert_error('let x: integer = -"a";', Code.NON_NUMERIC_OPERAND)


# --- comparaciones ---------------------------------------------------------


def test_comparacion_numerica_mixta_es_valida():
    assert_ok("let x: boolean = 1 < 2.5;")


def test_comparacion_relacional_entre_cadenas_es_invalida():
    assert_error('let x: boolean = "a" < "b";', Code.INVALID_RELATIONAL)


def test_igualdad_entre_integer_y_float_es_valida():
    assert_ok("let x: boolean = 1 == 1.0;")


def test_igualdad_entre_tipos_incompatibles():
    assert_error('let x: boolean = 1 == "uno";', Code.INVALID_EQUALITY)


# --- asignaciones y constantes --------------------------------------------


def test_asignacion_compatible():
    assert_ok("let x: integer = 1; x = 2;")


def test_asignacion_incompatible():
    assert_error("let x: integer = 1; x = false;", Code.INCOMPATIBLE_ASSIGNMENT)


def test_constante_sin_inicializar():
    assert_error("const x: integer;", Code.CONST_WITHOUT_INITIALIZER)


def test_constante_no_se_reasigna():
    assert_error("const x: integer = 1; x = 2;", Code.CONST_REASSIGNMENT)


def test_declaracion_sin_tipo_ni_inicializador():
    assert_error("let x;", Code.CANNOT_INFER_TYPE)


def test_inferencia_desde_el_inicializador():
    result = assert_ok("let x = 1 + 2; let y: integer = x;")
    assert result.symbol_table is not None


# --- ternario --------------------------------------------------------------


def test_ternario_valido_con_tipo_comun():
    assert_ok("let x: float = true ? 1 : 2.5;")


def test_ternario_con_condicion_no_booleana():
    assert_error("let x = 1 ? 1 : 2;", Code.NON_BOOLEAN_CONDITION)


def test_ternario_con_ramas_incompatibles():
    assert_error('let x = true ? 1 : "uno";', Code.INCOMPATIBLE_TERNARY)


# --- null ------------------------------------------------------------------


def test_null_en_tipos_de_referencia():
    assert_ok(
        """
        class C { let a: integer; }
        let objeto: C = null;
        let lista: integer[] = null;
        let texto: string = null;
        """
    )


def test_null_no_es_asignable_a_valor():
    result = compile_code(
        """
        let a: integer = null;
        let b: float = null;
        let c: boolean = null;
        """
    )
    assert result.codes().count(Code.INCOMPATIBLE_ASSIGNMENT) == 3


def test_comparacion_con_null_en_referencias():
    assert_ok(
        """
        class C { let a: integer; }
        let objeto: C = null;
        let x: boolean = objeto == null;
        let y: boolean = objeto != null;
        """
    )


def test_aritmetica_con_null_es_invalida():
    assert_error("let x = null + 1;", Code.NULL_OPERATION)


# --- API del sistema de tipos ---------------------------------------------


@pytest.mark.parametrize(
    "source,target,expected",
    [
        (INTEGER, FLOAT, True),
        (FLOAT, INTEGER, False),
        (INTEGER, INTEGER, True),
        (NULL, ClassType("C"), True),
        (NULL, INTEGER, False),
        (NULL, ArrayType(INTEGER), True),
        (ArrayType(INTEGER), ArrayType(FLOAT), False),
        (BOOLEAN, STRING, False),
    ],
)
def test_is_assignable(source, target, expected):
    assert compat.is_assignable(source, target) is expected


def test_common_numeric_type():
    assert compat.common_numeric_type(INTEGER, INTEGER) == INTEGER
    assert compat.common_numeric_type(INTEGER, FLOAT) == FLOAT
    assert compat.common_numeric_type(FLOAT, FLOAT) == FLOAT


def test_predicados_de_tipos():
    assert compat.is_numeric(INTEGER) and compat.is_numeric(FLOAT)
    assert not compat.is_numeric(STRING)
    assert compat.is_boolean(BOOLEAN)
    assert compat.is_reference(ClassType("C"))
    assert compat.is_reference(ArrayType(INTEGER))
    assert compat.is_reference(STRING)
    assert not compat.is_reference(INTEGER)


def test_common_array_element_type():
    assert compat.common_array_element_type([INTEGER, FLOAT]) == FLOAT
    assert compat.common_array_element_type([INTEGER, STRING]) is None
    assert compat.common_array_element_type([]) is not None  # unknown


def test_is_comparable():
    assert compat.is_comparable(INTEGER, FLOAT, "<")
    assert not compat.is_comparable(STRING, STRING, "<")
    assert compat.is_comparable(INTEGER, FLOAT, "==")
    assert compat.is_comparable(NULL, ClassType("C"), "==")
    assert not compat.is_comparable(NULL, INTEGER, "==")


def test_nombres_de_tipos_de_arreglo():
    assert ArrayType(ArrayType(INTEGER)).name == "integer[][]"
    assert ArrayType(ArrayType(INTEGER)).dimensions == 2
    assert ArrayType(ArrayType(INTEGER)).base_element == INTEGER
