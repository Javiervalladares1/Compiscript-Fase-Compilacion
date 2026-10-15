"""CLI (`program/Driver.py`), API `compile_source` y manejo de errores sintacticos."""

from __future__ import annotations

import io
import json
import subprocess
import sys

from conftest import REPO_ROOT, SAMPLE_PROGRAM, compile_code
from compiler import CompileOptions, compile_file, compile_source
from compiler.cli import main
from compiler.semantic.diagnostics import Code, Phase, Severity

DRIVER = REPO_ROOT / "program" / "Driver.py"


def _run_cli(*args: str) -> tuple[int, str]:
    stream = io.StringIO()
    code = main([*args], stream=stream)
    return code, stream.getvalue()


# --- API interna -----------------------------------------------------------


def test_compile_source_devuelve_resultado_completo():
    result = compile_source("let x: integer = 1;", filename="memoria.cps")
    assert result.success is True
    assert result.filename == "memoria.cps"
    assert result.ast is not None
    assert result.symbol_table is not None
    assert result.error_count == 0
    assert result.warning_count == 0
    assert result.exit_code == 0


def test_compile_source_separa_diagnosticos_por_fase():
    result = compile_source("let x: integer = (1;", filename="m.cps")
    assert result.syntax_diagnostics
    assert not result.semantic_diagnostics
    assert all(d.phase in (Phase.LEXICAL, Phase.SYNTACTIC) for d in result.syntax_diagnostics)


def test_compile_source_estructura_para_el_ide():
    data = compile_source("let x: integer = 1;").to_dict()
    assert set(["success", "diagnostics", "ast", "symbolTable"]) <= set(data)
    assert isinstance(data["diagnostics"], list)
    assert isinstance(data["errorCount"], int)
    assert isinstance(data["warningCount"], int)
    json.dumps(data, ensure_ascii=False)


def test_compile_file_del_programa_de_ejemplo():
    result = compile_file(SAMPLE_PROGRAM)
    assert result.success, [d.format() for d in result.errors]
    assert result.filename == "program.cps"


def test_opcion_syntax_only_omite_el_analisis_semantico():
    result = compile_source("print(noDeclarada);", options=CompileOptions(syntax_only=True))
    assert result.success
    assert result.symbol_table is None
    assert result.ast is not None


def test_modo_estricto_en_la_api():
    source = 'function f(): integer { return 1; print("x"); }'
    assert compile_source(source).success
    assert not compile_source(source, options=CompileOptions(strict=True)).success


# --- diagnosticos ----------------------------------------------------------


def test_los_diagnosticos_incluyen_linea_y_columna():
    result = compile_code("let x: integer = 1;\nprint(desconocida);")
    diagnostic = result.errors[0]
    assert diagnostic.line == 2
    assert diagnostic.column == 7
    assert diagnostic.code == Code.UNDECLARED_IDENTIFIER


def test_formato_de_los_diagnosticos():
    result = compile_code("print(desconocida);")
    assert result.errors[0].format() == "test.cps:1:7 [SEM001] Identificador no declarado: 'desconocida'."


def test_los_diagnosticos_llevan_tipos_esperado_y_recibido():
    result = compile_code('let x: integer = "a";')
    diagnostic = result.errors[0]
    assert diagnostic.expected_type == "integer"
    assert diagnostic.actual_type == "string"


def test_los_diagnosticos_se_ordenan_por_ubicacion():
    result = compile_code(
        """
        print(tercero);
        print(segundo);
        print(primero);
        """
    )
    posiciones = [(d.line, d.column) for d in result.diagnostics]
    assert posiciones == sorted(posiciones)


def test_el_analisis_no_se_detiene_en_el_primer_error():
    result = compile_code("print(a); print(b); print(c);")
    assert result.error_count == 3


def test_no_se_repiten_diagnosticos_identicos():
    result = compile_code("print(a);")
    assert len(result.diagnostics) == 1


# --- errores sintacticos ---------------------------------------------------


