# Vivienda y salario medio en España, 2008–2024

La tasación nacional de vivienda libre por m² (MIVAU) se compara con la ganancia
media bruta anual por trabajador de la EAES del INE (tabla 28185, ambos sexos,
secciones B–S y todas las nacionalidades). No es salario mediano, neto ni renta
por habitante. Cambios en la composición del empleo pueden afectar a la media.

Las dos figuras del notebook `01_prices.ipynb` utilizan base común 2008 = 100,
el mismo periodo, colores y límites verticales. La segunda divide ambos índices
nominales por el mismo IPC nacional medio anual, relativo a 2008. No se extrapola
el salario de 2025. Los valores originales e índices se guardan en
`reports/tables/block01/housing_salary_comparison.csv`.

| Serie | Cambio nominal 2008–2024 | Cambio descontado el IPC |
|---|---:|---:|
| Vivienda, tasación €/m² | −7,60 % | −30,78 % |
| Salario medio bruto anual | +34,99 % | +1,12 % |

El salario medio bruto anual de 2024 es 29.540,26 €. El cociente vivienda/salario,
indexado con base 2008 = 100, termina en 68,45 (−31,55 %). Este cociente es idéntico
en términos nominales y reales porque el deflactor común se cancela.

La base de 2008 está próxima al máximo del ciclo de vivienda. Estos resultados
no significan que la vivienda haya bajado desde 2000 ni que la accesibilidad
haya mejorado en todos los territorios o para todos los hogares. El cociente
por m² y salario bruto no incluye superficie, impuestos, ahorro, tipos de interés
ni ingresos conjuntos del hogar. No identifica causas de los precios.

Fuentes: [INE, tabla 28185](https://www.ine.es/jaxiT3/Tabla.htm?t=28185),
[EAES 2024](https://www.ine.es/dyngs/Prensa/EAES2024.htm), tasación MIVAU e IPC
nacional del snapshot original del bloque 1. La selección, fecha de recuperación
y SHA-256 se conservan en `data/snapshots/block01/salary_source.json` y en el
manifiesto de datasets. El CSV original se conserva en `data/raw/block01/ine_eaes_28185.csv`.

Reproducción: `python scripts/build_block01_salary_data.py` reconstruye el
snapshot salarial desde el CSV conservado; `--refresh` vuelve a descargarlo.
Ejecutar las celdas de la sección 2.1 del notebook regenera las figuras 16 y 17
y la tabla. El generador original del bloque mantiene sus 13 figuras.
