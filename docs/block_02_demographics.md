# Bloque 2 · Demografía, construcción y precio

## Pregunta

¿Ha aumentado la demanda de vivienda más rápido que la oferta y qué parte del crecimiento demográfico procede de la migración exterior?

## Datos y cobertura

Se reutiliza la tasación media anual de vivienda libre del bloque 1, sin mezclarla con IPV, anuncios o importes por operación. Objetivo 2000–2025; el parque publicado empieza en 2001 y la comparación conjunta en 2001. Construcción: 2008–2025. Hogares ECP: stocks de cierre 2020–2025 y variaciones 2021–2025. Saldos demográficos: 2008–2024. Lugar de nacimiento: stocks de cierre 2001–2025.

El cierre del año t corresponde al 1 de enero de t+1 para población y hogares, y al 31 de diciembre para viviendas. El precio es una media anual nominal. Se mantienen las observaciones definitivas; se añade la publicación provisional solo para fechas posteriores. El cierre de población y lugar de nacimiento de 2025 es provisional. Hogares y estimaciones de vivienda pueden revisarse.

## Transformaciones y validaciones

- CSV originales comprimidos con gzip determinista; SHA-256 de bytes originales y snapshots.
- Números españoles: separador de miles y coma decimal. Ausencias conservadas.
- Adultos = población total menos edades simples 0–17; se exigen las 18 edades por fecha.
- Parque nacional = suma de 50 provincias y unidad conjunta Ceuta/Melilla; 51 unidades completas por año.
- Construcción: total nacional, libres + protegidas, 12 meses completos por estado y tipo; contraste con suma provincial, sin doble conteo.
- Índices: una sola base común por panel; se excluyen años sin observaciones de todas las series incluidas.
- Diferencias anuales: solo entre años consecutivos. No se puentean años ausentes.
- Tasas demográficas: se conservan las tasas oficiales por 1.000 habitantes y el residuo entre crecimiento y componentes. Cambio de estadística migratoria en 2021 señalado.
- En los primeros años, los grupos por nacimiento pueden diferir una persona del total por redondeo publicado; no se reasigna.
- Comparación regional: 17 comunidades, mismos extremos 2020–2025 y escala porcentual. Ceuta/Melilla excluidas por la agregación conjunta del parque.

## Interpretación

Parque total no equivale a oferta anunciada. Viviendas no principales no equivale a viviendas vacías. Adultos no equivale a hogares independientes. La creación neta de hogares menos viviendas terminadas no es un déficit exacto: omite otros cambios del parque, uso de viviendas existentes y localización. Hogares observados no recoge toda la demanda latente.

Saldo natural incluye nacimientos y defunciones de todos los residentes. Saldo migratorio incluye españoles y extranjeros. Lugar de nacimiento no equivale a nacionalidad, y sus variaciones no son llegadas netas. Las figuras describen crecimiento y coincidencias; no identifican efectos causales sobre precios ni atribuyen responsabilidad a gobiernos o personas.

## Reproducir

`python scripts/run_block02.py` reproduce sin red las 13 figuras y cuatro tablas de análisis. `notebooks/02_demographics.ipynb` incluye código, salidas y explicación por figura. Para actualizar fuentes: `python scripts/build_block02_data.py --refresh`; revisar publicaciones y cobertura antes de regenerar. Los resultados de esta entrega corresponden a los snapshots del 6 de octubre de 2026.
