"""Pruebas del recorrido fuente -> TAC -> MIPS -> simulador externo."""

from __future__ import annotations

import io
import json
from pathlib import Path
import shutil

import pytest

from compiler import CompileOptions, compile_file, compile_source
from compiler.backend.registers import RegisterAllocator
from compiler.backend.simulator import SimulatorError, run_spim
from compiler.cli import main
from compiler.ir.model import IRFunction, Place
from compiler.semantic.diagnostics import Phase
from compiler.types.types import INTEGER


ROOT = Path(__file__).resolve().parents[1]
SPIM = pytest.mark.skipif(shutil.which("spim") is None, reason="Se requiere SPIM en PATH")


def compile_mips(source: str, mode: str = "registers"):
    result = compile_source(source, options=CompileOptions(generate_mips=True, allocation=mode))
    assert result.success, [d.format() for d in result.diagnostics]
    assert result.ir is not None and result.tac and result.mips
    return result


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
@pytest.mark.parametrize("name, expected", [
    ("01_factorial.cps", "120\n720\n5040\n"),
    ("02_llamadas_y_parametros.cps", "21\n55\n13\n"),
    ("03_control_y_memoria.cps", "suma=12\ntrue\n3.75000000\n7\n1\n"),
    ("04_closures.cps", "12\n14\n"),
    ("05_clases_y_herencia.cps", "Toby ladra.\nToby\n"),
    ("06_excepciones.cps", "Error atrapado: division por cero\nindice fuera del arreglo\nContinuamos\n"),
])
def test_examples_execute_in_spim(mode, name, expected):
    result = compile_file(ROOT / "examples" / "mips" / name,
                          CompileOptions(generate_mips=True, allocation=mode))
    assert result.success, [d.format() for d in result.diagnostics]
    assert run_spim(result.mips) == expected


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_evaluation_order_globals_shadowing_and_short_circuit(mode):
    result = compile_mips('''
        let x: integer = 1;
        function cambiar(): integer { x = x + 1; return x; }
        function sumar(a: integer, b: integer): integer { return a + b; }
        print(x + cambiar());
        print(sumar(x, cambiar()));
        print(x);
        { let x: integer = 99; print(x); }
        print(x);
        let b: boolean = false && cambiar() > 0;
        let c: boolean = true || cambiar() > 0;
        print(b); print(c); print(x);
    ''', mode)
    assert run_spim(result.mips) == "3\n5\n3\n99\n3\nfalse\ntrue\n3\n"


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_pressure_and_many_arguments(mode):
    parameters = ", ".join(f"a{i}: integer" for i in range(24))
    total = " + ".join(f"a{i}" for i in range(24))
    arguments = ", ".join(f"({i} + 1)" for i in range(24))
    source = f"function sumar({parameters}): integer {{ return {total}; }} print(sumar({arguments}));"
    result = compile_mips(source, mode)
    assert run_spim(result.mips) == "300\n"


@SPIM
def test_saved_registers_frame_pointer_and_stack_are_restored():
    result = compile_mips('''
        function f(n: integer): integer {
          let local: integer = n * 2;
          if (n == 0) { return local; }
          return local + f(n - 1);
        }
        print(f(20));
    ''')
    assembly = result.mips.replace(".data\n", ".data\n_probe_sp: .word 0\n", 1)
    before = ["sw $sp, _probe_sp", "li $fp, 123456"]
    before.extend(f"li $s{i}, {100 + i}" for i in range(8))
    after = ["lw $t9, _probe_sp", "bne $sp, $t9, _probe_fail", "nop",
             "li $t9, 123456", "bne $fp, $t9, _probe_fail", "nop"]
    for i in range(8):
        after.extend([f"li $t9, {100 + i}", f"bne $s{i}, $t9, _probe_fail", "nop"])
    assembly = assembly.replace("    jal _cs_entry\n    nop\n",
        "\n".join(before) + "\n    jal _cs_entry\n    nop\n" + "\n".join(after) + "\n", 1)
    assembly += "\n_probe_fail:\n li $a0, -999\n li $v0, 1\n syscall\n li $v0, 10\n syscall\n"
    assert run_spim(assembly) == "420\n"


