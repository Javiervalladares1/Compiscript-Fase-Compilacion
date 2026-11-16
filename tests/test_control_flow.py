"""Control de flujo: condiciones, bucles, switch, break/continue y codigo muerto."""

from __future__ import annotations

from conftest import assert_error, assert_ok, codes, compile_code
from compiler.semantic.diagnostics import Code, Severity


# --- condiciones -----------------------------------------------------------


def test_condiciones_booleanas_validas():
    assert_ok(
        """
        let x: integer = 0;
        if (x < 3) { print("a"); } else { print("b"); }
        while (x < 3) { x = x + 1; }
        do { x = x - 1; } while (x > 0);
        for (let i: integer = 0; i < 2; i = i + 1) { print(i); }
        """
    )


def test_condicion_de_if_no_booleana():
    assert_error("if (1) { print(\"a\"); }", Code.NON_BOOLEAN_CONDITION)


def test_condicion_de_while_no_booleana():
    assert_error('while ("s") { print("a"); }', Code.NON_BOOLEAN_CONDITION)


def test_condicion_de_do_while_no_booleana():
    assert_error('do { print("a"); } while (3);', Code.NON_BOOLEAN_CONDITION)


def test_condicion_de_for_no_booleana():
    assert_error(
        "for (let i: integer = 0; i; i = i + 1) { print(i); }",
        Code.NON_BOOLEAN_CONDITION,
    )


def test_for_sin_condicion_es_valido():
    assert_ok("for (let i: integer = 0; ; i = i + 1) { break; }")


# --- break / continue ------------------------------------------------------


def test_break_y_continue_validos_en_bucle():
    assert_ok("while (true) { if (true) { continue; } break; }")


def test_break_fuera_de_bucle():
    assert_error("break;", Code.BREAK_OUTSIDE_LOOP)


def test_continue_fuera_de_bucle():
    assert_error("continue;", Code.CONTINUE_OUTSIDE_LOOP)


def test_break_dentro_de_switch_es_valido():
    """Extension documentada: `break` tambien es valido dentro de `switch`."""
    assert_ok(
        """
        let x: integer = 1;
        switch (x) {
          case 1: print("uno"); break;
          default: print("otro");
        }
        """
    )


def test_continue_dentro_de_switch_sin_bucle_es_invalido():
    assert_error(
        """
        let x: integer = 1;
        switch (x) {
          case 1: continue;
        }
        """,
        Code.CONTINUE_OUTSIDE_LOOP,
    )


def test_break_no_atraviesa_una_funcion_anidada():
    assert_error(
        """
        while (true) {
          function f(): integer { break; return 1; }
        }
        """,
        Code.BREAK_OUTSIDE_LOOP,
    )


# --- foreach ---------------------------------------------------------------


def test_foreach_sobre_arreglo():
    assert_ok("let xs: integer[] = [1, 2]; foreach (n in xs) { print(n + 1); }")


def test_foreach_infiere_el_tipo_del_elemento():
    assert_error(
        'let xs: integer[] = [1]; foreach (n in xs) { let s: string = n; }',
        Code.INCOMPATIBLE_ASSIGNMENT,
    )


def test_foreach_sobre_valor_no_iterable():
    assert_error("let x: integer = 5; foreach (n in x) { print(n); }", Code.FOREACH_NOT_ITERABLE)


def test_foreach_sobre_matriz_produce_filas():
    assert_ok(
        """
        let m: integer[][] = [[1, 2], [3]];
        foreach (fila in m) { print(fila[0]); }
        """
    )


def test_break_y_continue_validos_en_foreach():
    assert_ok(
        """
        let xs: integer[] = [1, 2, 3];
        foreach (n in xs) { if (n == 1) { continue; } break; }
        """
    )


# --- switch ----------------------------------------------------------------


def test_switch_con_selector_entero():
    assert_ok(
        """
        let x: integer = 2;
        switch (x) {
          case 1: print("uno");
          case 2: print("dos");
          default: print("otro");
        }
        """
    )


def test_switch_con_selector_string():
    assert_ok(
        """
        let s: string = "a";
        switch (s) { case "a": print("A"); default: print("otro"); }
        """
    )


def test_switch_no_exige_selector_booleano():
    result = compile_code("let x: integer = 1; switch (x) { case 1: print(\"uno\"); }")
    assert Code.NON_BOOLEAN_CONDITION not in codes(result)
    assert Code.INVALID_SWITCH_SUBJECT not in codes(result)


def test_case_incompatible_con_el_selector():
    assert_error(
        'let x: integer = 1; switch (x) { case "uno": print("no"); }',
        Code.INCOMPATIBLE_CASE,
    )


def test_case_literal_duplicado():
    assert_error(
        'let x: integer = 1; switch (x) { case 1: print("a"); case 1: print("b"); }',
        Code.DUPLICATE_CASE,
    )


def test_selector_no_comparable():
    assert_error(
        'let xs: integer[] = [1]; switch (xs) { case 1: print("no"); }',
        Code.INVALID_SWITCH_SUBJECT,
    )


def test_selector_invalido_no_encadena_errores_de_case():
    result = compile_code('let xs: integer[] = [1]; switch (xs) { case 1: print("no"); }')
    assert Code.INCOMPATIBLE_CASE not in codes(result)


# --- try / catch -----------------------------------------------------------


def test_try_catch_valido():
    assert_ok('try { print("a"); } catch (err) { print("error: " + err); }')


def test_identificador_de_catch_es_string():
    assert_ok('try { print("a"); } catch (err) { let m: string = err; }')


# --- codigo muerto ---------------------------------------------------------


def test_codigo_muerto_tras_return():
    result = compile_code('function f(): integer { return 1; print("x"); }')
    assert Code.UNREACHABLE_AFTER_RETURN in codes(result)
    assert result.success  # es solo una advertencia


def test_codigo_muerto_tras_break():
    result = compile_code('while (true) { break; print("x"); }')
    assert Code.UNREACHABLE_AFTER_BREAK in codes(result)


def test_codigo_muerto_tras_continue():
    result = compile_code(
        'for (let i: integer = 0; i < 2; i = i + 1) { continue; print("x"); }'
    )
    assert Code.UNREACHABLE_AFTER_CONTINUE in codes(result)


def test_bloque_inalcanzable_por_condicion_literal():
    result = compile_code('if (false) { print("x"); }')
    assert Code.UNREACHABLE_CONDITION in codes(result)


def test_advertencia_no_impide_la_compilacion():
    result = compile_code('function f(): integer { return 1; print("x"); }')
    assert result.success
    assert result.exit_code == 0


def test_modo_estricto_convierte_advertencias_en_fallo():
    result = compile_code('function f(): integer { return 1; print("x"); }', strict=True)
    assert not result.success
    assert result.exit_code == 1


def test_severidad_de_las_advertencias():
    result = compile_code('function f(): integer { return 1; print("x"); }')
    warnings = [d for d in result.diagnostics if d.severity is Severity.WARNING]
    assert warnings and all(d.code.startswith("SEM-W") for d in warnings)


def test_return_invalido_no_marca_codigo_muerto():
    """Un `return` fuera de funcion es un error, no debe encadenar avisos."""
    result = compile_code('return 1; print("no es codigo muerto");')
    assert Code.RETURN_OUTSIDE_FUNCTION in codes(result)
    assert Code.UNREACHABLE_AFTER_RETURN not in codes(result)
