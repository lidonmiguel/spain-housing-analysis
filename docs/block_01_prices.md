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
- Salarios bruto y neto: Eurostat `earn_nt_net`, España, euros, persona soltera
  sin hijos al 100 % del salario de referencia, 2000–2023. Vivienda de referencia
  de 80 m² y salarios en euros nominales y constantes de 2023, sin base 100.
  Dos gráficas adicionales muestran tasa de vivienda menos tasa salarial en puntos
  porcentuales, 2003–2023, con el mismo color y escala. El neto es un perfil fiscal,
  no el neto medio observado. 2024 se excluye por ruptura y valores anómalos;
  2025 no se encadena a través de esa ruptura. No se mezcla con la fuente EAES.
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

23 figuras y tablas en `reports/figures/block01/` y `reports/tables/block01/`.
Informe principal: `reports/block_01_prices.md`; informe salarial:
`reports/block_01_housing_salary.md`. Notebook unificado: `01_prices.ipynb`, con cobertura y mandatos integrados. `run_analysis` reproduce el bloque completo y llama
a `salary_analysis.run_salary_analysis` para las siete figuras salariales; también integra las tres figuras de `long_history`.
El notebook reutiliza este módulo. `housing_salary_comparison.csv` guarda importes;
`housing_salary_variation_gap.csv` guarda diferencias de tasas en puntos porcentuales.

Eurostat se conserva en `salary_eurostat.json`; su selección, política de exclusión
y SHA-256 están en `salary_eurostat_source.json`. La EAES del INE es una fuente
alternativa conservada: `build_block01_salary_data.py` normaliza su CSV original,
pero no reconstruye ni actualiza Eurostat.

No se incluyen resultados de alquiler en el bloque 1. Se conservan los snapshots
originales y su trazabilidad. Comparar vivienda y salarios no sustituye un análisis
completo de accesibilidad ni identifica causas.