def test_getReg_spills_dirty_victim_and_respects_pinned_operands():
    emitted, stored, loaded = [], [], []
    function = IRFunction("test")
    allocator = RegisterAllocator(function, emitted.append,
        lambda reg, value: loaded.append((reg, value)),
        lambda reg, value: stored.append((reg, value)))
    values = [Place(f"t{i}", INTEGER) for i in range(18)]
    first = allocator.getReg(values[0], write=True)
    for value in values[1:16]:
        allocator.getReg(value, write=True)
    new = allocator.getReg(values[16], write=True, pinned=(first,))
    assert new != first
    assert allocator.locations[values[0]] == first
    assert allocator.spills == 1 and len(stored) == 1
    victim = stored[0][1]
    allocator.getReg(victim, pinned=(first, new))
    assert loaded[-1][1] == victim
    assert all(reg not in ("$sp", "$fp", "$ra", "$t8", "$t9") for reg in allocator.registers)


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_float_promotion_comparisons_and_returns(mode):
    result = compile_mips('''
        function f(a: float, b: float, c: float, d: float, e: float): float {
          return a + b + c + d + e;
        }
        print(f(1, 2.5, 3, 4.5, 5));
        print(2 < 2.5); print(2.5 >= 2); print(2 == 2.0);
        print(2.0 != 2); print(-2.5); print(5.0 / 2);
    ''', mode)
    lines = run_spim(result.mips).splitlines()
    assert float(lines[0]) == 16
    assert lines[1:5] == ["true", "true", "true", "false"]
    assert [float(x) for x in lines[5:]] == [-2.5, 2.5]


@SPIM
def test_strings_content_equality_utf8_and_integer_limits():
    result = compile_mips('''
        let texto: string = "ho" + "la";
        print(texto == "hola"); print(texto != "hola");
        print("áéñ🙂 " + -2147483648 + " " + 2147483647 + " " + false + " " + 0);
        print(-7 / 2); print(-7 % 2);
        print(-2147483648 / -1); print(-2147483648 % -1);
        print(2147483647 + 1);
    ''')
    assert run_spim(result.mips) == (
        "true\nfalse\náéñ🙂 -2147483648 2147483647 false 0\n-3\n-1\n"
        "-2147483648\n0\n-2147483648\n"
    )


@SPIM
def test_float_arrays_null_strings_and_string_switch():
    result = compile_mips('''
        let a: float[] = [1, 2.5]; print(a[0]); print(a[1]);
        let x: string = null; print(x); print(x == null); print(x + "!");
        switch ("hola") {
          case "ho" + "la": print(1); break;
          default: print(0);
        }
        function f(): float { return 2; } print(f());
    ''')
    assert run_spim(result.mips) == "1.00000000\n2.50000000\nnull\ntrue\nnull!\n1\n2.00000000\n"


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_arrays_matrices_loops_switch_and_early_returns(mode):
    result = compile_mips('''
        function crear(n: integer): integer[] { return [n, n + 1, n + 2]; }
        let a: integer[] = crear(4);
        a[1] = 10;
        let matriz: integer[][] = [a, [1, 2, 3]];
        print(matriz[0][1]);
        let total: integer = 0;
        for (let i: integer = 0; i < 3; i = i + 1) {
          if (i == 1) { continue; }
          total = total + a[i];
        }
        print(total);
        do { total = total - 1; if (total > 8) { continue; } } while (total > 8);
        switch (total) {
          case 8: print(8);
          case 9: print(9); break;
          default: print(0);
        }
    ''', mode)
    assert run_spim(result.mips) == "10\n10\n8\n9\n"


@SPIM
@pytest.mark.parametrize("source, message", [
    ("print(1 / 0);", "division por cero"),
    ("print(1.0 / 0.0);", "division por cero"),
    ("let a: integer[] = [1]; print(a[2]);", "indice fuera"),
    ("let a: integer[] = [1]; print(a[-1]);", "indice fuera"),
])
def test_runtime_errors_are_reported(source, message):
    result = compile_mips(source)
    with pytest.raises(SimulatorError, match=message):
        run_spim(result.mips)


