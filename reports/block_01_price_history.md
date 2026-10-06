# Bloque 1: perspectiva histórica ampliada

La serie de compra por tasación empieza en **1995**, las transacciones por vivienda en **2004**,
el IPV en **2007** y el alquiler general IPVA en **2011**. Se usan años completos: compra
hasta **2025** y alquiler hasta **2024**. Los trimestres de 2026 quedan fuera de las medias anuales.

## Evolución nacional y contexto político

![Series largas](figures/history/01_national_long_history.svg)

Las medidas conservan sus definiciones: tasación de vivienda libre por m², importe medio de
transacciones de segunda mano libre por vivienda e índice fiscal de alquiler. No hay una serie
nacional comparable de alquiler en €/vivienda desde 1995; no se inventa agregando medianas locales.

![Gobiernos nacionales](figures/history/02_national_governments.svg)

Las franjas identifican presidencias o gabinetes nacionales
y el partido de la presidencia autonómica.
La coincidencia temporal no estima efectos causales.
La tabla por gobierno excluye años de transición,
expone la duración y anualiza el cambio; los periodos sin dos años completos quedan sin resultado.
Se conservan intervalos históricos del Senado; pueden existir interinidades breves no detalladas.

## Vivienda frente a los precios generales: 2011–2024

![Vivienda frente a los precios generales](figures/history/03_common_nominal_real.svg)

Comparamos cuánto han subido la compra y el alquiler respecto a los precios generales,
medidos por el IPC. Todas las series parten de 2011 = 100: un valor de 120
representa una subida acumulada del 20 %, no un precio en euros.

Entre 2011 y 2024, la compra aumentó un **27.91%**, el alquiler un **17.33%**
y el IPC un **27.43%**. En este periodo, la compra subió
casi lo mismo que los precios generales y el alquiler creció menos.

El IPC permite comparar la evolución del precio de la vivienda con la de los precios
en general, pero no indica si los ingresos han crecido al mismo ritmo.

![Ciclo e inflación](figures/history/04_cycles_inflation_rates.svg)

El IPC disponible en el snapshot comienza en **2002**: las series reales y sus tablas lo indican.
Los valores reales son euros de 2025 o índices relativos al año base especificado; deflactar no mide
accesibilidad económica, que requiere ingresos. Se utiliza IPC nacional también para territorios.

## Comunidades, provincias y municipios

![Comunidades](figures/history/05_region_long_growth_maps.svg)
![Provincias](figures/history/06_province_long_growth_maps.svg)

Se generalizan los contornos y se omiten islotes menores de aproximadamente 1 km².
Los mapas comparan extremos fijos: 1995–2025 nominal y 2002–2025 real. Las tablas territoriales
indican primer y último dato, cobertura y años ausentes. También identifican máximo anterior a
la crisis **dentro de 1995–2008**, mínimo posterior **dentro de 2009–2015**, caída y recuperación.
Son extremos de ventanas explícitas, no fechas universales del ciclo de todos los territorios.

![Compra autonómica y partidos](figures/history/07_regional_governments_1995.svg)
![Perfiles municipales](figures/history/08_city_profiles_long_history.svg)

Compra municipal: **2005–2025**, selección de 30 casos. Alquiler fiscal por m² y por vivienda:
**2011–2024**, según cobertura. Los perfiles usan una muestra fija con todos los años observados,
media no ponderada de índices locales; el número de ciudades y su composición se publican.
Navarra y País Vasco mantienen sus fechas de inicio fiscal (2021 y 2024). Las tablas de alquiler
no asignan máximos anteriores a 2008 a series que empiezan después.

## Código y resultados reproducibles

- [Notebook con cálculos visibles y resultados](../notebooks/01b_price_history.ipynb).
- [Tablas históricas completas](tables/history/), incluidas cobertura, ciclos y presidencias.
- [Código del análisis](../src/spain_housing/price_history.py).
- [Fuentes originales y SHA-256](../data/snapshots/block01/source_manifest.json).

Ejecutar `python scripts/run_price_history.py` desde la raíz. No requiere descargar fuentes.
La ampliación del IPVA procede de la tabla INE 59056 (general por edificación), sin encadenar
porcentajes redondeados de notas de prensa ni extrapolar contratos nuevos hacia atrás.