def test_error_sintactico_con_ubicacion():
    result = compile_code("let x: integer = (1 + 2;")
    assert result.errors[0].code == Code.SYNTAX
    assert result.errors[0].line == 1
    assert result.errors[0].column > 1


def test_error_lexico():
    result = compile_code("let x = @;")
    assert Code.LEXICAL in [d.code for d in result.diagnostics]


def test_mensajes_de_error_en_espanol():
    result = compile_code("let x: integer = (1 + 2;")
    assert "Falta" in result.errors[0].message or "esperaba" in result.errors[0].message


def test_se_acumulan_varios_errores_sintacticos():
    result = compile_code("let a: integer = (1;\nlet b: integer = (2;")
    assert len(result.errors) >= 2


def test_no_se_ejecuta_el_analisis_semantico_con_arbol_no_confiable():
    result = compile_code("let x: integer = (1 + 2;\nprint(noDeclarada);")
    assert result.ast is None
    assert result.symbol_table is None
    assert not result.semantic_diagnostics


def test_severidad_de_los_errores_sintacticos():
    result = compile_code("let x: integer = (1;")
    assert all(d.severity is Severity.ERROR for d in result.syntax_diagnostics)


# --- CLI -------------------------------------------------------------------


def test_cli_exito_en_el_programa_de_ejemplo():
    code, output = _run_cli(str(SAMPLE_PROGRAM))
    assert code == 0
    assert "Compilacion exitosa" in output


def test_cli_codigo_de_salida_distinto_de_cero_con_errores(tmp_path):
    fuente = tmp_path / "malo.cps"
    fuente.write_text("print(desconocida);", encoding="utf-8")
    code, output = _run_cli(str(fuente))
    assert code == 1
    assert "Compilacion fallida" in output
    assert "[SEM001]" in output


def test_cli_archivo_inexistente():
    code, _ = _run_cli("no_existe.cps")
    assert code == 2


def test_cli_exporta_el_ast_en_dot(tmp_path):
    destino = tmp_path / "ast.dot"
    code, output = _run_cli(str(SAMPLE_PROGRAM), "--ast", str(destino))
    assert code == 0
    assert destino.exists()
    assert destino.read_text(encoding="utf-8").startswith("digraph")
    assert "AST (DOT) escrito" in output


def test_cli_exporta_el_ast_en_json(tmp_path):
    destino = tmp_path / "ast.json"
    code, _ = _run_cli(str(SAMPLE_PROGRAM), "--ast-json", str(destino))
    assert code == 0
    assert json.loads(destino.read_text(encoding="utf-8"))["kind"] == "Program"


def test_cli_exporta_la_tabla_de_simbolos(tmp_path):
    destino = tmp_path / "symbols.json"
    code, _ = _run_cli(str(SAMPLE_PROGRAM), "--symbols", str(destino))
    assert code == 0
    data = json.loads(destino.read_text(encoding="utf-8"))
    assert data["scopes"]["kind"] == "global"
    assert data["symbolCount"] > 0


def test_cli_imprime_la_tabla_en_texto():
    code, output = _run_cli(str(SAMPLE_PROGRAM), "--symbols-text")
    assert code == 0
    assert "AMBITO" in output and "CATEGORIA" in output


def test_cli_salida_json_de_diagnosticos(tmp_path):
    fuente = tmp_path / "malo.cps"
    fuente.write_text('let x: integer = "a";', encoding="utf-8")
    code, output = _run_cli(str(fuente), "--diagnostics", "json")
    assert code == 1
    data = json.loads(output)
    assert data["success"] is False
    assert data["diagnostics"][0]["code"] == Code.INCOMPATIBLE_ASSIGNMENT
    assert data["diagnostics"][0]["line"] == 1


def test_cli_modo_estricto(tmp_path):
    fuente = tmp_path / "aviso.cps"
    fuente.write_text('function f(): integer { return 1; print("x"); }', encoding="utf-8")
    assert _run_cli(str(fuente))[0] == 0
    assert _run_cli(str(fuente), "--strict")[0] == 1


