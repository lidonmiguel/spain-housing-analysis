"""1950 analytical horizon with verified coverage and explicit historical breaks."""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from spain_housing.prices_analysis import BUY, RENT, annual_changes, style


def rental_changes(frame):
    """Calculate changes within each CPI system; leave the 2002 bridge unobserved."""
    rows = []
    for segment, data in frame.groupby("segment"):
        rent = data[data.metric == "rent_cpi"].set_index("year").value.sort_index()
        cpi = data[data.metric == "cpi_general"].set_index("year").value.sort_index()
        real = rent / cpi.reindex(rent.index)
        rows.append(
            pd.DataFrame(
                {
                    "year": rent.index,
                    "segment": segment,
                    "nominal_pct": annual_changes(rent).to_numpy(),
                    "real_pct": annual_changes(real).to_numpy(),
                }
            )
        )
    return pd.concat(rows, ignore_index=True).sort_values("year")


def compare_window(purchase, rental, first, last):
    """Same period, base and annual CPI; reject unverified rental-system splicing."""
    selected = rental[rental.year.between(first, last)]
    if selected.segment.nunique() != 1:
        raise ValueError("Window crosses the unverified 2001/2002 rental bridge")
    p = purchase[purchase.metric == "purchase_nominal"].set_index("year").value.sort_index()
    r = selected[selected.metric == "rent_cpi"].set_index("year").value.sort_index()
    cpi = selected[selected.metric == "cpi_general"].set_index("year").value.sort_index()
    years = list(range(first, last + 1))
    if any(not set(years) <= set(s.dropna().index) for s in [p, r, cpi]):
        raise ValueError("Comparison requires every observed year in its declared window")
    result = pd.DataFrame(index=years)
    result.index.name = "year"
    for name, s in [("purchase", p), ("rent", r)]:
        result[name + "_nominal"] = s.loc[years] / s.loc[first] * 100
        result[name + "_real"] = result[name + "_nominal"] / (cpi.loc[years] / cpi.loc[first])
    result["cpi"] = cpi.loc[years] / cpi.loc[first] * 100
    return result


