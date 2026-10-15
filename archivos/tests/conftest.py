"""Configuracion y utilidades compartidas por la bateria de pruebas."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from compiler import CompilationResult, CompileOptions, compile_source  # noqa: E402

PROGRAMS_DIR = REPO_ROOT / "examples"
VALID_DIR = PROGRAMS_DIR / "valid"
INVALID_DIR = PROGRAMS_DIR / "invalid"
SAMPLE_PROGRAM = REPO_ROOT / "program" / "program.cps"


def compile_code(source: str, strict: bool = False) -> CompilationResult:
    """Compila un fragmento en memoria."""
    return compile_source(source, filename="test.cps", options=CompileOptions(strict=strict))


def codes(result: CompilationResult) -> list[str]:
    return [diagnostic.code for diagnostic in result.diagnostics]


def assert_ok(source: str) -> CompilationResult:
    """Comprueba que ``source`` compila sin errores."""
    result = compile_code(source)
    assert result.success, f"Se esperaba exito y se obtuvieron: {_describe(result)}"
    return result


def assert_error(source: str, *expected_codes: str) -> CompilationResult:
    """Comprueba que ``source`` produce exactamente los codigos indicados."""
    result = compile_code(source)
    assert not result.success, "Se esperaba al menos un error y la compilacion fue exitosa"
    for code in expected_codes:
        assert code in codes(result), (
            f"Falta el codigo {code}. Diagnosticos obtenidos: {_describe(result)}"
        )
    return result


def assert_no_code(source: str, *forbidden: str) -> CompilationResult:
    result = compile_code(source)
    for code in forbidden:
        assert code not in codes(result), (
            f"No se esperaba el codigo {code}. Diagnosticos: {_describe(result)}"
        )
    return result


def _describe(result: CompilationResult) -> str:
    if not result.diagnostics:
        return "(ninguno)"
    return "; ".join(diagnostic.format() for diagnostic in result.diagnostics)


def expected_codes_of(path: Path) -> list[str]:
    """Lee la cabecera ``// @expect COD1 COD2`` de un programa de prueba."""
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    if not first_line.startswith("// @expect"):
        return []
    return first_line.replace("// @expect", "").split()


def program_files(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.cps"))


@pytest.fixture()
def compile_fixture():
    return compile_code


def ids_of(paths: Iterable[Path]) -> list[str]:
    return [path.name for path in paths]
