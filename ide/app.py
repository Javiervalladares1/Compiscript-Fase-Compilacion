"""IDE web minimo para escribir y compilar codigo Compiscript.

Es una capa delgada sobre la API interna del compilador
(:func:`compiler.compile_source`). El compilador funciona sin el IDE y el IDE
no contiene logica semantica.

Seguridad: el unico dato que acepta el servidor es el codigo fuente del editor.
No se leen rutas arbitrarias del disco ni se ejecutan comandos del usuario.

Ejecucion::

    python3 ide/app.py
    # o bien
    FLASK_APP=ide/app.py python3 -m flask run
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from flask import Flask, jsonify, render_template, request  # noqa: E402

from compiler import CompileOptions, compile_source  # noqa: E402
from compiler.backend.simulator import SimulatorError, run_spim  # noqa: E402

#: Nombre que se muestra como "archivo" de los diagnosticos del editor.
EDITOR_FILENAME = "<editor>"

#: Tamano maximo del codigo aceptado, para evitar peticiones abusivas.
MAX_SOURCE_BYTES = 512 * 1024

EXAMPLE_PATH = REPO_ROOT / "program" / "program.cps"
EXAMPLES = {
    "frontend": EXAMPLE_PATH,
    "factorial": REPO_ROOT / "examples/mips/01_factorial.cps",
    "llamadas": REPO_ROOT / "examples/mips/02_llamadas_y_parametros.cps",
    "control": REPO_ROOT / "examples/mips/03_control_y_memoria.cps",
    "closures": REPO_ROOT / "examples/mips/04_closures.cps",
    "clases": REPO_ROOT / "examples/mips/05_clases_y_herencia.cps",
    "excepciones": REPO_ROOT / "examples/mips/06_excepciones.cps",
    "integral": EXAMPLE_PATH,
}
RUN_TIMEOUT = 5.0


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["JSON_SORT_KEYS"] = False

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/example")
    def example() -> Any:
        """Solo permite seleccionar ejemplos conocidos del proyecto."""
        name = request.args.get("name", "frontend")
        path = EXAMPLES.get(name)
        if path is None:
            return jsonify({"error": "Ejemplo desconocido."}), 404
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            return jsonify({"error": "No se encontro el ejemplo en el proyecto."}), 404
        return jsonify({"source": source, "name": path.name,
                        "phase": "frontend" if name == "frontend" else "mips"})

    def compile_request(*, execute: bool = False) -> Any:
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({"error": "Se esperaba un objeto JSON."}), 400
        source = payload.get("source")
        if not isinstance(source, str):
            return jsonify({"error": "Se esperaba el campo 'source' con el codigo fuente."}), 400
        if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
            return jsonify({"error": "El codigo fuente excede el tamano maximo permitido."}), 413

        allocation = payload.get("allocation", "registers")
        if allocation not in ("registers", "stack"):
            return jsonify({"error": "La asignacion debe ser registers o stack."}), 400
        generate_mips = payload.get("generate_mips", False)
        if not isinstance(generate_mips, bool):
            return jsonify({"error": "generate_mips debe ser boolean."}), 400
        strict = payload.get("strict", False)
        if not isinstance(strict, bool):
            return jsonify({"error": "strict debe ser boolean."}), 400
        options = CompileOptions(
            strict=strict,
            generate_mips=execute or generate_mips,
            allocation=allocation,
        )
        result = compile_source(source, filename=EDITOR_FILENAME, options=options)
        data = result.to_dict()
        data["execution"] = None
        if execute and result.success and result.mips is not None:
            try:
                output = run_spim(result.mips, timeout=RUN_TIMEOUT)
                data["execution"] = {"success": True, "output": output, "error": None}
            except SimulatorError as error:
                data["execution"] = {"success": False, "output": "", "error": str(error)}
        return jsonify(data)

    @app.post("/api/compile")
    def compile_endpoint() -> Any:
        return compile_request()

    @app.post("/api/run")
    def run_endpoint() -> Any:
        return compile_request(execute=True)

    return app


app = create_app()


def _parse_args() -> Any:
    import argparse

    parser = argparse.ArgumentParser(description="IDE web de Compiscript")
    parser.add_argument(
        "--host",
        default=None,
        help="Interfaz de escucha (por omision 127.0.0.1; usar 0.0.0.0 en Docker)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Puerto de escucha (por omision 5001)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    import os

    args = _parse_args()

    # Por omision solo escucha en localhost. Dentro de Docker se necesita
    # IDE_HOST=0.0.0.0 para que el puerto publicado sea alcanzable.
    host = args.host or os.environ.get("IDE_HOST", "127.0.0.1")

    # En macOS el puerto 5000 lo ocupa "AirPlay Receiver" (Control Center). Por
    # eso el puerto es configurable por bandera y por variable de entorno;
    # `PORT` se acepta porque es la convencion de la mayoria de entornos.
    port = args.port or int(os.environ.get("IDE_PORT") or os.environ.get("PORT") or 5001)

    print(f"IDE de Compiscript en http://{host}:{port}  (Ctrl+C para salir)")
    app.run(host=host, port=port, debug=False)