def run_long_history(root):
    root = Path(root)
    snapshot = root / "data/snapshots/history1950"
    figures = root / "reports/figures/since1950"
    tables = root / "reports/tables/since1950"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    purchase = pd.read_csv(snapshot / "purchase_bis.csv")
    rental = pd.read_csv(snapshot / "rental_cpi_segments.csv")
    rates = rental_changes(rental)
    rates.to_csv(tables / "rental_annual_changes.csv", index=False, float_format="%.8f")
    p = purchase[purchase.metric == "purchase_nominal"].set_index("year").value
    pr = purchase[purchase.metric == "purchase_real"].set_index("year").value
    r = rental[rental.metric == "rent_cpi"].set_index("year").value
    segments = rental[rental.metric == "rent_cpi"].set_index("year").segment
    coverage = pd.DataFrame(index=range(1950, 2026))
    coverage.index.name = "year"
    coverage["purchase_nominal_2010_100"] = p
    coverage["purchase_real_2010_100"] = pr
    coverage["purchase_scope"] = (
        purchase[purchase.metric == "purchase_nominal"].set_index("year").coverage
    )
    coverage["rent_native_index"] = r
    coverage["rent_system"] = segments
    coverage["rent_nominal_annual_pct"] = rates.set_index("year").nominal_pct
    coverage["rent_real_annual_pct"] = rates.set_index("year").real_pct
    coverage.to_csv(tables / "annual_coverage_1950_2025.csv", float_format="%.8f")
    paths = []

    def save(fig, name):
        fig.tight_layout(rect=[0, 0.035, 1, 0.96])
        fig.text(
            0.01,
            0.008,
            "Fuentes: BIS (compra) e INE (alquiler e IPC) · años completos · huecos sin imputar",
            fontsize=8,
            color="#555",
        )
        path = figures / name
        with plt.rc_context({"svg.fonttype": "none", "svg.hashsalt": "housing-since1950"}):
            fig.savefig(path, metadata={"Date": None})
        plt.close(fig)
        paths.append(path)

    fig, ax = plt.subplots(figsize=(14, 4))
    intervals = [
        (0, 1971, 1974, "#8a8a8a", "Compra: histórico OCDE"),
        (0, 1975, 1986, "#c99a43", "Compra: proxy del área de Madrid"),
        (0, 1987, 2006, BUY, "Compra: nacional por m²"),
        (0, 2007, 2025, "#235aa0", "Compra: nacional, índice puro"),
        (1, 1961, 2001, RENT, "Alquiler: IPC base 1992"),
        (1, 2002, 2025, "#b24b13", "Alquiler: otro sistema IPC"),
    ]
    for row, start, end, color, title in intervals:
        ax.broken_barh([(start, end + 1 - start)], (row - 0.3, 0.6), facecolors=color)
        ax.text(
            (start + end + 1) / 2,
            row,
            title.replace("Compra: ", "")
            .replace("Alquiler: ", "")
            .replace("histórico OCDE", "OCDE")
            .replace("proxy del área de Madrid", "Madrid\n(proxy)"),
            ha="center",
            va="center",
            fontsize=8,
            color="white",
            wrap=True,
        )
    ax.broken_barh([(1950, 21)], (-0.3, 0.6), facecolors="#e7e7e7")
    ax.broken_barh([(1950, 11)], (0.7, 0.6), facecolors="#e7e7e7")
    ax.text(1960.5, 0, "Sin datos verificados", ha="center", va="center", fontsize=8, color="#555")
    ax.text(1955.5, 1, "Sin datos\nverificados", ha="center", va="center", fontsize=8, color="#555")
    ax.set(
        yticks=[0, 1],
        yticklabels=["Compra", "Alquiler"],
        xlim=(1950, 2026),
        xticks=[1950, 1961, 1971, 1987, 2002, 2007, 2025],
        ylim=(-0.8, 1.7),
        title="Objetivo desde 1950: cobertura efectiva y cambios de fuente",
    )
    ax.grid(axis="x", alpha=0.2)
    save(fig, "01_coverage_since1950.svg")

    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True, sharey=True)
    styles = [
        (1971, 1974, "#777", ":", "Histórico OCDE"),
        (1975, 1986, "#c99a43", "--", "Área de Madrid (proxy)"),
        (1987, 2006, BUY, "-", "Nacional, por m²"),
        (2007, 2025, "#235aa0", "-", "Nacional, índice puro"),
    ]
    high = math.ceil(max(p.max(), pr.max()) / 25) * 25
    for ax, series, title in [
        (axes[0], p, "Compra nominal: serie seleccionada del BIS, 1971–2025"),
        (axes[1], pr, "Compra real: deflactada por IPC por el BIS, 1971–2025"),
    ]:
        for start, end, color, line, label in styles:
            s = series.loc[start:end]
            ax.plot(s.index, s, color=color, ls=line, lw=2.4, label=label)
        ax.axvspan(1950, 1971, color="#e7e7e7", alpha=0.6)
        ax.text(1960, high * 0.45, "Sin datos\nverificados", ha="center", color="#666")
        ax.axvspan(1975, 1987, color="#c99a43", alpha=0.08)
        ax.axhline(100, color="#555", ls=":", lw=0.8)
        ax.set(xlim=(1950, 2026), ylim=(0, high), xticks=range(1950, 2026, 10))
        style(ax, title, "Índice BIS: 2010 = 100")
        ax.legend(loc="upper left", ncol=2, fontsize=8)
    save(fig, "02_purchase_bis_nominal_real.svg")

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True, sharey=True)
    limit = math.ceil(max(rates.nominal_pct.abs().max(), rates.real_pct.abs().max()) / 5) * 5
    for ax, col, title in [
        (axes[0], "nominal_pct", "Alquiler IPC: variación nominal anual"),
        (axes[1], "real_pct", "Alquiler IPC: variación anual descontando IPC general"),
    ]:
        # Separate plotting calls leave the 2001/2002 bridge genuinely undrawn.
        for segment, data in rates.groupby("segment"):
            ax.plot(data.year, data[col], color=RENT, lw=2, label=segment.replace("_", "–"))
        ax.axvspan(1950, 1962, color="#e7e7e7", alpha=0.6)
        ax.axvline(2002, ls="--", color="#777", lw=1)
        ax.axhline(0, color="#555", lw=0.8)
        ax.set(xlim=(1950, 2026), ylim=(-limit, limit), xticks=range(1950, 2026, 10))
        style(ax, title, "% interanual · 2002 sin enlace verificado")
    save(fig, "03_rental_yearly_nominal_real.svg")

    comparisons = []
    for first, last in [(1987, 2001), (2002, 2025)]:
        frame = compare_window(purchase, rental, first, last)
        frame.to_csv(tables / f"comparison_{first}_{last}.csv", float_format="%.8f")
        fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
        hi = math.ceil(frame.max().max() / 25) * 25 + 25
        for ax, suffix, title in [
            (axes[0], "nominal", "Nominal"),
            (axes[1], "real", "Ajustado por IPC"),
        ]:
            for metric, label, color, offset in [
                ("purchase", "Compra BIS", BUY, 10),
                ("rent", "Alquiler IPC", RENT, -10),
            ]:
                s = frame[metric + "_" + suffix]
                ax.plot(s.index, s, label=label, color=color, lw=2.3)
                ax.annotate(
                    f"{s.loc[last] - 100:+.1f}%",
                    (last, s.loc[last]),
                    xytext=(6, offset),
                    textcoords="offset points",
                    color=color,
                    fontsize=9,
                )
                comparisons.append(
                    dict(
                        first_year=first,
                        last_year=last,
                        metric=metric,
                        measure=suffix,
                        change_pct=s.loc[last] - 100,
                    )
                )
            if suffix == "nominal":
                ax.plot(frame.index, frame.cpi, "--", color="#777", label="IPC general")
            ax.axhline(100, color="#555", lw=1, ls=":")
            ax.set(xlim=(first, last + 3), ylim=(0, hi))
            ax.set_xticks(sorted(set(range(first, last + 1, 3)) | {last}))
            ax.tick_params(axis="y", labelleft=True)
            style(ax, f"{title}: {first}–{last}", f"{first} = 100 · misma escala en ambos paneles")
            ax.legend(loc="upper left")
        save(fig, f"04_comparison_{first}_{last}.svg")
    findings = pd.DataFrame(comparisons)
    findings.to_csv(tables / "period_results.csv", index=False, float_format="%.8f")
    rows = []
    for first, last in [(1987, 2001), (2002, 2025)]:
        for metric, label in [("purchase", "Compra BIS"), ("rent", "Alquiler IPC")]:
            f = findings[(findings.first_year == first) & (findings.metric == metric)].set_index(
                "measure"
            )
            rows.append(
                f"| {first}–{last} | {label} | {f.loc['nominal', 'change_pct']:+.2f}% | "
                f"{f.loc['real', 'change_pct']:+.2f}% |"
            )
    result_table = "\n".join(rows)
    report = f"""# Vivienda desde 1950: horizonte histórico y datos efectivamente recuperados

**1950 es el inicio solicitado del análisis, no el primer dato disponible.** La cobertura
verificada empieza en 1961 para alquiler e IPC y en 1971 para la serie seleccionada de compra.
Se publican los años vacíos desde 1950. No son ceros, ni precios constantes, ni estimaciones.

![Cobertura efectiva](figures/since1950/01_coverage_since1950.svg)

## Compra: 1971–2025, con cambios de cobertura

![Compra nominal y real](figures/since1950/02_purchase_bis_nominal_real.svg)

Fuente: [BIS, series seleccionadas](https://data.bis.org/topics/RPP). El tramo 1971–1974 usa
estadísticas históricas de la OCDE; 1975–1986 usa precios del área de Madrid; 1987–2006,
precios nacionales por m²; desde 2007, índice nacional de precios puro. El proxy madrileño
se dibuja discontinuo y diferenciado. La frecuencia trimestral histórica puede incluir
interpolaciones del proveedor. No se trata de una medición nacional homogénea desde 1971.

Los índices nominales y reales mantienen la base BIS 2010 = 100 y una escala vertical común.
Son índices, no €/m² o €/vivienda. El índice real oficial BIS utiliza el IPC; las comparaciones
por periodo de abajo deflactan las medias anuales con el mismo IPC anual para compra y alquiler.

## Alquiler: recuperación real desde 1961

![Cambios anuales del alquiler](figures/since1950/03_rental_yearly_nominal_real.svg)

Se recuperaron los índices mensuales históricos del INE (tabla 196, alquiler; tabla 268,
IPC general), 1961–2001. Se verificó la media anual de alquiler contra la tabla 203.
Desde 2002 se usan las tablas 24079 y 24077. Se exigen doce meses observados para cada año.

La base 1992 y el sistema posterior a 2002 se conservan por separado. El INE documenta una
ruptura metodológica en 2002: [enlace legal](https://www.ine.es/ipc01/enlaces.htm).
No se ha verificado un coeficiente de enlace para estas extracciones: el cambio anual de 2002
queda vacío y no se calcula un cambio acumulado entre ambos sistemas.

El alquiler de esta sección es el **componente de alquiler del IPC**, distinto del **IPVA**
fiscal usado en la comparación 2011–2024. No se sustituyen ni se mezclan ambos indicadores.
El IPC de alquiler no representa el precio anunciado ni exclusivamente contratos nuevos.

## Comparaciones nacionales dentro de periodos coherentes

Compra se compara desde 1987 para evitar usar Madrid como si representara toda España.
Ambas series tienen la misma ventana, base y deflactor dentro de cada comparación.
Cada par nominal/real comparte exactamente su escala vertical. Las dos ventanas tienen
bases y duraciones diferentes: sus porcentajes no constituyen un ranking entre periodos.

| Periodo | Medida | Cambio nominal | Cambio real |
| --- | --- | ---: | ---: |
{result_table}

![1987–2001](figures/since1950/04_comparison_1987_2001.svg)
![2002–2025](figures/since1950/04_comparison_2002_2025.svg)

El resultado 2011–2024 del [análisis reciente](block_01_price_history.md) no describe
lo ocurrido desde 1950. El cambio de año inicial y de indicador modifica la pregunta.
Deflactar precios tampoco mide accesibilidad: para eso se requieren ingresos coherentes.

## Qué sigue sin estar verificado

- Compra nacional comparable 1950–1970 y alquiler nacional 1950–1960.
- Enlace cuantitativo del alquiler entre 2001 y 2002.
- Datos anuales originales de la reconstrucción académica 1959–1986: se localizó el
  [estudio de Taltavull y Juárez (2015)](https://recyt.fecyt.es/index.php/CyTET/article/view/76437),
  pero no se incorporan precios modelados que no se hayan extraído y validado.

La búsqueda incluyó archivos del INE, documentación del Banco de España, BIS e investigación.
Esto delimita lo recuperado, no demuestra que no existan otras fuentes históricas.

## Reproducción

- [Notebook con código y resultados](../notebooks/01c_prices_since_1950.ipynb).
- [Cobertura anual 1950–2025 y tablas](tables/since1950/).
- [Fuentes originales y SHA-256](../data/snapshots/history1950/source_manifest.json).
- [Metodología y atribución](../data/snapshots/history1950/README.md).

`python scripts/run_history1950.py` reproduce cinco figuras y las tablas sin internet.
`python scripts/build_history1950_data.py` vuelve a extraer las fuentes originales.
"""
    (root / "reports/block_01_since_1950.md").write_text(report, encoding="utf-8")
    return paths, findings
