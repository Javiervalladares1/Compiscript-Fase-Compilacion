"""Manejo de ambitos: anidamiento, sombreado, redeclaracion y visibilidad."""

from __future__ import annotations

from conftest import assert_error, assert_no_code, assert_ok, compile_code
from compiler.semantic.diagnostics import Code
from compiler.symbols.scope import ScopeKind


def _scope_kinds(result) -> set[str]:
    assert result.symbol_table is not None
    return {scope.kind.value for scope in result.symbol_table.all_scopes}


def test_variable_global_visible_en_todo_el_programa():
    assert_ok(
        """
        let global: integer = 1;
        function usar(): integer { return global; }
        { print(global); }
        """
    )


def test_variable_local_no_escapa_de_su_funcion():
    assert_error(
        """
        function f(): integer { let local: integer = 1; return local; }
        print(local);
        """,
        Code.UNDECLARED_IDENTIFIER,
    )


def test_bloques_anidados_crean_ambitos():
    result = assert_ok("{ let a: integer = 1; { let b: integer = 2; print(a + b); } }")
    assert ScopeKind.BLOCK.value in _scope_kinds(result)


def test_sombreado_valido_entre_ambitos():
    assert_ok(
        """
        let x: integer = 1;
        {
          let x: string = "sombra";
          print(x);
        }
        print(x + 1);
        """
    )


def test_redeclaracion_en_el_mismo_ambito_es_invalida():
    assert_error("let x: integer = 1; let x: integer = 2;", Code.DUPLICATE_DECLARATION)


def test_redeclaracion_de_constante_en_el_mismo_ambito():
    assert_error("const x: integer = 1; const x: integer = 2;", Code.DUPLICATE_DECLARATION)


def test_variable_no_declarada():
    assert_error("print(desconocida);", Code.UNDECLARED_IDENTIFIER)


def test_asignacion_a_variable_no_declarada():
    assert_error("desconocida = 1;", Code.ASSIGN_TO_UNDECLARED)


def test_parametros_duplicados():
    assert_error(
        "function f(a: integer, a: integer): integer { return a; }",
        Code.DUPLICATE_PARAMETER,
    )


def test_variable_fuera_de_alcance_tras_el_bloque():
    assert_error("{ let interna: integer = 1; } print(interna);", Code.UNDECLARED_IDENTIFIER)


def test_ambito_de_catch_es_independiente():
    result = assert_ok('try { print("a"); } catch (err) { print(err); }')
    assert ScopeKind.CATCH.value in _scope_kinds(result)


def test_identificador_de_catch_no_escapa():
    assert_error(
        'try { print("a"); } catch (err) { print(err); } print(err);',
        Code.UNDECLARED_IDENTIFIER,
    )


def test_ambito_de_foreach_es_independiente():
    result = assert_ok(
        "let xs: integer[] = [1, 2]; foreach (item in xs) { print(item); }"
    )
    assert ScopeKind.LOOP.value in _scope_kinds(result)


def test_variable_de_foreach_no_escapa():
    assert_error(
        "let xs: integer[] = [1]; foreach (item in xs) { print(item); } print(item);",
        Code.UNDECLARED_IDENTIFIER,
    )


def test_variable_del_for_no_escapa():
    assert_error(
        "for (let i: integer = 0; i < 3; i = i + 1) { print(i); } print(i);",
        Code.UNDECLARED_IDENTIFIER,
    )


def test_parametro_sombrea_variable_global():
    assert_ok(
        """
        let valor: string = "global";
        function f(valor: integer): integer { return valor + 1; }
        """
    )


def test_jerarquia_de_ambitos_se_construye():
    result = compile_code(
        """
        class C {
          let a: integer;
          function m(): integer { { let b: integer = 1; return b; } }
        }
        function f(): integer { while (true) { return 1; } return 0; }
        """
    )
    kinds = _scope_kinds(result)
    for expected in (
        ScopeKind.GLOBAL.value,
        ScopeKind.CLASS.value,
        ScopeKind.METHOD.value,
        ScopeKind.FUNCTION.value,
        ScopeKind.BLOCK.value,
        ScopeKind.LOOP.value,
    ):
        assert expected in kinds


def test_resolucion_local_antes_que_global():
    result = assert_ok(
        """
        let x: string = "global";
        function f(): integer { let x: integer = 5; return x; }
        """
    )
    assert result.symbol_table is not None


# --- uso antes de inicializar (SEM046) -------------------------------------


def test_uso_de_variable_declarada_sin_inicializar():
    """`let x: integer;` sin asignar no puede leerse todavia."""
    assert_error("let x: integer;\nprint(x);", Code.USE_BEFORE_INITIALIZATION)


def test_uso_en_expresion_de_variable_sin_inicializar():
    assert_error(
        "let x: integer;\nlet y: integer = x + 1;",
        Code.USE_BEFORE_INITIALIZATION,
    )


def test_tras_asignarla_la_variable_ya_puede_usarse():
    assert_ok("let x: integer;\nx = 5;\nprint(x);")


def test_la_variable_inicializada_en_la_declaracion_no_advierte():
    assert_no_code("let x: integer = 1;\nprint(x);", Code.USE_BEFORE_INITIALIZATION)
