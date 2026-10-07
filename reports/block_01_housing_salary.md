# Vivienda y salarios bruto y neto en España, 2002–2023

La vivienda es una tasación nacional MIVAU multiplicada por **80 m²**, un supuesto
fijo de superficie, no el tamaño medio ni el importe de una compraventa.
Bruto y neto proceden de [Eurostat, earn_nt_net](https://ec.europa.eu/eurostat/databrowser/view/earn_nt_net/default/table?lang=en):
España, euros, persona soltera sin hijos al 100 % del salario de referencia.
El neto incorpora impuestos y cotizaciones de ese perfil; no es el neto medio
observado de todos los trabajadores. No se mezcla esta fuente con INE EAES.

## Importes y cambios acumulados

![Importes nominales](figures/block01/16_housing_salary_nominal.png)
![Euros constantes](figures/block01/17_housing_salary_real.png)

Los dos paneles conservan importes en euros y escalas distintas para vivienda y
salarios. La segunda figura usa euros de 2023, deflactados por el mismo IPC.
No se normalizan las series a base 100.

| Serie | Cambio nominal 2002–2023 | Cambio descontado IPC |
| --- | ---: | ---: |
| Vivienda de 80 m² | +61.65 % | +2.41 % |
| Salario bruto anual | +62.63 % | +3.03 % |
| Salario neto anual · perfil fiscal | +59.51 % | +1.05 % |

## Diferencia de variación anual

![Vivienda frente a bruto](figures/block01/18_housing_salary_gross_gap.png)
![Vivienda frente a neto](figures/block01/19_housing_salary_net_gap.png)

Una barra por año, mismo color y escala: **tasa de vivienda menos tasa salarial**,
en puntos porcentuales. Cada tasa es (valor actual / valor anterior − 1) × 100.
Las barras cubren 2003–2023; el primer año solo sirve para calcular la tasa.
Una barra positiva indica que vivienda sube más o cae menos; una negativa,
que el salario sube más o cae menos. No es el porcentaje de cambio del cociente.

## Cobertura y reproducción

Se conserva la respuesta original en `data/snapshots/block01/salary_eurostat.json`
y la política de comparación y huella SHA-256 en `salary_eurostat_source.json`.
2024 está marcado como ruptura y contiene importes anómalos; se excluye junto a
2025, sin extrapolar ni encadenar a través de la ruptura. El snapshot EAES y su
script de normalización se conservan como fuente alternativa, no usada aquí.

`python scripts/run_block01.py` reproduce las cuatro figuras, este informe y las
tablas `housing_salary_comparison.csv` y `housing_salary_variation_gap.csv`, sin red.
El notebook utiliza las mismas funciones de `src/spain_housing/salary_analysis.py`.
La comparación no mide por sí sola accesibilidad: faltan ingresos del hogar,
gastos, ahorro, financiación y diferencias territoriales; no identifica causas.
