# Requisitos y evidencia de la fase final

Fuente: [requerimientos de generación de código del curso](https://github.com/gbrolo/compilers-2026/blob/main/compiscript/README_CODE_GENERATION.md).

| Requisito | Implementación | Comprobación |
| --- | --- | --- |
| Llamadas y retornos — 20 puntos | IR tipado, área de argumentos, prólogo y epílogo en `compiler/backend/mips.py` | Recursión, Fibonacci, 24 argumentos, variables que sobreviven llamadas y comparación de sp/fp/s0-s7 |
| Registros o pila — 20 puntos | `RegisterAllocator.getReg`, spill y flush en `compiler/backend/registers.py`; dos modos | Presión de registros, víctima dirty y operandos protegidos; ejecuciones en ambos modos |
| MIPS funcional y simulado — 60 puntos | Backend MIPS32, runtime y wrapper de SPIM | Assembler ejecutado por SPIM con salidas esperadas independientes del código generado |
| Casos exitosos y fallidos | `tests/test_mips.py` y batería semántica | Sintaxis/tipos inválidos, GEN001, división por cero, índices, null, errores de assembler y timeout |
| IDE para escribir y compilar | `ide/app.py`, `ide/templates/`, `ide/static/` | API y pruebas del IDE; edición, dos modos, descargas y salida de SPIM |
| Documentación de arquitectura | `docs/architecture.md`, `docs/FASE3_MIPS.md` | Modelos, límites entre etapas, convención de llamadas, capturas, objetos y handlers |
| Instrucciones de ejecución | `README.md`, `LEEME_PARTE_2.md` | Instalación local, generación, ejecución, IDE, pruebas y Docker |
| Repositorio GitHub | Parte 1 en el repo; parte 2 en ZIP por indicación de entrega | Manifiesto de archivos y hashes en el ZIP; integrar ambas partes para la presentación |
| Contribuciones reales | `CONTRIBUTIONS.md` | Plantilla para los tres integrantes; completar nombres y commits auténticos |

La separación en dos paquetes no sustituye la integración del proyecto para
presentarlo. La evaluación del IDE y la batería de pruebas requiere extraer
la parte 2 sobre la raíz del clon actualizado.

## Comprobación antes de presentar

```bash
source .venv/bin/activate
spim -version
python -m pytest -o addopts='' -q
python program/Driver.py program/program.cps --mips out/programa.asm --run
bash scripts/start_ide.sh
```

Si SPIM no está disponible, pytest omite los casos que necesitan el simulador.
Esas omisiones no constituyen evidencia de ejecución MIPS. La validación local
incluida en `docs/VALIDACION_FASE3.md` indica los comandos y resultados reales.

El proyecto no utiliza un intérprete de Python para fingir las salidas del
assembler: `run_spim` escribe un `.asm` temporal y ejecuta la herramienta externa.
Los resultados esperados de las pruebas se escriben por separado.

## Alcance documentado

El programa del curso y los seis ejemplos MIPS se ejecutan en ambos modos.
Las limitaciones de extensiones adicionales (funciones como valores,
concatenación con float, módulo float e impresión de objetos completos) se
reportan con GEN001 y se detallan en `FASE3_MIPS.md`; no se emite assembler
para ellas. La gramática, los diagnósticos y las pruebas de las fases
anteriores se conservan.
