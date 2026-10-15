"""Arreglos: homogeneidad, dimensiones, indexacion y asignaciones."""

from __future__ import annotations

from conftest import assert_error, assert_ok, codes, compile_code
from compiler.semantic.diagnostics import Code


def test_arreglo_homogeneo():
    assert_ok("let xs: integer[] = [1, 2, 3];")


def test_arreglo_heterogeneo():
    assert_error('let xs = [1, "dos", true];', Code.HETEROGENEOUS_ARRAY)


def test_arreglo_con_promocion_numerica_es_homogeneo():
    assert_ok("let xs: float[] = [1, 2.5, 3];")


def test_arreglo_vacio_con_contexto():
    assert_ok("let xs: integer[] = [];")


def test_arreglo_vacio_sin_contexto():
    assert_error("let xs = [];", Code.UNRESOLVED_EMPTY_ARRAY)


def test_arreglo_vacio_anidado_con_contexto():
    assert_ok("let m: integer[][] = [];")


def test_matriz():
    assert_ok("let m: integer[][] = [[1, 2], [3, 4]];")


def test_matriz_con_filas_incompatibles():
    """Las filas 'integer[]' y 'string[]' no tienen un tipo comun."""
    assert_error('let m: integer[][] = [[1, 2], ["a"]];', Code.HETEROGENEOUS_ARRAY)


def test_matriz_con_fila_de_tipo_equivocado():
    assert_error('let m: integer[][] = [["a"], ["b"]];', Code.INCOMPATIBLE_ASSIGNMENT)


def test_matriz_con_promocion_en_las_filas():
    assert_ok("let m: float[][] = [[1, 2], [3]];")


def test_dimensiones_incompatibles():
    assert_error(
        "let m: integer[][] = [[1]]; let xs: integer[] = m;",
        Code.INCOMPATIBLE_ASSIGNMENT,
    )


def test_indice_entero():
    assert_ok("let xs: integer[] = [1, 2]; let a: integer = xs[0];")


def test_indice_no_entero():
    assert_error('let xs: integer[] = [1]; let a: integer = xs["0"];', Code.NON_INTEGER_INDEX)


def test_indice_float_es_invalido():
    assert_error("let xs: integer[] = [1]; let a: integer = xs[1.5];", Code.NON_INTEGER_INDEX)


def test_acceso_a_valor_no_indexable():
    assert_error("let x: integer = 1; let a: integer = x[0];", Code.NOT_INDEXABLE)


def test_acceso_encadenado_en_matriz():
    assert_ok(
        """
        let m: integer[][] = [[1, 2], [3, 4]];
        let fila: integer[] = m[0];
        let celda: integer = m[0][1];
        """
    )


def test_indice_literal_fuera_de_rango_es_advertencia():
    result = compile_code("let xs: integer[] = [1, 2, 3]; print(xs[7]);")
    assert Code.INDEX_OUT_OF_RANGE in codes(result)
    assert result.success  # no impide la compilacion


def test_indice_literal_dentro_de_rango_no_advierte():
    result = compile_code("let xs: integer[] = [1, 2, 3]; print(xs[2]);")
    assert Code.INDEX_OUT_OF_RANGE not in codes(result)


def test_indice_variable_no_produce_falsos_positivos():
    result = compile_code(
        """
        let xs: integer[] = [1, 2, 3];
        for (let i: integer = 0; i < 10; i = i + 1) { print(xs[i]); }
        """
    )
    assert Code.INDEX_OUT_OF_RANGE not in codes(result)


def test_reasignacion_invalida_el_tamano_conocido():
    result = compile_code(
        """
        let xs: integer[] = [1, 2, 3];
        xs = [1, 2, 3, 4, 5, 6, 7, 8];
        print(xs[7]);
        """
    )
    assert Code.INDEX_OUT_OF_RANGE not in codes(result)


def test_asignacion_a_posicion_de_arreglo():
    assert_ok("let xs: integer[] = [1, 2]; xs[0] = 9;")


def test_asignacion_a_posicion_con_tipo_incompatible():
    assert_error('let xs: integer[] = [1]; xs[0] = "a";', Code.INCOMPATIBLE_ASSIGNMENT)


def test_asignacion_en_matriz():
    assert_ok("let m: integer[][] = [[1, 2]]; m[0][1] = 5;")


def test_funcion_que_devuelve_un_arreglo():
    assert_ok(
        """
        function multiplos(n: integer): integer[] { return [n, n * 2]; }
        let xs: integer[] = multiplos(3);
        let primero: integer = xs[0];
        """
    )


def test_arreglo_de_objetos():
    assert_ok(
        """
        class C { let a: integer; }
        let objetos: C[] = [new C(), new C()];
        let primero: C = objetos[0];
        """
    )


def test_arreglo_de_cadenas_concatenado():
    assert_ok('let xs: string[] = ["a", "b"]; let s: string = xs[0] + xs[1];')


def test_arreglos_son_invariantes():
    assert_error(
        "let xs: integer[] = [1, 2]; let ys: float[] = xs;",
        Code.INCOMPATIBLE_ASSIGNMENT,
    )


def test_foreach_sobre_arreglo_de_arreglos():
    assert_ok(
        """
        let m: integer[][] = [[1], [2]];
        foreach (fila in m) { foreach (n in fila) { print(n); } }
        """
    )


def test_tipo_de_arreglo_en_la_tabla_de_simbolos():
    result = compile_code("let m: integer[][] = [[1]];")
    assert result.symbol_table is not None
    symbol = result.symbol_table.global_scope.lookup_local("m")
    assert symbol is not None and symbol.type.name == "integer[][]"