@pytest.mark.parametrize("source", [
    'print("x=" + 1.5);',
    "print(2147483648);",
    "print(1.5 % 1.0);",
    "function f(): integer { return 1; } let g = f; print(g());",
    "print([1, 2]);",
    "class A {} print(new A());",
])
def test_unsupported_features_report_codegen_diagnostics(source):
    assert compile_source(source).success
    result = compile_source(source, options=CompileOptions(generate_mips=True))
    assert not result.success
    assert result.errors[0].code == "GEN001"
    assert result.errors[0].phase is Phase.CODEGEN
    assert result.mips is None


def test_frontend_errors_do_not_generate_code():
    result = compile_source("print(desconocido);", options=CompileOptions(generate_mips=True))
    assert not result.success and result.ir is None and result.mips is None


@SPIM
def test_cli_exports_both_stages_and_runs(tmp_path):
    tac, asm = tmp_path / "out" / "factorial.tac", tmp_path / "out" / "factorial.asm"
    out = io.StringIO()
    code = main([str(ROOT / "examples/mips/01_factorial.cps"), "--tac", str(tac),
                 "--mips", str(asm), "--run", "--quiet"], stream=out)
    assert code == 0
    assert "BeginFunc" in tac.read_text() and "jal" in asm.read_text()
    assert out.getvalue().endswith("120\n720\n5040\n")


def test_cli_json_remains_valid_when_exporting_tac_and_mips(tmp_path):
    output = io.StringIO()
    code = main([str(ROOT / "examples/mips/01_factorial.cps"),
                 "--tac", str(tmp_path / "test.tac"),
                 "--mips", str(tmp_path / "test.asm"),
                 "--ast-json", str(tmp_path / "ast.json"),
                 "--symbols", str(tmp_path / "symbols.json"),
                 "--diagnostics", "json"], stream=output)
    payload = json.loads(output.getvalue())
    assert code == 0 and payload["success"]
    assert payload["tac"] and payload["mips"]
    assert (tmp_path / "ast.json").is_file() and (tmp_path / "symbols.json").is_file()


@SPIM
def test_printing_error_words_is_not_a_runtime_error():
    text = "Error de ejecucion: spim: (parser) Exception occurred at"
    result = compile_mips(f"print({json.dumps(text)});")
    assert run_spim(result.mips) == text + "\n"


def test_only_tac_and_existing_frontend_mode():
    source = "function f(n: integer): integer { return n + 1; } print(f(4));"
    result = compile_source(source, options=CompileOptions(generate_tac=True))
    assert result.success and result.tac and "param 4" in result.tac
    assert result.mips is None
    result = compile_source(source)
    assert result.success and result.ir is None and result.mips is None


def test_conflicting_options_and_failed_compilations_do_not_write_assembly(tmp_path):
    with pytest.raises(ValueError, match="syntax_only"):
        CompileOptions(syntax_only=True, generate_mips=True)
    with pytest.raises(ValueError, match="allocation"):
        CompileOptions(allocation="invalid")
    source = tmp_path / "invalid.cps"
    source.write_text("print(desconocido);", encoding="utf-8")
    assembly = tmp_path / "invalid.asm"
    code = main([str(source), "--mips", str(assembly)], stream=io.StringIO())
    assert code == 1 and not assembly.exists()


def test_strict_warnings_prevent_generation():
    result = compile_source('function f(): integer { return 1; print(2); }',
        options=CompileOptions(strict=True, generate_mips=True))
    assert not result.success and result.warnings and result.ir is None and result.mips is None


