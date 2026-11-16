"""Crea la parte 2 complementaria al nucleo publicado; incluye hashes SHA-256."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/Javiervalladares1/Compiscript-Fase-Compilacion"
CORE_ROOT_FILES = (
    ".dockerignore", ".gitignore", "Dockerfile", "README.md",
    "antlr-4.13.1-complete.jar", "python-venv.sh", "requirements.txt",
    "scripts/generate_parser.sh", "examples/valid/01_tipos_basicos.cps",
    "examples/invalid/14_sintaxis.cps",
)
PART2_ROOT_FILES = (
    "CONTRIBUTIONS.md", "pytest.ini", "LEEME_PARTE_2.md",
    "scripts/start_ide.sh", "scripts/demo_video.sh", "scripts/empaquetar_fase3.py",
)


def files_under(directory: str) -> list[Path]:
    return sorted(path for path in (ROOT / directory).rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts
                  and path.name != ".DS_Store")


def core_files() -> list[Path]:
    files = [ROOT / name for name in CORE_ROOT_FILES]
    for directory in ("compiler", "program", "commands", "examples/mips"):
        files.extend(files_under(directory))
    return sorted(set(files))


def part2_files() -> list[Path]:
    files = [ROOT / name for name in PART2_ROOT_FILES]
    for directory in ("ide", "tests", "docs", "examples/valid", "examples/invalid"):
        files.extend(files_under(directory))
    # El guion de una grabacion anterior conserva su evidencia historica.
    # Esta entrega incluye solamente el guion actualizado de la fase 3.
    excluded = set(core_files()) | {ROOT / "docs/GUION_VIDEO_GRABADO.md"}
    return sorted(set(files) - excluded)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe(files: list[Path]) -> dict[str, str]:
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in files}


def verify(package: Path) -> None:
    with zipfile.ZipFile(package) as archive:
        if archive.testzip() is not None:
            raise SystemExit("El ZIP contiene un archivo danado.")
        manifest = json.loads(archive.read("MANIFIESTO_PARTE2.json"))
        errors = []
        for name, expected in manifest["parte2_archivos"].items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                errors.append("ZIP: " + name)
            if not (ROOT / name).is_file() or digest(ROOT / name) != expected:
                errors.append("Extraido: " + name)
        for name, expected in manifest["parte1_archivos"].items():
            if not (ROOT / name).is_file() or digest(ROOT / name) != expected:
                errors.append("Nucleo: " + name)
        if errors:
            raise SystemExit("Archivos faltantes o modificados:\n" + "\n".join(errors))
    print("ZIP y archivos integrados coinciden con el manifiesto.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", help="Commit del nucleo (por defecto HEAD)")
    parser.add_argument("--verify", type=Path, help="Comprueba el ZIP y los archivos ya integrados")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "out/entrega_fase3/parte2_ide_pruebas_documentacion.zip")
    args = parser.parse_args()
    if args.verify:
        verify(args.verify)
        return
    commit = args.commit or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    core, second = core_files(), part2_files()
    manifest = {
        "repositorio": REPOSITORY,
        "commit_parte1": commit,
        "criterio": "Parte 1: nucleo compilador. Parte 2: IDE, pruebas y documentacion.",
        "integracion": "Extraer la parte 2 en la raiz del repositorio actualizado.",
        "parte1_archivos": describe(core),
        "parte2_archivos": describe(second),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in second:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("MANIFIESTO_PARTE2.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    (args.output.parent / "division_fase3.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verify(args.output)
    print(f"Parte 1: {len(core)} archivos; parte 2: {len(second)} archivos + manifiesto.")
    print(args.output)


if __name__ == "__main__":
    main()
