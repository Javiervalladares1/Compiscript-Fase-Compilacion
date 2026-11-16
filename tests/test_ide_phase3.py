"""Contrato del IDE para mostrar y ejecutar la fase MIPS."""

import shutil

import pytest

from ide.app import MAX_SOURCE_BYTES, create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_page_exposes_compiler_stages(client):
    response = client.get("/")
    assert response.status_code == 200
    for element in ("editor", "tac-output", "mips-output", "execution-output", "allocation"):
        assert f'id="{element}"' in response.get_data(as_text=True)
    assert client.get("/static/app.js").status_code == 200


@pytest.mark.parametrize("name", ["factorial", "llamadas", "control", "closures", "clases", "excepciones", "integral"])
def test_mips_examples_are_available(client, name):
    response = client.get("/api/example", query_string={"name": name})
    assert response.status_code == 200
    assert response.json["phase"] == "mips" and response.json["source"]


def test_example_allowlist_and_original_default(client):
    assert client.get("/api/example?name=../../requirements.txt").status_code == 404
    original = client.get("/api/example").json
    assert original["name"] == "program.cps" and original["phase"] == "frontend"


@pytest.mark.parametrize("mode", ["registers", "stack"])
def test_compile_generates_code_without_running(client, mode):
    response = client.post("/api/compile", json={
        "source": "print(42);", "generate_mips": True, "allocation": mode,
    })
    data = response.json
    assert response.status_code == 200 and data["success"]
    assert "BeginFunc" in data["tac"] and ".globl main" in data["mips"]
    assert data["execution"] is None


@pytest.mark.skipif(shutil.which("spim") is None, reason="Se requiere SPIM")
def test_run_executes_real_simulator(client):
    example = client.get("/api/example?name=factorial").json
    data = client.post("/api/run", json={"source": example["source"]}).json
    assert data["success"] and data["execution"]["success"]
    assert data["execution"]["output"] == "120\n720\n5040\n"


@pytest.mark.skipif(shutil.which("spim") is None, reason="Se requiere SPIM")
def test_runtime_errors_keep_generated_code_and_report_failure(client):
    data = client.post("/api/run", json={"source": "print(1 / 0);"}).json
    assert data["success"] and data["mips"]
    assert not data["execution"]["success"]
    assert "division por cero" in data["execution"]["error"]


def test_semantic_error_blocks_execution(client):
    data = client.post("/api/run", json={"source": "print(desconocido);"}).json
    assert not data["success"] and data["execution"] is None and data["mips"] is None


def test_frontend_and_backend_accept_classes(client):
    data = client.post("/api/compile", json={"source": "class A { let x: integer = 1; }"}).json
    assert data["success"] and data["mips"] is None
    data = client.post("/api/compile", json={
        "source": "class A { let x: integer = 1; }", "generate_mips": True,
    }).json
    assert data["success"] and data["mips"] and "_cs_vt_A" in data["mips"]


@pytest.mark.parametrize("payload", [[], [1], {"source": 1},
    {"source": "print(1);", "allocation": "invalid"},
    {"source": "print(1);", "generate_mips": "true"},
    {"source": "print(1);", "strict": "false"}])
def test_invalid_requests_are_rejected(client, payload):
    assert client.post("/api/compile", json=payload).status_code == 400


def test_source_size_limit(client):
    assert client.post("/api/run", json={"source": "a" * (MAX_SOURCE_BYTES + 1)}).status_code == 413
