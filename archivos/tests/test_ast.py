"""AST propio: construccion, ubicaciones, serializacion y visualizacion."""

from __future__ import annotations

import json

from conftest import SAMPLE_PROGRAM, compile_code
from compiler import compile_file
from compiler.ast import nodes as N
from compiler.ast.builder import iter_nodes
from compiler.ast.serializer import ast_to_dict, ast_to_json, ast_to_text
from compiler.ast.visualizer import to_dot, write_dot


def _ast(source: str) -> N.Program:
    result = compile_code(source)
    assert result.ast is not None
    return result.ast


def _kinds(source: str) -> set[str]:
    return {node.kind for node in iter_nodes(_ast(source))}


def test_el_ast_no_es_el_parse_tree_de_antlr():
    program = _ast("let x: integer = 1;")
    assert isinstance(program, N.Program)
    assert not hasattr(program, "getChild")


def test_todos_los_nodos_tienen_ubicacion():
    program = _ast(
        """
        let x: integer = 1;
        function f(a: integer): integer { return a; }
        class C { let v: integer; }
        """
    )
    for node in iter_nodes(program):
        assert node.span.line >= 1
        assert node.span.column >= 1
        assert node.span.file == "test.cps"


def test_ubicacion_precisa_de_un_identificador():
    program = _ast("let total: integer = 1;\nprint(total);")
    identifiers = [n for n in iter_nodes(program) if isinstance(n, N.Identifier)]
    assert identifiers[0].name == "total"
    assert (identifiers[0].span.line, identifiers[0].span.column) == (2, 7)


def test_span_final_disponible():
    program = _ast("let x: integer = 1;")
    assert program.statements[0].span.end_line == 1
    assert program.statements[0].span.end_column > 1


def test_nodos_de_declaracion():
    kinds = _kinds(
        """
        let a: integer = 1;
        const B: integer = 2;
        function f(p: integer): integer { return p; }
        class C : D { let campo: integer; function m(): void { } }
        class D { }
        """
    )
    for expected in ("VarDecl", "FunctionDecl", "Parameter", "ClassDecl", "TypeRef", "Block"):
        assert expected in kinds


def test_nodos_de_expresion():
    kinds = _kinds(
        """
        class C { let v: integer; function m(): integer { return this.v; } }
        let obj: C = new C();
        let xs: integer[] = [1, 2];
        let a = 1 + 2 * 3;
        let b = -a;
        let c = true ? 1 : 2;
        let d = xs[0];
        let e = obj.v;
        let f = obj.m();
        let g: string = "texto";
        let h: float = 1.5;
        let i: boolean = false;
        let j: C = null;
        obj.v = 5;
        a = 9;
        """
    )
    for expected in (
        "IntegerLiteral",
        "FloatLiteral",
        "StringLiteral",
        "BooleanLiteral",
        "NullLiteral",
        "ArrayLiteral",
        "Identifier",
        "BinaryExpr",
        "UnaryExpr",
        "TernaryExpr",
        "CallExpr",
        "PropertyAccess",
        "IndexExpr",
        "NewExpr",
        "ThisExpr",
        "AssignStmt",
    ):
        assert expected in kinds, f"Falta el nodo {expected}"


def test_nodos_de_sentencia():
    kinds = _kinds(
        """
        let xs: integer[] = [1];
        if (true) { print(1); } else { print(2); }
        while (true) { break; }
        do { print(1); } while (false);
        for (let i: integer = 0; i < 2; i = i + 1) { continue; }
        foreach (n in xs) { print(n); }
        switch (1) { case 1: print(1); default: print(2); }
        try { print(1); } catch (e) { print(e); }
        function f(): integer { return 1; }
        print("x");
        f();
        { print("bloque"); }
        """
    )
    for expected in (
        "IfStmt",
        "WhileStmt",
        "DoWhileStmt",
        "ForStmt",
        "ForEachStmt",
        "SwitchStmt",
        "SwitchCase",
        "DefaultCase",
        "TryCatchStmt",
        "BreakStmt",
        "ContinueStmt",
        "ReturnStmt",
        "PrintStmt",
        "ExpressionStmt",
        "Block",
    ):
        assert expected in kinds, f"Falta el nodo {expected}"


def test_asignacion_como_expresion():
    kinds = _kinds("let a: integer = 1; let b: integer = 0; b = (a = 3);")
    assert "AssignExpr" in kinds


def test_asignacion_de_propiedad_como_expresion():
    kinds = _kinds(
        """
        class C { let v: integer; }
        let o: C = new C();
        print((o.v = 5));
        """
    )
    assert "AssignExpr" in kinds
    assert "PropertyAccess" in kinds


def test_asociatividad_izquierda_de_las_operaciones_binarias():
    program = _ast("let x = 1 - 2 - 3;")
    declaration = program.statements[0]
    assert isinstance(declaration, N.VarDecl)
    root = declaration.initializer
    assert isinstance(root, N.BinaryExpr) and root.operator == "-"
    assert isinstance(root.left, N.BinaryExpr) and root.left.operator == "-"
    assert isinstance(root.right, N.IntegerLiteral) and root.right.value == 3


def test_precedencia_de_operadores():
    program = _ast("let x = 1 + 2 * 3;")
    declaration = program.statements[0]
    assert isinstance(declaration, N.VarDecl)
    root = declaration.initializer
    assert isinstance(root, N.BinaryExpr) and root.operator == "+"
    assert isinstance(root.right, N.BinaryExpr) and root.right.operator == "*"


