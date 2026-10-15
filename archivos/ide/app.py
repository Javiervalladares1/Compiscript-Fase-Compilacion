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

#: Nombre que se muestra como "archivo" de los diagnosticos del editor.
EDITOR_FILENAME = "<editor>"

#: Tamano maximo del codigo aceptado, para evitar peticiones abusivas.
MAX_SOURCE_BYTES = 512 * 1024

EXAMPLE_PATH = REPO_ROOT / "program" / "program.cps"


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["JSON_SORT_KEYS"] = False

    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/api/example")
    def example() -> Any:
        """Devuelve el programa de ejemplo incluido en el repositorio."""
        try:
            source = EXAMPLE_PATH.read_text(encoding="utf-8")
        except OSError:
            source = "// No se encontro program/program.cps\n"
        return jsonify({"source": source, "name": EXAMPLE_PATH.name})

    @app.post("/api/compile")
    def compile_endpoint() -> Any:
        payload = request.get_json(silent=True) or {}
        source = payload.get("source")
        if not isinstance(source, str):
            return jsonify({"error": "Se esperaba el campo 'source' con el codigo fuente."}), 400
        if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
            return jsonify({"error": "El codigo fuente excede el tamano maximo permitido."}), 413

        options = CompileOptions(strict=bool(payload.get("strict", False)))
        result = compile_source(source, filename=EDITOR_FILENAME, options=options)
        return jsonify(result.to_dict())

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
        help="Puerto de escucha (por omision 5000; en macOS suele estar ocupado)",
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
    port = args.port or int(os.environ.get("IDE_PORT") or os.environ.get("PORT") or 5000)

    print(f"IDE de Compiscript en http://{host}:{port}  (Ctrl+C para salir)")
    app.run(host=host, port=port, debug=False)
