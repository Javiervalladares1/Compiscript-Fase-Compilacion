"""Tabla de simbolos: jerarquia, contenido de los simbolos y exportacion."""

from __future__ import annotations

import json

from conftest import SAMPLE_PROGRAM, compile_code
from compiler import compile_file
from compiler.symbols.scope import ScopeKind
from compiler.symbols.symbols import (
    ClassSymbol,
    FunctionSymbol,
    SymbolCategory,
    VariableSymbol,
)

PROGRAM = """
const LIMITE: integer = 10;
let contador: integer = 0;

function acumular(inicio: integer, paso: float): float {
  let total: float = inicio;
  function ayudante(): float { return total + paso; }
  return ayudante();
}

class Animal {
  let nombre: string;
  function constructor(nombre: string) { this.nombre = nombre; }
  function hablar(): string { return this.nombre; }
}

class Perro : Animal { }
"""


def _table(source: str = PROGRAM):
    result = compile_code(source)
    assert result.symbol_table is not None
    return result.symbol_table


def test_existe_el_ambito_global():
    table = _table()
    assert table.global_scope.kind is ScopeKind.GLOBAL
    assert table.global_scope.parent is None


def test_jerarquia_de_ambitos_con_padres_e_hijos():
    table = _table()
    for scope in table.all_scopes:
        for child in scope.children:
            assert child.parent is scope
        if scope.parent is not None:
            assert scope in scope.parent.children


def test_nombre_calificado_del_ambito():
    table = _table()
    nombres = {scope.qualified_name for scope in table.all_scopes}
    assert "global" in nombres
    assert any(name.startswith("global::acumular") for name in nombres)


def test_profundidad_de_los_ambitos():
    table = _table()
    assert table.global_scope.depth == 0
    for scope in table.all_scopes:
        if scope.parent is not None:
            assert scope.depth == scope.parent.depth + 1


def test_simbolo_de_constante():
    symbol = _table().global_scope.lookup_local("LIMITE")
    assert isinstance(symbol, VariableSymbol)
    assert symbol.category is SymbolCategory.CONSTANT
    assert symbol.mutable is False
    assert symbol.initialized is True
    assert symbol.type.name == "integer"
    assert symbol.span is not None and symbol.span.line == 2


def test_simbolo_de_variable():
    symbol = _table().global_scope.lookup_local("contador")
    assert isinstance(symbol, VariableSymbol)
    assert symbol.category is SymbolCategory.VARIABLE
    assert symbol.mutable is True


def test_simbolo_de_funcion_con_parametros_ordenados():
    symbol = _table().global_scope.lookup_local("acumular")
    assert isinstance(symbol, FunctionSymbol)
    assert symbol.category is SymbolCategory.FUNCTION
    assert [p.index for p in symbol.parameters] == [0, 1]
    assert [p.name for p in symbol.parameters] == ["inicio", "paso"]
    assert [p.type.name for p in symbol.parameters] == ["integer", "float"]
    assert symbol.return_type.name == "float"
    assert symbol.ast_node is not None
    assert symbol.body_scope is not None


def test_simbolo_de_clase_con_miembros():
    animal = _table().classes.get("Animal")
    assert isinstance(animal, ClassSymbol)
    assert "nombre" in animal.fields
    assert "hablar" in animal.methods
    assert animal.constructor is not None
    assert animal.constructor.category is SymbolCategory.CONSTRUCTOR
    assert animal.class_scope is not None


def test_informacion_de_herencia():
    table = _table()
    perro = table.classes.get("Perro")
    assert perro is not None and perro.base_name == "Animal"
    assert table.classes.ancestors("Perro") == ["Perro", "Animal"]


def test_simbolo_de_parametro():
    table = _table()
    funcion = table.global_scope.lookup_local("acumular")
    assert isinstance(funcion, FunctionSymbol)
    assert funcion.body_scope is not None
    parametro = funcion.body_scope.lookup_local("inicio")
    assert isinstance(parametro, VariableSymbol)
    assert parametro.category is SymbolCategory.PARAMETER
    assert parametro.initialized is True


def test_capturas_registradas_en_el_simbolo():
    table = _table()
    funcion = table.global_scope.lookup_local("acumular")
    assert isinstance(funcion, FunctionSymbol)
    assert funcion.body_scope is not None
    ayudante = funcion.body_scope.lookup_local("ayudante")
    assert isinstance(ayudante, FunctionSymbol)
    assert set(ayudante.captures) == {"total", "paso"}
    assert ayudante.enclosing_function == "acumular"


