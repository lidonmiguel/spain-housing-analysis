"""Reproduce housing and earnings comparisons from the frozen Eurostat snapshot."""

import hashlib
import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from spain_housing.prices_analysis import annual_changes, load_purchase_data, series_for

HOUSING = "Vivienda de 80 m²"
GROSS = "Salario bruto anual"
NET = "Salario neto anual · perfil fiscal"
NAMES = [
    "16_housing_salary_nominal",
    "17_housing_salary_real",
    "18_housing_salary_gross_gap",
    "19_housing_salary_net_gap",
]


def earnings_series(dataset, code):
    """Decode JSON-stat offsets by named dimensions, rather than fixed positions."""
    required = {"freq": "A", "currency": "EUR", "ecase": "P1_NCH_AW100", "geo": "ES"}
    indices = dataset["dimension"]
    for dimension, category in required.items():
        if indices[dimension]["category"]["index"] != {category: 0}:
            raise ValueError(f"Unexpected earnings selection: {dimension}")
    ids, sizes = dataset["id"], dataset["size"]
    if len(ids) != len(sizes) or set(ids) != set(required) | {"estruct", "time"}:
        raise ValueError("Unexpected earnings dimensions")
    times = indices["time"]["category"]["index"]
    structures = indices["estruct"]["category"]["index"]
    coordinates = {"estruct": structures[code]}
    result, statuses = {}, {}
    for year, position in times.items():
        coordinates["time"] = position
        offset = 0
        for dimension, size in zip(ids, sizes, strict=True):
            offset = offset * size + coordinates.get(dimension, 0)
        result[int(year)] = dataset["value"].get(str(offset), np.nan)
        statuses[int(year)] = dataset.get("status", {}).get(str(offset), "")
    return pd.Series(result).sort_index(), pd.Series(statuses).sort_index()


