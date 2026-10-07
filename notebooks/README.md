# Notebooks

- `00_data_audit.ipynb`: plantilla de auditoría y alcance de las fuentes.
- `01_prices.ipynb`: bloque 1, compra desde 2000, IPC y salarios bruto/neto;
  utiliza los generadores de `src/spain_housing/`, con 17 figuras.
- `01b_price_history.ipynb`: cobertura, ciclos y gobiernos del mismo bloque.
- `02_demographics.ipynb`: bloque 2 ejecutado, con seis figuras.
- `03_supply_and_tenure.ipynb` a `08_hypothesis_review.ipynb`: bloques pendientes;
  sus plantillas no representan análisis completados.

Abrir desde la raíz o desde `notebooks/`; reiniciar el kernel y ejecutar todas las celdas.
Los snapshots permiten reproducir sin internet. Para regenerar entregables sin Jupyter:
`python scripts/run_block01.py` y `python scripts/run_block02.py`.
