"""IDE web: endpoints, contrato JSON y limites de seguridad."""

from __future__ import annotations

import pytest

from conftest import REPO_ROOT  # noqa: F401  (asegura el sys.path del repositorio)

flask = pytest.importorskip("flask", reason="Flask es necesario para las pruebas del IDE")

from ide.app import EDITOR_FILENAME, MAX_SOURCE_BYTES, create_app  # noqa: E402


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


def test_pagina_principal(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Compiscript IDE" in body
    assert 'id="editor"' in body
    assert 'id="diagnostics-list"' in body
    assert 'id="ast-tree"' in body
    assert 'id="symbols-table"' in body


def test_endpoint_de_ejemplo(client):
    response = client.get("/api/example")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "program.cps"
    assert "class Animal" in data["source"]


def test_compilacion_exitosa(client):
    response = client.post("/api/compile", json={"source": "let x: integer = 1;"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["errorCount"] == 0
    assert data["ast"]["kind"] == "Program"
    assert data["symbolRows"]


def test_compilacion_con_errores(client):
    response = client.post("/api/compile", json={"source": 'let x: integer = "a";'})
    data = response.get_json()
    assert data["success"] is False
    assert data["errorCount"] == 1
    diagnostic = data["diagnostics"][0]
    assert diagnostic["code"] == "SEM012"
    assert diagnostic["line"] == 1
    assert diagnostic["column"] == 18
    assert diagnostic["severity"] == "error"
    assert diagnostic["file"] == EDITOR_FILENAME


def test_diagnostico_incluye_tipos(client):
    response = client.post("/api/compile", json={"source": 'let x: integer = "a";'})
    diagnostic = response.get_json()["diagnostics"][0]
    assert diagnostic["expectedType"] == "integer"
    assert diagnostic["actualType"] == "string"


def test_error_sintactico_sin_ast(client):
    response = client.post("/api/compile", json={"source": "let x: integer = (1;"})
    data = response.get_json()
    assert data["success"] is False
    assert data["ast"] is None
    assert data["diagnostics"][0]["phase"] == "syntactic"


def test_advertencias_no_invalidan_la_compilacion(client):
    source = 'function f(): integer { return 1; print("x"); }'
    data = client.post("/api/compile", json={"source": source}).get_json()
    assert data["success"] is True
    assert data["warningCount"] == 1


def test_modo_estricto_desde_el_ide(client):
    source = 'function f(): integer { return 1; print("x"); }'
    data = client.post("/api/compile", json={"source": source, "strict": True}).get_json()
    assert data["success"] is False


def test_tabla_de_simbolos_en_la_respuesta(client):
    source = "class C { let a: integer; } let c: C = new C();"
    data = client.post("/api/compile", json={"source": source}).get_json()
    nombres = {row["name"] for row in data["symbolRows"]}
    assert {"C", "c", "a"} <= nombres
    assert data["symbolTable"]["scopes"]["kind"] == "global"


def test_peticion_sin_codigo_fuente(client):
    response = client.post("/api/compile", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_peticion_con_tipo_incorrecto(client):
    response = client.post("/api/compile", json={"source": 123})
    assert response.status_code == 400


def test_codigo_fuente_demasiado_grande(client):
    response = client.post("/api/compile", json={"source": "a" * (MAX_SOURCE_BYTES + 1)})
    assert response.status_code == 413


def test_el_ide_no_expone_lectura_de_archivos(client):
    """El unico dato aceptado es el codigo fuente; no hay rutas de archivo."""
    response = client.post(
        "/api/compile", json={"source": "let x: integer = 1;", "path": "/etc/passwd"}
    )
    data = response.get_json()
    assert data["success"] is True
    assert data["file"] == EDITOR_FILENAME


def test_recursos_estaticos(client):
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200
