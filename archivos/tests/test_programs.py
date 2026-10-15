"""Programas Compiscript completos: `examples/valid` e `examples/invalid`.

Cada programa invalido declara en su primera linea los codigos que debe
producir::

    // @expect SEM012 SEM013
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import (
    INVALID_DIR,
    SAMPLE_PROGRAM,
    VALID_DIR,
    expected_codes_of,
    ids_of,
    program_files,
)
from compiler import CompileOptions, compile_file

VALID_PROGRAMS = program_files(VALID_DIR)
INVALID_PROGRAMS = program_files(INVALID_DIR)


def test_hay_programas_de_prueba():
    assert len(VALID_PROGRAMS) >= 8
    assert len(INVALID_PROGRAMS) >= 12


@pytest.mark.parametrize("path", VALID_PROGRAMS, ids=ids_of(VALID_PROGRAMS))
def test_programa_valido_compila(path: Path):
    result = compile_file(path)
    assert result.success, "\n".join(d.format() for d in result.diagnostics)


@pytest.mark.parametrize("path", VALID_PROGRAMS, ids=ids_of(VALID_PROGRAMS))
def test_programa_valido_sin_advertencias(path: Path):
    """Los programas validos tambien deben pasar en modo estricto."""
    result = compile_file(path, CompileOptions(strict=True))
    assert result.success, "\n".join(d.format() for d in result.diagnostics)


@pytest.mark.parametrize("path", VALID_PROGRAMS, ids=ids_of(VALID_PROGRAMS))
def test_programa_valido_produce_ast_y_tabla(path: Path):
    result = compile_file(path)
    assert result.ast is not None
    assert result.symbol_table is not None


@pytest.mark.parametrize("path", INVALID_PROGRAMS, ids=ids_of(INVALID_PROGRAMS))
def test_programa_invalido_produce_los_codigos_esperados(path: Path):
    expected = expected_codes_of(path)
    assert expected, f"{path.name} no declara la cabecera '// @expect'"
    result = compile_file(path)
    obtained = [d.code for d in result.diagnostics]
    assert obtained == expected, (
        f"Codigos obtenidos: {obtained}\n"
        + "\n".join(d.format() for d in result.diagnostics)
    )


@pytest.mark.parametrize("path", INVALID_PROGRAMS, ids=ids_of(INVALID_PROGRAMS))
def test_programa_invalido_falla_cuando_hay_errores(path: Path):
    expected = expected_codes_of(path)
    result = compile_file(path)
    solo_advertencias = all(code.startswith("SEM-W") for code in expected)
    assert result.success is solo_advertencias


@pytest.mark.parametrize("path", INVALID_PROGRAMS, ids=ids_of(INVALID_PROGRAMS))
def test_todo_diagnostico_tiene_ubicacion(path: Path):
    result = compile_file(path)
    for diagnostic in result.diagnostics:
        assert diagnostic.line >= 1
        assert diagnostic.column >= 1
        assert diagnostic.file == path.name
        assert diagnostic.message


# --- programa de ejemplo del curso -----------------------------------------


def test_program_cps_compila_sin_errores():
    result = compile_file(SAMPLE_PROGRAM)
    assert result.error_count == 0, "\n".join(d.format() for d in result.errors)
    assert result.success


def test_program_cps_usa_el_constructor_heredado():
    """`Dog` no declara constructor: debe reutilizar el de `Animal`."""
    result = compile_file(SAMPLE_PROGRAM)
    assert result.symbol_table is not None
    constructor = result.symbol_table.classes.lookup_constructor("Dog")
    assert constructor is not None
    assert constructor.owner_class == "Animal"


def test_program_cps_advierte_del_indice_fuera_de_rango():
    result = compile_file(SAMPLE_PROGRAM)
    assert [d.code for d in result.warnings] == ["SEM-W005"]