def test_simulator_reports_missing_executable(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(SimulatorError, match="No se encontro SPIM"):
        run_spim(".text\nmain:")


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_simulator_rejects_invalid_timeouts(timeout, monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: "/unused/spim")
    with pytest.raises(SimulatorError, match="finito y mayor que cero"):
        run_spim(".text\nmain:", timeout=timeout)


@SPIM
def test_simulator_reports_assembly_errors_and_timeout():
    with pytest.raises(SimulatorError):
        run_spim(".text\n.globl main\nmain:\n instruccion_inexistente\n")
    with pytest.raises(SimulatorError, match="excedio"):
        run_spim(".text\n.globl main\nmain:\n b main\n nop\n", timeout=0.1)


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_nested_functions_share_lexical_variables_and_recursive_frames(mode):
    result = compile_mips('''
      function outer(x: integer): integer {
        let n: integer = 0;
        function left(): integer { n = n + x; return n; }
        function right(): integer {
          function deep(): integer { return left() + x; }
          return deep();
        }
        print(left()); print(right());
        if (x > 1) { return n + outer(x - 1); }
        return n;
      }
      print(outer(3));
    ''', mode)
    assert run_spim(result.mips) == "3\n9\n2\n6\n1\n3\n12\n"


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_classes_initializers_inherited_constructors_and_dynamic_methods(mode):
    result = compile_mips('''
      class Base {
        let n: integer = 7;
        let values: integer[] = [1, 2];
        function constructor(a: integer, b: integer, c: integer, d: integer, e: integer) {
          this.n = a + b + c + d + e;
        }
        function value(): integer { return this.n; }
        function nested(x: integer): integer {
          function inc(): integer { this.n = this.n + x; return this.value(); }
          return inc();
        }
      }
      class Child : Base {
        let extra: integer = 10;
        function value(): integer { return this.n + this.extra; }
      }
      let b: Base = new Child(1, 2, 3, 4, 5);
      print(b.value()); print(b.nested(5));
      b.values[0] = 99; print(b.values[0]);
      let other: Child = new Child(0, 0, 0, 0, 0);
      print(other.values[0]); print(other.value());
    ''', mode)
    assert run_spim(result.mips) == "25\n30\n99\n1\n10\n"


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_try_catch_restores_call_frames_and_preserves_prior_effects(mode):
    result = compile_mips('''
      let value: integer = 0;
      function fail(n: integer): integer {
        if (n > 0) { return fail(n - 1); }
        value = 9;
        return 1 / 0;
      }
      function test(): integer {
        let local: integer = 1;
        try {
          local = 42;
          print(fail(8));
        } catch (e) {
          print(e); print(local); print(value);
        }
        return 100;
      }
      print(test());
      try {
        try { print(1 / 0); } catch (inner) {
          print(inner);
          let missing: integer[] = null;
          print(missing[0]);
        }
      } catch (outer) { print(outer); }
      print(7);
    ''', mode)
    assert run_spim(result.mips) == "division por cero\n42\n9\n100\ndivision por cero\nindice fuera del arreglo\n7\n"


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_try_handlers_are_removed_on_return_break_and_continue(mode):
    result = compile_mips('''
      function early(): integer {
        try { return 5; } catch (e) { return 0; }
      }
      try {
        print(early());
        let n: integer = 0;
        while (n < 3) {
          try { n = n + 1; continue; } catch (e) { print(99); }
        }
        while (true) {
          try { break; } catch (e) { print(98); }
        }
        print(n);
        print(1 / 0);
      } catch (e) { print(e); }
      print(6);
    ''', mode)
    assert run_spim(result.mips) == "5\n3\ndivision por cero\n6\n"


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_null_property_and_method_access_can_be_caught(mode):
    result = compile_mips('''
      class A { let n: integer = 1; function get(): integer { return this.n; } }
      let a: A = null;
      try { print(a.n); } catch (e) { print(e); }
      try { print(a.get()); } catch (e) { print(e); }
      print(10);
    ''', mode)
    assert run_spim(result.mips) == "acceso a un objeto null\nacceso a un objeto null\n10\n"


@SPIM
@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_official_program_runs_through_catch_and_inherited_method(mode):
    result = compile_file(ROOT / "program/program.cps", CompileOptions(generate_mips=True, allocation=mode))
    assert result.success, [d.format() for d in result.diagnostics]
    assert run_spim(result.mips) == (
      "5 + 1 = 6\nGreater than 5\nResult is now 10\nResult is now 9\nResult is now 8\n"
      "Loop index: 0\nLoop index: 1\nLoop index: 2\nNumber: 1\nNumber: 2\nNumber: 4\nNumber: 5\n"
      "It's seven\nIt's six\nSomething else\nCaught an error: indice fuera del arreglo\nRex barks.\n"
      "First number: 1\nMultiples of 2: 2, 4\nProgram finished.\n"
    )
