# Segunda mitad pendiente de subir

Esta carpeta contiene los otros **50 archivos originales** del proyecto.
El repositorio conserva 50 archivos originales con el núcleo completo del
compilador. La división es por número de archivos, no por líneas ni tamaño.

Repositorio: https://github.com/Javiervalladares1/Compiscript-Fase-Compilacion

## Contenido

- `archivos/`: los 50 archivos pendientes con su estructura original. Incluye
  `ide/`, `tests/`, `docs/`, 22 ejemplos, `CONTRIBUTIONS.md`, `pytest.ini` y
  `.claude/launch.json`.
- `originales/`: respaldo del README y de `.gitignore` anteriores a la separación.
- `division.json`: listas exactas de ambas mitades y hashes SHA-256 de los
  100 archivos originales para comprobar que se conservaron.

La carpeta completa está ignorada por Git, por lo que no se sube al repositorio.

## Integrar después

Desde la raíz del proyecto:

```bash
cp -R pendiente/archivos/. .
cp pendiente/originales/README.md README.md
python3 -m pytest
```

Estos comandos copian los archivos a sus rutas originales y restauran la
documentación completa; no crean un commit ni suben nada automáticamente.
Conserva el `.gitignore` actual para mantener `pendiente/` fuera de Git.

Validación del proyecto completo antes de separarlo: **393 pruebas correctas y
1 omitida**. El código del compilador se conservó sin cambios.
