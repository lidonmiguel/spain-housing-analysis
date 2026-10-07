# Bloque 1 · Precio de compra de vivienda

## Pregunta

¿Cómo ha cambiado el precio de compra de vivienda en España desde 2000, cuándo y dónde?

## Una medida principal

Tasación media de vivienda libre en €/m², MIVAU, medias de cuatro trimestres completos.
Ventana nacional, autonómica y provincial: 2000–2025. La tasación es una valoración,
no el importe anunciado ni el precio efectivo de cada operación. El IPV y los importes
por vivienda quedan como fuentes originales, sin mezclarse en las figuras principales.

## Comparaciones y cobertura

- IPC: 2002–2025; dos índices con base común 2002 = 100.
- Salario medio bruto anual: INE EAES, ambos sexos, secciones B–S, todas las
  nacionalidades, 2008–2024. Vivienda y salario se indexan con base 2008 = 100;
  se muestran dos figuras con la misma escala, nominal y deflactada con el mismo
  IPC nacional medio anual. No se extrapola 2025 ni se confunde media con mediana.
- Municipios: selección explícita de 30 casos, 2005–2025.
- Perfiles: muestras fijas con todos los años observados; media no ponderada de índices locales.
- Mapas: nivel 2025 y variación con extremos fijos; no se rellenan observaciones ausentes.
- Ciclo: máximo dentro de 2000–2008 y mínimo dentro de 2009–2015.

## Gobiernos

Las franjas son contexto temporal. Las comparaciones por presidencia usan años completos
dentro del mandato y excluyen años de transición. Las tablas incluyen fechas, cobertura,
cambio acumulado y tasa anualizada. Se mantienen sin resultado los intervalos con
menos de dos años completos. No se promedian resultados por partido ni se atribuye causalidad.
El año central en el gráfico de mandatos es una posición visual, no una fecha de intervención.

## Entregables

15 figuras y tablas en `reports/figures/block01/` y `reports/tables/block01/`.
Informe principal: `reports/block_01_prices.md`. Notebooks: `01_prices.ipynb` y
`01b_price_history.ipynb`. Ambos scripts usan el mismo generador `run_analysis`
para las 13 figuras originales. Las figuras 16 y 17, y su tabla
`housing_salary_comparison.csv`, se generan en las celdas salariales de `01_prices.ipynb`.
Resumen salarial: `reports/block_01_housing_salary.md`. El snapshot salarial se
reconstruye con `python scripts/build_block01_salary_data.py`; `--refresh` actualiza
el CSV original y su procedencia. El cociente vivienda/salario es invariante al
deflactor común y no equivale al esfuerzo de compra de un hogar. La base 2008,
próxima al máximo inmobiliario, condiciona la lectura del cambio acumulado.
No se incluyen resultados de alquiler en el bloque 1. Se conservan los snapshots originales
y su trazabilidad para no destruir fuentes recuperadas.
