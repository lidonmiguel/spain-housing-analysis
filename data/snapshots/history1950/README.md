# Histórico con horizonte desde 1950

Estos snapshots son extracciones de fuentes reales, no una reconstrucción de precios de 1950.
Compra: BIS 1971–2025; alquiler e IPC: INE 1961–2001 y 2002–2025 por separado.
Los años anteriores quedan vacíos en `reports/tables/since1950/annual_coverage_1950_2025.csv`.

| Archivo | Concepto | Base y cobertura |
| --- | --- | --- |
| `purchase_bis.csv` | Serie seleccionada BIS nominal/real | 2010 = 100; medias de cuatro trimestres completos |
| `rental_cpi_segments.csv` | Componente alquiler del IPC e IPC general | Base 1992 hasta 2001; base 2025 desde 2002; medias de doce meses |
| `source_manifest.json` | Originales, URL, SHA-256 y fechas | Incluye metodología BIS y enlaces legales del INE |

## Cambios que afectan a la interpretación

BIS: 1971–1974 estadística OCDE; 1975–1986 precios del área de Madrid (proxy geográfico);
1987–2006 nacional por m²; desde 2007 nacional, índice puro. BIS puede interpolar trimestres
históricos a partir de observaciones anuales. La serie no es homogénea en todo su recorrido.
No se convierten sus índices a euros ni se calculan comparaciones nacionales usando el proxy.

INE: el sistema cambió en 2002. Se conservan segmentos separados sin asumir un coeficiente
no verificado. El cambio de 2002 y los acumulados que cruzan ese corte quedan sin calcular.
La media anual de alquiler de 1961–2001 se coteja con la tabla 203 publicada por INE.

El IPC de alquiler y el IPVA fiscal son indicadores distintos. IPVA se mantiene en el
análisis 2011–2024; no se empalma con el componente alquiler del IPC.

## Atribución y condiciones

Fuentes nacionales y BIS Residential Property Price database:
https://data.bis.org/topics/RPP (series Q.ES.N.628 y Q.ES.R.628).
Documentación: https://www.bis.org/statistics/pp_selected_documentation.pdf.
Uso de estadísticas BIS sujeto a https://data.bis.org/help/legal.
Datos INE: tablas 196, 203, 268, 24079 y 24077; https://www.ine.es/aviso_legal.
La licencia MIT del código no modifica las condiciones de las fuentes.

## Reproducción

`python scripts/build_history1950_data.py` recupera y extrae los originales.
`python scripts/run_history1950.py` reproduce figuras y tablas desde estos snapshots.
Se excluyen años parciales de 2026. No se requiere internet para el análisis versionado.
