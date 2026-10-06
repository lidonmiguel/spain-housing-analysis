# Spain Housing Analysis

Proyecto de ciencia de datos sobre la vivienda en España, con fuentes oficiales y análisis reproducible.

**Bloque 1: precio de compra de vivienda desde 2000 hasta 2025**, con 13 figuras,
tablas territoriales y contexto político. La medida principal es la **tasación media
de vivienda libre en €/m²**. La comparación con los precios generales (IPC) empieza
en **2002** y los municipios seleccionados en **2005**. Datos recuperados el 6 de octubre de 2026.

**Bloque 2: demografía, construcción y precio**, con seis figuras, datos INE/MIVAU y comparaciones con cobertura explícita.

## Empieza aquí

- [Demografía: notebook ejecutado](notebooks/02_demographics.ipynb) e [informe](reports/block_02_demographics.md).
- [Informe completo del precio de compra](reports/block_01_prices.md).
- [Notebook principal ejecutado: código, gráficas y resultados](notebooks/01_prices.ipynb).
- [Notebook de cobertura, ciclos y mandatos](notebooks/01b_price_history.ipynb).
- [Figuras](reports/figures/block01/) y [tablas descargables](reports/tables/block01/).
- [Fuentes originales y SHA-256](data/snapshots/block01/source_manifest.json).

![Precio de compra nacional desde 2000](reports/figures/block01/01_national_levels.png)

## Qué analiza el bloque 1

| Parte | Medida y periodo |
| --- | --- |
| Evolución nacional | Tasación €/m², 2000–2025; cambios anuales y ciclo |
| Precios generales | Tasación e IPC, misma base 2002 = 100, 2002–2025 |
| Comunidades y provincias | Nivel 2025, cambio 2000–2025, cobertura territorial |
| Municipios y perfiles | 30 casos seleccionados, 2005–2025; muestras fijas |
| Gobiernos | Evolución de la compra durante presidencias; contexto, sin atribución causal |

Tasación, precio de una transacción e índice IPV tienen definiciones distintas.
Las fuentes originales se conservan, pero este bloque usa la tasación de forma consistente.
Comparar con el IPC no mide accesibilidad económica: para ello se necesitan ingresos
y condiciones de financiación. Los periodos políticos no constituyen un ranking de gestión.

## Reproducir

Python 3.11 o posterior. Desde la raíz:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/run_block01.py
python scripts/run_block02.py
jupyter lab
```

En Windows PowerShell, activar con `.venv\Scripts\Activate.ps1`.
`run_price_history.py` reproduce el mismo bloque de compra: hay un único generador.
Los snapshots están versionados y el análisis no necesita descargar datos.

```bash
ruff check src scripts tests
python scripts/check_project.py
python -m unittest discover -s tests -v
python scripts/check_notebooks.py
```

## Organización y siguientes bloques

`notebooks/`: análisis y resultados; `src/`: cálculos reutilizables; `scripts/`: extracción y ejecución;
`data/snapshots/`: fuentes congeladas; `reports/`: figuras y tablas; `docs/`: alcance y metodología.
Los bloques 1 y 2 están desarrollados. Siguen pendientes: oferta y tenencia en detalle, propiedad,
accesibilidad económica, políticas y modelado.

## Licencias y atribución

Código: [MIT](LICENSE). Los datos externos conservan sus condiciones originales.
Geometrías: [atribuciones y licencia de terceros](data/snapshots/block01/THIRD_PARTY_NOTICES.md).