def test_literales_se_distinguen_por_su_texto():
    program = _ast('let a = 1; let b = 1.5; let c = "s";')
    literals = [n for n in iter_nodes(program) if isinstance(n, N.Expression)]
    kinds = [n.kind for n in literals]
    assert "IntegerLiteral" in kinds and "FloatLiteral" in kinds and "StringLiteral" in kinds


def test_las_expresiones_guardan_el_tipo_resuelto():
    program = _ast('let x: string = "a" + 1;')
    declaration = program.statements[0]
    assert isinstance(declaration, N.VarDecl)
    assert declaration.initializer is not None
    assert declaration.initializer.resolved_type is not None
    assert declaration.initializer.resolved_type.name == "string"


# --- serializacion ---------------------------------------------------------


def test_serializacion_a_diccionario():
    data = ast_to_dict(_ast("let x: integer = 1;"))
    assert data["kind"] == "Program"
    assert "children" in data
    assert data["children"][0]["kind"] == "VarDecl"
    assert data["children"][0]["span"]["line"] == 1


def test_serializacion_a_json_valido():
    payload = ast_to_json(_ast("let x: integer = 1;"))
    parsed = json.loads(payload)
    assert parsed["kind"] == "Program"


def test_serializacion_a_texto():
    text = ast_to_text(_ast("let x: integer = 1;"))
    assert "Program" in text and "VarDecl x" in text


def test_serializacion_del_programa_de_ejemplo():
    result = compile_file(SAMPLE_PROGRAM)
    assert result.ast is not None
    data = ast_to_dict(result.ast)
    assert data["kind"] == "Program"
    assert len(data["children"]) > 10
    json.dumps(data)  # debe ser serializable sin errores


# --- visualizacion ---------------------------------------------------------


def test_generacion_de_dot():
    dot = to_dot(_ast("let x: integer = 1;"))
    assert dot.startswith("digraph")
    assert dot.rstrip().endswith("}")
    assert "->" in dot
    assert "n0 [label=" in dot


def test_identificadores_unicos_por_nodo():
    dot = to_dot(_ast("let a: integer = 1; let b: integer = 2;"))
    ids = [line.split(" ")[2] for line in dot.splitlines() if "[label=" in line]
    assert len(ids) == len(set(ids))


def test_escape_de_caracteres_especiales_en_dot():
    """Los caracteres con significado en DOT deben salir escapados."""
    from compiler.ast.visualizer import _escape

    assert _escape('con "comillas"') == 'con \\"comillas\\"'
    assert _escape("barra \\ invertida") == "barra \\\\ invertida"
    assert _escape("salto\nde linea") == "salto\\nde linea"
    assert _escape("{llaves}") == "\\{llaves\\}"
    assert _escape("a|b <c>") == "a\\|b \\<c\\>"


def test_dot_con_cadena_que_incluye_caracteres_especiales():
    # La gramatica de Compiscript no admite comillas dentro de una cadena,
    # pero si barras invertidas, llaves y angulos.
    dot = to_dot(_ast('let x: string = "C:\\temp {a|b} <c>";'))
    for line in dot.splitlines():
        if "[label=" not in line:
            continue
        body = line.split('[label="', 1)[1].rsplit('", fillcolor', 1)[0]
        # Ninguna comilla sin escapar puede cerrar la etiqueta antes de tiempo.
        assert body.replace('\\"', "").count('"') == 0


def test_dot_generado_es_valido_para_graphviz(tmp_path):
    from compiler.ast.visualizer import graphviz_available, render_image

    if not graphviz_available():
        return  # Graphviz es opcional: su ausencia no invalida el DOT
    source = write_dot(_ast('let x: string = "C:\\temp {a|b} <c>";'), tmp_path / "ast.dot")
    assert render_image(source, tmp_path / "ast.svg") is not None


def test_escritura_del_archivo_dot(tmp_path):
    target = write_dot(_ast("let x: integer = 1;"), tmp_path / "sub" / "ast.dot")
    assert target.exists()
    assert target.read_text(encoding="utf-8").startswith("digraph")


def test_el_dot_incluye_el_tipo_resuelto():
    dot = to_dot(_ast("let x: float = 1.5;"))
    assert "tipo: float" in dot


# --- arbol de texto del AST -----------------------------------------------


def test_to_tree_usa_conectores_y_ubicaciones():
    tree = _ast("let x: integer = 1;").to_tree()
    lines = tree.splitlines()
    assert lines[0].startswith("Program")
    assert "[1:1]" in lines[0]
    assert any("├── " in line or "└── " in line for line in lines)


def test_to_tree_refleja_la_jerarquia_padre_hijo():
    tree = _ast("let x: integer = 1 + 2;").to_tree()
    assert "VarDecl x" in tree
    assert "Binary +" in tree
    # Los literales cuelgan de la operacion binaria, no de la raiz.
    binario = next(i for i, l in enumerate(tree.splitlines()) if "Binary +" in l)
    literal = next(i for i, l in enumerate(tree.splitlines()) if "IntegerLiteral 1" in l)
    assert literal > binario


def test_to_tree_muestra_operadores_e_identificadores():
    tree = _ast("let total = precio * cantidad;").to_tree()
    assert "Binary *" in tree
    assert "Identifier precio" in tree
    assert "Identifier cantidad" in tree


def test_to_tree_incluye_todos_los_nodos_del_dot():
    """El arbol de texto y el DOT describen el mismo AST."""
    tree_lines = _ast("function f(a: integer): integer { return a; }").to_tree().splitlines()
    dot = to_dot(_ast("function f(a: integer): integer { return a; }"))
    assert len(tree_lines) == dot.count("[label=")
