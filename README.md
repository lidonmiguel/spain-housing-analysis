# Spain Housing Analysis

Proyecto de ciencia de datos sobre la vivienda en España, con fuentes oficiales,
análisis reproducible y una lectura crítica de los discursos políticos.

**Primer bloque realizado:** 24 figuras, tablas de resultados e informes en español.
Histórico ampliado: compra desde 1995, alquiler desde 2011 y municipios desde 2005.
Datos recuperados el **6 de octubre de 2026**. Los demás bloques son trabajo pendiente.

## Empieza aquí

- [**Empieza por el histórico ampliado:** ciclos, inflación y gobiernos](reports/block_01_price_history.md).
- [**Notebook histórico con cálculos visibles y gráficas**](notebooks/01b_price_history.ipynb).
- [Gráficas históricas](reports/figures/history/) y [tablas históricas](reports/tables/history/).
- [Informe: precios, territorio y contexto político](reports/block_01_prices.md).
- [Notebook ejecutado con las gráficas y resultados](notebooks/01_prices.ipynb).
- [Figuras publicadas](reports/figures/block01/) y [tablas descargables](reports/tables/block01/).
- [Fuentes y huellas SHA-256](data/snapshots/block01/source_manifest.json).

### Perspectiva histórica: 2011–2024

| Medida nacional | Cambio nominal | Cambio ajustado por IPC |
| --- | ---: | ---: |
| Compra: índice IPV | +27,91% | +0,37% |
| Alquiler: índice IPVA general | +17,33% | −7,93% |

La tasación media nacional cayó un 29,53% entre el máximo anual de 2008 y el
mínimo de 2014, y subió un 45,78% entre 2014 y 2025. Las tablas territoriales
incluyen fechas, extremos del ciclo y cobertura real. El ajuste por IPC empieza en 2002.

![Perspectiva histórica nacional](reports/figures/history/01_national_long_history.svg)

### Ventana reciente complementaria: 2021–2024

| Medida nacional | Cambio nominal | Cambio ajustado por IPC |
| --- | ---: | ---: |
| Compra: índice IPV | +21,02% | +4,93% |
| Alquiler: índice IPVA | +9,07% | −5,43% |

El IPC subió un 15,33%. El IPVA de contratos nuevos creció un 19,30%, frente al
7,49% de contratos existentes. Las series fiscales y los índices de alquiler
no equivalen al precio anunciado para quien busca una vivienda hoy.

![Compra, alquiler e inflación en una ventana común](reports/figures/block01/03_indexed_comparison.png)

## Qué contiene el bloque de precios

| Parte | Gráficas y resultados |
| --- | --- |
| Evolución nacional | Tasación €/m², transacciones €/vivienda, alquiler IPVA, cambios anuales y acumulados |
| Gobierno nacional | Franjas políticas y cambios entre años completos dentro de cada presidencia |
| Inflación | Compra y alquiler nominales y reales en una ventana común |
| Perfiles territoriales | Muestra fija de 30 grandes ciudades, periferias y casos de costa e interior |
| Comunidades | Mapas de nivel 2024 y crecimiento 2011–2024; mapa de calor anual |
| Presidencias autonómicas | Paneles de las 17 comunidades y tabla de cambios por intervalo |
| Provincias y municipios | Mapas de precio y crecimiento, alquiler por vivienda y casos locales |
| Lectura política | Resultados observados por presidencia; contratos nuevos frente a existentes |

Los datos proceden de **INE, MIVAU, Senado y CartoCiudad**. Se conservan sus
conceptos originales: transacciones, tasaciones y medianas fiscales se distinguen.
Las franjas autonómicas identifican el partido de la presidencia, **no todos los
socios del gabinete**. Coincidir con un gobierno no demuestra el efecto de sus políticas.

Navarra tiene alquiler fiscal desde 2021 y País Vasco desde 2024 en esta publicación.
Los mapas municipales y perfiles describen una selección explícita de 30 casos,
sin presentarla como representativa de todos los municipios españoles.

## Reproducir el análisis

Python 3.11 o posterior. Desde la raíz del repositorio:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts/run_block01.py
python scripts/run_price_history.py
jupyter lab
```

Abrir primero `notebooks/01b_price_history.ipynb`; el análisis reciente está en
`notebooks/01_prices.ipynb`. Los snapshots están versionados: no se necesita
acceso a internet para generar figuras y resultados. El notebook incluye salidas
ya ejecutadas; genera también imágenes temporales para mostrarlas al volver a ejecutarlo.

Para reconstruir las extracciones desde las publicaciones originales, con internet:

```bash
python scripts/build_block01_data.py
python scripts/run_block01.py
```

La descarga fiscal original ocupa aproximadamente 71 MB. Los originales se almacenan
en `data/raw/` y se reutilizan si ya existen; una publicación futura puede cambiar
las URL o el formato. Los snapshots preservan el corte utilizado en este informe.

Validación:

```bash
ruff check src scripts tests
python scripts/check_project.py
python -m unittest discover -s tests -v
python scripts/check_notebooks.py
```

## Organización y próximos bloques

| Carpeta | Contenido |
| --- | --- |
| `notebooks/` | Análisis ordenados; bloque 01 ejecutado, demás bloques preparados |
| `src/spain_housing/` | Indicadores y análisis reutilizable |
| `scripts/` | Descarga, extracción, generación de resultados y validación |
| `data/snapshots/block01/` | Tablas extraídas y geometrías del corte utilizado |
| `data/metadata/` | Registro de fuentes, archivos y presidencias |
| `docs/` | Metodología, alcance, catálogo de figuras e hipótesis |
| `reports/` | Informe, figuras y tablas publicadas |
| `tests/` | Pruebas de fórmulas, cobertura y límites temporales |

Pendientes: población y hogares; oferta y tenencia; propiedad y concentración;
accesibilidad económica; evaluación de medidas legales; modelado y síntesis.
Véanse [plan de investigación](docs/research_plan.md), [metodología](docs/methodology.md)
y [especificación del primer bloque](docs/block_01_prices.md).

## Licencias y atribución

Código: [MIT](LICENSE). Las fuentes externas conservan sus términos propios.
Las geometrías proceden de Click That 'Hood; véanse las
[atribuciones y licencia de terceros](data/snapshots/block01/THIRD_PARTY_NOTICES.md).