def extend_salary_cpi(root, cpi):
    """Link annual INE general CPI bases to add 2000 and 2001, without estimates."""
    if 2000 in cpi.index and 2001 in cpi.index:
        return cpi
    folder = Path(root) / "data/snapshots/block01"
    frames = {}
    for table in (278, 259):
        path = folder / f"cpi_historical_{table}.csv"
        metadata = json.loads(path.with_suffix(".json").read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
            raise ValueError(f"Historical CPI checksum mismatch: {table}")
        data = pd.read_csv(path, sep=";", dtype=str)
        data = data[data["Tipo de dato"] == "Media anual"]
        if table == 259:
            data = data[data["Grupos COICOP 2001"] == "\u00cdndice general"]
        data = data.set_index(data.Periodo.astype(int))
        frames[table] = pd.to_numeric(data.Total.str.replace(",", ".", regex=False))
    old = frames[278]
    base2001 = frames[259]
    # Base 2001 means annual average in 2001 = 100; anchor to the existing 2002 value.
    index2001 = cpi.loc[2002] * 100 / base2001.loc[2002]
    extension = pd.Series(
        {2000: index2001 * old.loc[2000] / old.loc[2001], 2001: index2001}, name=cpi.name
    )
    if not np.isfinite(extension).all() or (extension <= 0).any():
        raise ValueError("Invalid linked historical CPI")
    result = pd.concat([extension, cpi]).sort_index()
    if result.index.has_duplicates:
        raise ValueError("Overlapping CPI years")
    return result


def load_salary_comparison(root, purchase=None, cpi=None):
    """Validate provenance and the explicitly reviewed 2000–2023 common window."""
    snapshot = Path(root) / "data/snapshots/block01"
    raw = (snapshot / "salary_eurostat.json").read_bytes().replace(b"\r\n", b"\n")
    policy = json.loads((snapshot / "salary_eurostat_source.json").read_text(encoding="utf-8"))
    if hashlib.sha256(raw).hexdigest() != policy["snapshot_sha256"]:
        raise ValueError("Eurostat salary snapshot checksum mismatch")
    dataset = json.loads(raw)["data"]
    gross, gross_status = earnings_series(dataset, "GRS")
    net, net_status = earnings_series(dataset, "NET")
    if purchase is None or cpi is None:
        values, _, cpi, _ = load_purchase_data(root)
        purchase = series_for(values, level="national")
    cpi = extend_salary_cpi(root, cpi)
    first, last = policy["comparison_window"]
    panel = (
        pd.concat(
            [
                (purchase * 80).rename(HOUSING),
                gross.rename(GROSS),
                net.rename(NET),
                cpi.rename("IPC"),
            ],
            axis=1,
            join="inner",
        )
        .sort_index()
        .loc[first:last]
    )
    if panel.index.has_duplicates or panel.index.tolist() != list(range(first, last + 1)):
        raise ValueError("Missing or duplicated salary comparison years")
    if not np.isfinite(panel.to_numpy()).all() or not panel.gt(0).all().all():
        raise ValueError("Salary comparison requires finite, positive amounts")
    if not panel[NET].le(panel[GROSS]).all():
        raise ValueError("Net earnings exceed gross earnings")
    if (gross_status.loc[panel.index].eq("b") | net_status.loc[panel.index].eq("b")).any():
        raise ValueError("The salary window crosses a flagged series break")
    nominal = panel.drop(columns="IPC")
    real = nominal.div(panel["IPC"] / panel.loc[last, "IPC"], axis=0)
    return panel, nominal, real


def variation_gaps(nominal):
    """Housing annual rate minus each wage annual rate, in percentage points."""
    rates = nominal.apply(annual_changes).dropna(how="any")
    return pd.DataFrame(
        {
            "Vivienda frente a salario bruto": rates[HOUSING] - rates[GROSS],
            "Vivienda frente a salario neto": rates[HOUSING] - rates[NET],
        }
    ).rename_axis("year")


def run_salary_analysis(root, purchase=None, cpi=None, preview_dir=None, vector=False):
    """Write four figures, their numerical tables and the matching Spanish report."""
    root = Path(root)
    figures, tables = root / "reports/figures/block01", root / "reports/tables/block01"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    panel, nominal, real = load_salary_comparison(root, purchase, cpi)
    first, last = int(panel.index.min()), int(panel.index.max())
    panel.join(real.add_suffix(f" · euros de {last}")).to_csv(
        tables / "housing_salary_comparison.csv", index_label="year", float_format="%.8f"
    )
    gaps = variation_gaps(nominal)
    gaps.to_csv(tables / "housing_salary_variation_gap.csv", float_format="%.8f")
    files = []

    def save(fig, name):
        path = figures / f"{name}.png"
        fig.savefig(path, dpi=120, bbox_inches="tight")
        if vector:
            with plt.rc_context({"svg.fonttype": "none"}):
                fig.savefig(figures / f"{name}.svg", metadata={"Date": None})
        if preview_dir is not None:
            preview = Path(preview_dir)
            preview.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, preview / path.name)
        plt.close(fig)
        files.append(path)

    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10}):
        money_format = FuncFormatter(lambda value, position: f"{value:,.0f}".replace(",", "."))
        amounts = pd.concat([nominal, real])
        housing_limit = amounts[HOUSING].max() * 1.16
        wage_limit = amounts[[GROSS, NET]].max().max() * 1.16
        for data, name, title, unit in [
            (nominal, NAMES[0], "Vivienda y salarios · importes nominales", "€ corrientes"),
            (real, NAMES[1], "Vivienda y salarios · ajustados por IPC", f"€ de {last}"),
        ]:
            fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            axes[0].plot(
                data.index,
                data[HOUSING],
                color="#207b8e",
                lw=2.5,
                label="Vivienda de 80 m² · tasación de referencia",
            )
            for column, color in [(GROSS, "#c2692f"), (NET, "#6554a4")]:
                axes[1].plot(data.index, data[column], color=color, lw=2.5, label=column)
            axes[0].set(ylabel=f"Vivienda · {unit}", ylim=(0, housing_limit))
            axes[1].set(ylabel=f"Salarios · {unit}/año", ylim=(0, wage_limit), xlabel="Año")
            for ax in axes:
                ax.set_xlim(first, last + 1)
                ax.yaxis.set_major_formatter(money_format)
                ax.grid(axis="y", alpha=0.2)
                ax.legend(loc="upper left")
            axes[1].set_xticks(list(range(first, last + 1, 2)) + [last])
            fig.suptitle(f"{title}\nEspaña, {first}–{last}", fontsize=15)
            fig.text(
                0.02,
                0.015,
                "MIVAU (tasación × 80 m²) · Eurostat (soltero/a sin hijos, 100 % salario "
                "de referencia) · INE (IPC)\nNeto del perfil fiscal, no media observada "
                "de todos los trabajadores. Escalas distintas por panel.",
                fontsize=9,
                color="#555555",
            )
            fig.tight_layout(rect=(0, 0.065, 1, 0.94))
            save(fig, name)

        # Two separate monetary charts and one full-period percentage comparison.
        for column, name, title, color, ylabel in [
            (
                NET,
                "20_net_salary_history",
                "Evoluci\u00f3n del salario neto anual",
                "#9b626b",
                "Salario neto anual (\u20ac corrientes)",
            ),
            (
                HOUSING,
                "21_housing_value_history",
                "Valor de una vivienda de referencia",
                "#207b8e",
                "Vivienda de 80 m\u00b2 (\u20ac corrientes)",
            ),
        ]:
            series = nominal[column]
            change = (series.iloc[-1] / series.iloc[0] - 1) * 100
            fig, ax = plt.subplots(figsize=(13, 5.8))
            ax.plot(series.index, series, color=color, lw=2.6, marker="o", markersize=4)
            for year in (first, last):
                value = series.loc[year]
                ax.annotate(
                    f"{year}: {value:,.0f} \u20ac".replace(",", "."),
                    (year, value),
                    xytext=(0, 12),
                    textcoords="offset points",
                    ha="center",
                    color=color,
                    fontsize=11,
                    fontweight="bold",
                )
            ax.set(xlabel="A\u00f1o", ylabel=ylabel, ylim=(0, series.max() * 1.2))
            ax.yaxis.set_major_formatter(money_format)
            ax.set_xticks(list(range(first, last, 2)) + [last])
            ax.grid(axis="y", alpha=0.2)
            ax.spines[["top", "right"]].set_visible(False)
            fig.suptitle(title, fontsize=17, fontweight="bold")
            text = f"Espa\u00f1a \u00b7 {first}\u2013{last} \u00b7 Subida total: +{change:.1f} %"
            fig.text(0.09, 0.84, text.replace(".", ","), color=color, fontsize=12)
            note = (
                (
                    "Eurostat: soltero/a sin hijos, 100 % del salario de referencia. "
                    "Neto del perfil fiscal, no salario neto medio observado."
                )
                if column == NET
                else (
                    "MIVAU: tasaci\u00f3n nacional de vivienda libre \u00d7 80 m\u00b2. "
                    "Superficie fija; no es el precio de una compraventa concreta."
                )
            )
            fig.text(
                0.09,
                0.025,
                note + "\nEuros corrientes, sin descontar inflaci\u00f3n. "
                "Comparaci\u00f3n hasta 2023 por anomal\u00eda salarial en 2024.",
                fontsize=9,
                color="#555555",
            )
            fig.tight_layout(rect=(0, 0.12, 1, 0.82))
            save(fig, name)

        cumulative = (
            nominal.loc[last, [HOUSING, NET]] / nominal.loc[first, [HOUSING, NET]] - 1
        ) * 100
        cumulative.rename("change_pct").to_csv(tables / "housing_net_salary_total_change.csv")
        fig, ax = plt.subplots(figsize=(11, 5.6))
        bars = ax.barh(
            ["Vivienda de 80 m\u00b2", "Salario neto anual"],
            cumulative,
            color=["#207b8e", "#9b626b"],
            height=0.48,
        )
        ax.invert_yaxis()
        ax.bar_label(
            bars,
            labels=[f"+{v:.1f} %".replace(".", ",") for v in cumulative],
            padding=8,
            fontsize=15,
            fontweight="bold",
        )
        ax.set(xlabel="Subida total durante el periodo (%)", xlim=(0, cumulative.max() * 1.3))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f} %"))
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="x", alpha=0.18)
        ax.set_axisbelow(True)
        fig.suptitle(
            "Cu\u00e1nto han subido la vivienda y el salario neto", fontsize=17, fontweight="bold"
        )
        fig.text(0.07, 0.84, f"Espa\u00f1a \u00b7 Mismo periodo: {first}\u2013{last}", fontsize=12)
        fig.text(
            0.07,
            0.025,
            "Cambio total = (importe final / importe inicial \u2212 1) \u00d7 100. "
            "No es una tasa anual ni la suma de las subidas anuales.\n"
            "MIVAU y Eurostat \u00b7 Importes nominales. Neto del perfil fiscal "
            "de referencia; no media observada de todos los trabajadores.",
            fontsize=9,
            color="#555555",
        )
        fig.tight_layout(rect=(0, 0.15, 1, 0.8))
        save(fig, "22_housing_net_salary_total_change")

        limit = max(1.0, gaps.abs().max().max() * 1.18)
        for column, name, wage in zip(gaps.columns, NAMES[2:], ["bruto", "neto"], strict=True):
            fig, ax = plt.subplots(figsize=(14, 5))
            gaps[column].plot.bar(ax=ax, color="#207b8e", width=0.7, rot=45)
            ax.axhline(0, color="#555555", lw=1)
            ax.set(
                title=f"Variación de la vivienda frente al salario {wage}",
                xlabel="Año",
                ylabel="Diferencia de variación anual (puntos porcentuales)",
                ylim=(-limit, limit),
            )
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(axis="y", alpha=0.2)
            ax.set_axisbelow(True)
            fig.text(
                0.02,
                0.015,
                "Positivo: la vivienda sube más o cae menos que el salario. "
                "Negativo: el salario sube más o cae menos.\n"
                "MIVAU · Eurostat (perfil fiscal soltero/a sin hijos, 100 % salario "
                "de referencia) · tasas nominales.",
                fontsize=9,
                color="#555555",
            )
            fig.tight_layout(rect=(0, 0.085, 1, 1))
            save(fig, name)

    changes = pd.DataFrame(
        {
            "nominal": (nominal.iloc[-1] / nominal.iloc[0] - 1) * 100,
            "real": (real.iloc[-1] / real.iloc[0] - 1) * 100,
        }
    )
    rows = "\n".join(
        f"| {label} | {changes.loc[label, 'nominal']:+.2f} % | "
        f"{changes.loc[label, 'real']:+.2f} % |"
        for label in nominal.columns
    )
    report = f"""# Vivienda y salarios bruto y neto en España, {first}–{last}

La vivienda es una tasación nacional MIVAU multiplicada por **80 m²**, un supuesto
fijo de superficie, no el tamaño medio ni el importe de una compraventa.
Bruto y neto proceden de [Eurostat, earn_nt_net](https://ec.europa.eu/eurostat/databrowser/view/earn_nt_net/default/table?lang=en):
España, euros, persona soltera sin hijos al 100 % del salario de referencia.
El neto incorpora impuestos y cotizaciones de ese perfil; no es el neto medio
observado de todos los trabajadores. No se mezcla esta fuente con INE EAES.

## Importes y cambios acumulados

![Salario neto](figures/block01/20_net_salary_history.png)
![Vivienda](figures/block01/21_housing_value_history.png)
![Subidas totales](figures/block01/22_housing_net_salary_total_change.png)
![Euros constantes](figures/block01/17_housing_salary_real.png)

Las dos primeras figuras muestran por separado el salario neto anual y el valor
de la vivienda, en euros corrientes. La tercera compara sus subidas totales
durante el mismo periodo, sin descontar inflación.
La tabla siguiente conserva también el bruto y los cambios ajustados por IPC.

| Serie | Cambio nominal {first}–{last} | Cambio descontado IPC |
| --- | ---: | ---: |
{rows}

## Diferencia de variación anual

![Vivienda frente a bruto](figures/block01/18_housing_salary_gross_gap.png)
![Vivienda frente a neto](figures/block01/19_housing_salary_net_gap.png)

Una barra por año, mismo color y escala: **tasa de vivienda menos tasa salarial**,
en puntos porcentuales. Cada tasa es (valor actual / valor anterior − 1) × 100.
Las barras cubren {first + 1}–{last}; el primer año solo sirve para calcular la tasa.
Una barra positiva indica que vivienda sube más o cae menos; una negativa,
que el salario sube más o cae menos. No es el porcentaje de cambio del cociente.

## Cobertura y reproducción

Se conserva la respuesta original en `data/snapshots/block01/salary_eurostat.json`
y la política de comparación y huella SHA-256 en `salary_eurostat_source.json`.
2024 está marcado como ruptura y contiene importes anómalos; se excluye junto a
2025, sin extrapolar ni encadenar a través de la ruptura. El snapshot EAES y su
script de normalización se conservan como fuente alternativa, no usada aquí.

`python scripts/run_block01.py` reproduce las siete figuras, este informe y las
tablas `housing_salary_comparison.csv` y `housing_salary_variation_gap.csv`, sin red.
El notebook utiliza las mismas funciones de `src/spain_housing/salary_analysis.py`.
La comparación no mide por sí sola accesibilidad: faltan ingresos del hogar,
gastos, ahorro, financiación y diferencias territoriales; no identifica causas.
"""
    (root / "reports/block_01_housing_salary.md").write_text(report, encoding="utf-8")
    return files, panel, nominal, real, gaps