def test_cli_genera_el_dot_aunque_falte_graphviz(tmp_path):
    destino = tmp_path / "ast.dot"
    imagen = tmp_path / "ast.png"
    code, output = _run_cli(str(SAMPLE_PROGRAM), "--ast", str(destino), "--ast-image", str(imagen))
    assert code == 0
    assert destino.exists()  # el DOT siempre se genera


def test_driver_como_subproceso():
    """El uso tradicional `python3 Driver.py program.cps` sigue funcionando."""
    completed = subprocess.run(
        [sys.executable, DRIVER.name, "program.cps"],
        cwd=str(REPO_ROOT / "program"),
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "Compilacion exitosa" in completed.stdout


def test_driver_no_muestra_traceback_ante_codigo_invalido(tmp_path):
    fuente = tmp_path / "malo.cps"
    fuente.write_text("let x: integer = (1 + 2;", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(DRIVER), str(fuente)],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "Traceback" not in completed.stdout
    assert "Traceback" not in completed.stderr


# --- banderas sin argumento (interfaz documentada en el README) ------------


def test_cli_ast_sin_argumento_escribe_ast_dot(tmp_path, monkeypatch):
    """`python3 Driver.py program.cps --ast` genera ast.dot en el directorio actual."""
    monkeypatch.chdir(tmp_path)
    code, output = _run_cli(str(SAMPLE_PROGRAM), "--ast")
    assert code == 0
    generado = tmp_path / "ast.dot"
    assert generado.exists()
    assert generado.read_text(encoding="utf-8").startswith("digraph")
    assert "AST (DOT) escrito" in output


def test_cli_ast_sin_argumento_imprime_el_arbol(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _, output = _run_cli(str(SAMPLE_PROGRAM), "--ast")
    assert "Program" in output
    assert "└── " in output or "├── " in output


def test_cli_symbols_sin_argumento_imprime_el_arbol():
    code, output = _run_cli(str(SAMPLE_PROGRAM), "--symbols")
    assert code == 0
    assert "GLOBAL" in output
    assert "scope function:makeAdder" in output
    assert "Dog : class (base: Animal)" in output


def test_cli_symbols_sin_argumento_no_crea_archivos(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _run_cli(str(SAMPLE_PROGRAM), "--symbols")
    assert list(tmp_path.iterdir()) == []


def test_cli_ast_y_symbols_combinados(tmp_path, monkeypatch):
    """`python3 Driver.py program.cps --ast --symbols` documentado en el README."""
    monkeypatch.chdir(tmp_path)
    code, output = _run_cli(str(SAMPLE_PROGRAM), "--ast", "--symbols")
    assert code == 0
    assert (tmp_path / "ast.dot").exists()
    assert "GLOBAL" in output
    assert "Program" in output


def test_cli_ast_con_argumento_sigue_escribiendo_donde_se_indique(tmp_path):
    """La forma `--ast RUTA` no cambia de comportamiento."""
    destino = tmp_path / "otro.dot"
    code, output = _run_cli(str(SAMPLE_PROGRAM), "--ast", str(destino))
    assert code == 0
    assert destino.exists()
    # Con ruta explicita no se vuelca el arbol en la consola.
    assert "├── " not in output


def test_cli_symbols_con_argumento_sigue_escribiendo_json(tmp_path):
    destino = tmp_path / "otro.json"
    code, output = _run_cli(str(SAMPLE_PROGRAM), "--symbols", str(destino))
    assert code == 0
    assert json.loads(destino.read_text(encoding="utf-8"))["symbolCount"] > 0
    assert "GLOBAL" not in output


def test_driver_ast_y_symbols_como_subproceso(tmp_path):
    """Las tres invocaciones documentadas funcionan de verdad desde la terminal."""
    for extra in (["--ast"], ["--symbols"], ["--ast", "--symbols"]):
        completed = subprocess.run(
            [sys.executable, str(DRIVER), str(SAMPLE_PROGRAM), *extra],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
        assert "Traceback" not in completed.stderr
