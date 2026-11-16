"""Funciones: firmas, llamadas, retornos, recursion, anidamiento y closures."""

from __future__ import annotations

from conftest import assert_error, assert_ok, compile_code
from compiler.semantic.diagnostics import Code
from compiler.symbols.symbols import FunctionSymbol


def _function(result, name: str) -> FunctionSymbol:
    assert result.symbol_table is not None
    for scope in result.symbol_table.all_scopes:
        symbol = scope.lookup_local(name)
        if isinstance(symbol, FunctionSymbol):
            return symbol
    raise AssertionError(f"No se encontro la funcion '{name}'")


# --- llamadas --------------------------------------------------------------


def test_llamada_correcta():
    assert_ok(
        """
        function suma(a: integer, b: integer): integer { return a + b; }
        let x: integer = suma(1, 2);
        """
    )


def test_numero_incorrecto_de_argumentos():
    assert_error(
        """
        function suma(a: integer, b: integer): integer { return a + b; }
        let x: integer = suma(1);
        """,
        Code.ARGUMENT_COUNT_MISMATCH,
    )


def test_tipo_incorrecto_de_argumento():
    assert_error(
        """
        function suma(a: integer, b: integer): integer { return a + b; }
        let x: integer = suma(1, "dos");
        """,
        Code.ARGUMENT_TYPE_MISMATCH,
    )


def test_promocion_de_argumento_integer_a_float():
    assert_ok(
        """
        function escalar(v: float): float { return v * 2.0; }
        let x: float = escalar(3);
        """
    )


def test_funcion_no_declarada():
    assert_error("let x: integer = noExiste(1);", Code.UNDECLARED_FUNCTION)


def test_variable_no_es_invocable():
    assert_error("let v: integer = 1; let x: integer = v(1);", Code.NOT_CALLABLE)


def test_clase_no_es_invocable():
    assert_error(
        "class C { let a: integer; } let x = C();",
        Code.NOT_CALLABLE,
    )


def test_no_se_puede_multiplicar_una_funcion():
    assert_error(
        """
        function f(): integer { return 1; }
        let x = f * 2;
        """,
        Code.NON_NUMERIC_OPERAND,
    )


# --- retornos --------------------------------------------------------------


def test_retorno_correcto():
    assert_ok("function f(): string { return \"ok\"; }")


def test_retorno_incompatible():
    assert_error(
        "function f(): integer { return \"no\"; }",
        Code.INCOMPATIBLE_RETURN,
    )


def test_return_fuera_de_funcion():
    assert_error("return 1;", Code.RETURN_OUTSIDE_FUNCTION)


def test_funcion_sin_retorno_en_todos_los_caminos():
    assert_error(
        """
        function f(n: integer): integer {
          if (n > 0) { return 1; }
        }
        """,
        Code.MISSING_RETURN,
    )


def test_funcion_con_retorno_en_ambas_ramas_es_valida():
    assert_ok(
        """
        function f(n: integer): integer {
          if (n > 0) { return 1; } else { return 2; }
        }
        """
    )


def test_funcion_void_sin_retorno_es_valida():
    assert_ok("function f(): void { print(\"hola\"); }")


def test_funcion_void_con_retorno_vacio_es_valida():
    assert_ok("function f(): void { return; }")


def test_funcion_void_no_devuelve_valor():
    assert_error("function f(): void { return 1; }", Code.RETURN_VALUE_IN_VOID)


def test_return_sin_valor_en_funcion_tipada():
    assert_error("function f(): integer { return; }", Code.INCOMPATIBLE_RETURN)


def test_inferencia_de_retorno_sin_anotacion():
    result = assert_ok("function f() { return 1 + 1; }")
    assert _function(result, "f").return_type.name == "integer"


def test_inferencia_de_retorno_void():
    result = assert_ok("function f() { print(\"hola\"); }")
    assert _function(result, "f").return_type.name == "void"


def test_inferencia_de_retorno_con_tipo_comun():
    result = assert_ok(
        """
        function f(c: boolean) {
          if (c) { return 1; }
          return 2.5;
        }
        """
    )
    assert _function(result, "f").return_type.name == "float"


def test_uso_de_expresion_void_como_valor():
    assert_error(
        """
        function f(): void { print("x"); }
        let x: integer = f();
        """,
        Code.VOID_AS_VALUE,
    )


# --- declaraciones ---------------------------------------------------------


def test_funcion_duplicada():
    assert_error(
        """
        function f(): integer { return 1; }
        function f(): integer { return 2; }
        """,
        Code.DUPLICATE_DECLARATION,
    )


def test_funcion_usada_antes_de_su_declaracion():
    assert_ok(
        """
        let x: integer = despues(1);
        function despues(n: integer): integer { return n; }
        """
    )


def test_parametro_sin_anotacion_de_tipo():
    assert_error("function f(a): integer { return 1; }", Code.CANNOT_INFER_TYPE)


# --- recursion -------------------------------------------------------------


def test_recursion_directa():
    assert_ok(
        """
        function factorial(n: integer): integer {
          if (n <= 1) { return 1; }
          return n * factorial(n - 1);
        }
        """
    )


def test_recursion_mutua():
    assert_ok(
        """
        function par(n: integer): boolean {
          if (n == 0) { return true; }
          return impar(n - 1);
        }
        function impar(n: integer): boolean {
          if (n == 0) { return false; }
          return par(n - 1);
        }
        """
    )


# --- anidamiento y closures ------------------------------------------------


def test_funcion_anidada():
    assert_ok(
        """
        function outer(): integer {
          function inner(): integer { return 1; }
          return inner();
        }
        """
    )


def test_funcion_anidada_no_es_visible_fuera():
    assert_error(
        """
        function outer(): integer {
          function inner(): integer { return 1; }
          return inner();
        }
        let x: integer = inner();
        """,
        Code.UNDECLARED_FUNCTION,
    )


def test_closure_registra_las_variables_capturadas():
    result = assert_ok(
        """
        function outer(x: integer): integer {
          let offset: integer = 1;
          function inner(): integer { return x + offset; }
          return inner();
        }
        """
    )
    inner = _function(result, "inner")
    assert set(inner.captures) == {"x", "offset"}


def test_closure_marca_la_variable_como_capturada():
    result = assert_ok(
        """
        function outer(x: integer): integer {
          function inner(): integer { return x; }
          return inner();
        }
        """
    )
    outer_scope = _function(result, "outer").body_scope
    assert outer_scope is not None
    assert outer_scope.lookup_local("x").captured is True


def test_las_globales_no_se_cuentan_como_capturas():
    result = assert_ok(
        """
        let global: integer = 1;
        function f(): integer { return global; }
        """
    )
    assert _function(result, "f").captures == []


def test_recursion_mutua_entre_funciones_anidadas():
    assert_ok(
        """
        function outer(n: integer): boolean {
          function par(k: integer): boolean {
            if (k == 0) { return true; }
            return impar(k - 1);
          }
          function impar(k: integer): boolean {
            if (k == 0) { return false; }
            return par(k - 1);
          }
          return par(n);
        }
        """
    )


def test_firma_registrada_en_la_tabla():
    result = compile_code("function suma(a: integer, b: float): float { return a + b; }")
    symbol = _function(result, "suma")
    assert symbol.arity == 2
    assert [p.name for p in symbol.parameters] == ["a", "b"]
    assert [p.type.name for p in symbol.parameters] == ["integer", "float"]
    assert symbol.return_type.name == "float"
    assert symbol.signature == "suma(a: integer, b: float): float"
