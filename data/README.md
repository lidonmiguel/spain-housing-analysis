# Datos y reproducción

`raw/`, `interim/` y `processed/` contienen descargas o trabajo local y están ignorados
por Git. `snapshots/block01/` contiene las extracciones reales necesarias para
reproducir el informe sin acceso a internet. No contiene microdatos personales.

## Corte del bloque 01: 6 de octubre de 2026

| Snapshot | Concepto y cobertura |
| --- | --- |
| `purchase_index.csv` | IPV, compra efectiva, medias anuales de cuatro trimestres, 2007–2025 |
| `rent_general_history.csv` | IPVA general, nacional y comunidades, 2011–2024 (INE 59056) |
| `rent_index.csv` | IPVA, total/nuevos/existentes, 2021–2024 |
| `cpi.csv` | IPC general, medias de doce meses, 2002–2025 |
| `valuations.csv` | Tasación libre €/m², cuatro trimestres por año, 1995–2025 |
| `rental_medians_2011_2017.csv.gz`, `rental_medians_2018_2024.csv.gz` | SERPAVI, medianas vivienda colectiva, 2011–2024 según territorio |
| `municipal_purchase.csv` | Tasación de 30 municipios seleccionados, 2005–2025 |
| `purchase_transaction_total.csv` | Valor medio por transacción de segunda mano libre, trimestral 2004–2026T2 |
| `selected_cities.csv` | Selección, grupos descriptivos y coordenadas oficiales verificadas |
| `governments.csv` | Presidencias autonómicas y etapas del gobierno nacional desde 1995 |
| `communities.geojson`, `provinces.geojson` | Geometrías ilustrativas simplificadas, vintage 2014 |

Navarra: alquiler desde 2021; País Vasco: desde 2024. La cobertura municipal depende
del año y de la medida. No se imputa una variación cuando falta uno de sus extremos.
El fichero ministerial duplica exactamente las tasaciones de Navarra: se deduplican
antes de comprobar los cuatro trimestres. Las comunidades uniprovinciales y ciudades
autónomas reutilizan la observación del territorio idéntico, marcado `territory_reuse`.

`source_manifest.json` conserva URL, SHA-256 y recuperación de las fuentes originales.
Para CartoCiudad, la huella corresponde a la respuesta API original; se guarda solo
la selección de atributos requerida, no toda la geometría de la respuesta.
Las tablas mantienen códigos territoriales, años, conceptos y unidades; los índices
usan la base indicada en cada publicación. El análisis los rebasa cuando los compara.

`python scripts/build_block01_data.py` descarga fuentes faltantes, verifica códigos
del geocodificador, extrae tablas y rechaza observaciones ambiguas. Los originales
se conservan en caché: no se reemplazan por una publicación nueva automáticamente.
`python scripts/run_block01.py` reproduce la ventana inicial;
`python scripts/run_price_history.py` genera el histórico ampliado. Ambos usan snapshots.

Metadatos: `source_register.csv` incluye fuentes candidatas para todos los bloques;
`dataset_manifest.csv` registra los originales reales del bloque 01;
`government_register.csv` distingue presidencia, gabinete y apoyos desconocidos.
El registro legal permanece pendiente para el bloque de evaluación de políticas.
