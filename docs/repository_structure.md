# Estructura del repositorio

| Ruta | Responsabilidad |
| --- | --- |
| `notebooks/` | Auditoría y relatos ejecutados de los bloques 1 y 2 |
| `notebooks/planned/` | Plantillas de análisis pendientes |
| `src/spain_housing/` | Cálculos, validación y generación |
| `scripts/run_block01.py`, `run_block02.py` | Reproducir sin red |
| `scripts/build_*.py`, `fetch_block01_context.py` | Recuperar fuentes; no necesarios para reproducir |
| `data/snapshots/` | Fuentes congeladas, procedencia y licencias |
| `data/metadata/` | Fuentes activas y candidatas |
| `reports/` | Informes, figuras PNG y tablas publicados |
| `docs/` | Alcance, metodología, planes y catálogos |
| `tests/`, `.github/workflows/` | Pruebas y verificaciones automáticas |

El bloque 1 genera 23 figuras: `prices_analysis` integra `salary_analysis` y `long_history`. El bloque 2 genera 13: `demographics` integra `demographic_publication`, hogares y migración. Los notebooks llaman una vez al generador y muestran los resultados.

Los catálogos de bloque enumeran todos los PNG publicados. Los nombres numéricos son identificadores estables, no el orden de lectura. Figuras auxiliares de bruto, euros constantes y componentes demográficos se conservan como apoyo.

`price_history.py` conserva funciones usadas por pruebas; `run_price_history.py` es una entrada compatible al bloque 1. Las fuentes alternativas se mantienen por trazabilidad. `tmp/`, entornos y cachés se excluyen de Git.

El antiguo notebook 01b está integrado en `01_prices.ipynb`. Para reproducir y verificar, seguir el [README](../README.md). Un cambio de figura debe actualizar generador, PNG, tabla, catálogo y explicación.