def test_visibilidad_por_omision():
    symbol = _table().global_scope.lookup_local("contador")
    assert symbol is not None and symbol.visibility.value == "public"


def test_resolucion_local_y_ascendente():
    table = _table()
    funcion = table.global_scope.lookup_local("acumular")
    assert isinstance(funcion, FunctionSymbol)
    scope = funcion.body_scope
    assert scope is not None
    assert scope.lookup_local("total") is not None
    assert scope.lookup_local("LIMITE") is None       # no es local
    assert scope.resolve("LIMITE") is not None        # si es visible por herencia de ambito


def test_no_se_permite_redeclarar_en_el_mismo_ambito():
    scope = _table().global_scope
    existente = scope.lookup_local("contador")
    assert existente is not None
    assert scope.declare(existente) is False


# --- exportacion -----------------------------------------------------------


def test_exportacion_a_diccionario():
    data = _table().to_dict()
    assert data["scopes"]["kind"] == "global"
    assert data["scopeCount"] > 1
    assert data["symbolCount"] > 5
    assert any(c["name"] == "Animal" for c in data["classes"])


def test_exportacion_serializable_a_json():
    payload = json.dumps(_table().to_dict(), ensure_ascii=False)
    assert '"global"' in payload


def test_exportacion_tabular():
    text = _table().to_text()
    assert "AMBITO" in text and "CATEGORIA" in text
    assert "acumular" in text and "Animal" in text


def test_filas_planas():
    rows = _table().rows()
    assert rows
    nombres = {row["name"] for row in rows}
    assert {"LIMITE", "contador", "acumular", "Animal", "Perro"} <= nombres
    for row in rows:
        assert set(row) == {
            "scope",
            "scopeKind",
            "name",
            "category",
            "type",
            "line",
            "column",
            "details",
        }


def test_tabla_del_programa_de_ejemplo():
    result = compile_file(SAMPLE_PROGRAM)
    assert result.symbol_table is not None
    table = result.symbol_table
    assert table.classes.get("Animal") is not None
    assert table.classes.get("Dog") is not None
    assert table.classes.is_subclass("Dog", "Animal")
    assert table.global_scope.lookup_local("PI") is not None
    assert table.global_scope.lookup_local("factorial") is not None
    json.dumps(table.to_dict(), ensure_ascii=False)


# --- arbol de ambitos de la tabla de simbolos ------------------------------


def test_to_tree_empieza_en_el_ambito_global():
    tree = compile_code(PROGRAM).symbol_table.to_tree()
    assert tree.splitlines()[0] == "GLOBAL"


def test_to_tree_anida_los_parametros_dentro_de_su_funcion():
    """Un parametro debe aparecer bajo el ambito de su funcion, no en global."""
    tree = compile_code(PROGRAM).symbol_table.to_tree()
    lines = tree.splitlines()

    ambito = next(i for i, l in enumerate(lines) if "scope function:acumular" in l)
    parametro = next(i for i, l in enumerate(lines) if "inicio : parameter" in l)
    assert parametro > ambito
    # Esta indentado por debajo del ambito de la funcion.
    assert lines[parametro].index("inicio") > lines[ambito].index("scope")


def test_to_tree_describe_categoria_y_tipo():
    tree = compile_code(PROGRAM).symbol_table.to_tree()
    assert "LIMITE : constant integer (inmutable)" in tree
    assert "contador : variable integer" in tree
    assert "acumular : function(integer, float) -> float" in tree


def test_to_tree_muestra_las_clases_y_su_base():
    tree = compile_file(SAMPLE_PROGRAM).symbol_table.to_tree()
    assert "Animal : class" in tree
    assert "Dog : class (base: Animal)" in tree


def test_to_tree_anida_las_funciones_anidadas():
    tree = compile_code(PROGRAM).symbol_table.to_tree()
    lines = tree.splitlines()
    externa = next(i for i, l in enumerate(lines) if "scope function:acumular" in l)
    interna = next(i for i, l in enumerate(lines) if "scope function:ayudante" in l)
    assert interna > externa
    assert lines[interna].index("scope") > lines[externa].index("scope")


def test_to_tree_incluye_un_simbolo_por_cada_fila():
    table = compile_file(SAMPLE_PROGRAM).symbol_table
    tree_symbols = [l for l in table.to_tree().splitlines() if " : " in l]
    assert len(tree_symbols) == len(table.rows())
