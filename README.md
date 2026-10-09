# Vivienda en España: precios, ingresos y demografía

Análisis descriptivo con fuentes oficiales congeladas y cálculos reproducibles sin red.

## Recorrido de lectura

1. [Precios e ingresos](notebooks/01_prices.ipynb): precio desde 2000, vivienda de 80 m² y salario neto, inflación, ciclo, territorios y contexto histórico. Incluye las tablas de cobertura y mandatos antes separadas en 01b.
2. [Demografía y vivienda](notebooks/02_demographics.ipynb): población y parque, uso, hogares, construcción y procedencia de llegadas.
3. [Plan de investigación](docs/research_plan.md): oferta, propiedad, financiación y políticas. Las [plantillas pendientes](notebooks/planned/) no contienen resultados.

Informes: [precios](reports/block_01_prices.md), [salarios](reports/block_01_housing_salary.md), [demografía](reports/block_02_demographics.md). [Auditoría](notebooks/00_data_audit.ipynb).

## Medidas y cobertura

| Comparación | Periodo | Medida |
| --- | --- | --- |
| Precio nacional | 2000–2025 | Tasación MIVAU en euros/m²; no precio de compraventa |
| Vivienda e ingresos | 2000–2023 | Tasación × 80 m² y salario neto Eurostat de un perfil fiscal |
| Contexto largo | 1971–2025 | Vivienda estimada con BIS, anclada a MIVAU 2025; remuneración AMECO con cotizaciones empresariales |
| Parque y población | 2001–2025 | Stocks nacionales; viviendas principales y no principales |
| Construcción | 2000–2025 | Viviendas iniciadas y terminadas, no compras |
| Procedencia de llegadas | 2008–2024 | Movimientos por residencia anterior, no origen de nacimiento |

Los euros históricos no se ajustan por inflación salvo indicación. BIS usa el área de Madrid en 1975–1986. Origen migratorio no determina nacionalidad. Parque total no equivale a oferta disponible. Las interpolaciones de hogares se marcan. Las comparaciones no identifican causas de los precios.

## Reproducir

Python 3.11 o posterior, desde la raíz:

```bash
python -m venv .venv
```

Activa `.venv\Scripts\Activate.ps1` en PowerShell o `source .venv/bin/activate` en Linux/macOS. Después:

```bash
python -m pip install -e ".[dev]"
python scripts/run_block01.py
python scripts/run_block02.py
jupyter lab
```

Los generadores reproducen **23 figuras del bloque 1 y 13 del bloque 2**, tablas e informes. Los notebooks muestran las mismas figuras.

```bash
ruff check src scripts tests
python scripts/check_project.py
python -m unittest discover -s tests -v
python scripts/check_notebooks.py --save
```

`--save` guarda las salidas; sin esa opción se comprueba en memoria. GitHub Actions ejecuta las verificaciones. [Mapa del repositorio](docs/repository_structure.md).

## Licencias

Código: [MIT](LICENSE). Los datos externos conservan sus condiciones originales. Geometrías: [atribuciones](data/snapshots/block01/THIRD_PARTY_NOTICES.md).
