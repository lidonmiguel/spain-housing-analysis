# Estructura y flujo del repositorio

Los bloques 1 (compra y salarios) y 2 (demografía y construcción) están ejecutados.
Los bloques 3–8 son plantillas y planes de trabajo, no resultados terminados.

| Ruta | Responsabilidad |
| --- | --- |
| `src/spain_housing/` | Cálculos, validación de fuentes y generación reutilizable |
| `scripts/build_*.py`, `fetch_block01_context.py` | Recuperación o normalización de fuentes; revisar antes de actualizar |
| `scripts/run_block01.py`, `run_block02.py` | Reproducir entregables con snapshots, sin red |
| `scripts/run_price_history.py` | Entrada compatible al mismo generador del bloque 1 |
| `notebooks/` | Explicación, exploración y salidas ejecutadas usando los módulos |
| `data/snapshots/block01/`, `block02/` | Datos congelados, procedencia y licencias |
| `data/raw/`, `interim/`, `processed/` | Caché y trabajo local; el original EAES es una excepción versionada |
| `data/metadata/` | Inventarios de fuentes, variables y registros; incluyen fuentes candidatas |
| `reports/` | Informes de resultados generados |
| `reports/figures/block01/`, `block02/` | PNG publicados; SVG opcionales del bloque 1 son locales |
| `reports/tables/block01/`, `block02/` | Tablas CSV y hallazgos JSON publicados |
| `docs/` | Alcance, metodología, planes y catálogos |
| `tests/`, `scripts/check_*.py` | Pruebas, validación de artefactos y ejecución de notebooks |

## Bloque 1

`prices_analysis.run_analysis` carga tasaciones, municipios, IPC y gobiernos;
genera las 13 figuras históricas y llama a `salary_analysis.run_salary_analysis`.
El módulo salarial genera las figuras 16–19 y sus dos tablas. Ambos módulos
escriben los informes correspondientes. Hay **17 figuras**, porque se conservan
los nombres históricos y sus huecos de numeración para no romper referencias.

La comparación salarial activa utiliza Eurostat `earn_nt_net`, bruto y neto
del mismo perfil fiscal, 2002–2023. La EAES del INE permanece como fuente
alternativa: su script normaliza esa fuente, no la de Eurostat.
Las figuras 18 y 19 muestran vivienda menos salario en puntos porcentuales,
con una barra por año y una escala común.

## Bloque 2

`demographics.run_analysis` verifica los snapshots del bloque 2 y genera
seis figuras y sus tablas e informe. `02_demographics.ipynb` muestra el análisis.
Su catálogo ejecutado es `block_02_chart_catalogue.csv`.

## Catálogos y reproducción

`docs/chart_catalogue.csv` es el plan general. Los catálogos
`block_01_chart_catalogue.csv` y `block_02_chart_catalogue.csv` enumeran
las figuras efectivamente ejecutadas. Los manifiestos de fuentes y las políticas
salariales documentan qué datos se usan y qué observaciones se excluyen.

Desde la raíz, tras instalar `.[dev]`:

```bash
python scripts/run_block01.py
python scripts/run_block02.py
ruff check src scripts tests
python scripts/check_project.py
python -m unittest discover -s tests -v
python scripts/check_notebooks.py
```

Un cambio de figura debe actualizar el generador, sus PNG y tablas, el catálogo
y los informes que la describen. El notebook debe reutilizar ese cálculo.
