"""Historical comparison from frozen BIS and AMECO observations."""

import hashlib
import io
import json
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from spain_housing.prices_analysis import load_purchase_data, series_for


def load_long_history(root: Path) -> pd.DataFrame:
    snapshot = root / "data/snapshots/block01"
    for name in ("long_housing_bis.csv", "long_compensation_ameco.zip"):
        path = snapshot / name
        metadata = json.loads(path.with_suffix(".json").read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
            raise ValueError(f"Modified historical source: {name}")
    quarters = pd.read_csv(snapshot / "long_housing_bis.csv")
    if not (quarters.REF_AREA.eq("ES") & quarters.VALUE.eq("N")).all():
        raise ValueError("Expected nominal Spanish BIS series")
    if quarters.TIME_PERIOD.duplicated().any():
        raise ValueError("Duplicate quarters")
    quarters["year"] = quarters.TIME_PERIOD.str[:4].astype(int)
    grouped = quarters.groupby("year").OBS_VALUE
    housing = grouped.mean().loc[grouped.count().eq(4)]
    with zipfile.ZipFile(snapshot / "long_compensation_ameco.zip") as archive:
        ameco = pd.read_csv(io.BytesIO(archive.read("AMECO7.TXT")), sep=";", encoding="latin-1")
    row = ameco.loc[ameco.CODE.eq("ESP.1.0.0.0.HWCDW")]
    if len(row) != 1 or row.iloc[0].UNIT != "1000 EURO-ESP":
        raise ValueError("Expected compensation in fixed-conversion euros")
    compensation = row.iloc[0][[c for c in ameco if c.isdigit()]].astype(float) * 1000
    compensation.index = compensation.index.astype(int)
    panel = pd.concat(
        [housing.rename("housing_bis_index"), compensation.rename("compensation_eur")], axis=1
    ).loc[1971:2025]
    if panel.isna().any().any() or (panel <= 0).any().any():
        raise ValueError("Missing or invalid historical observations")
    if list(panel.index) != list(range(1971, 2026)):
        raise ValueError("Incomplete annual coverage")
    return panel


def run_long_history(root: Path):
    panel = load_long_history(root)
    figures = root / "reports/figures/block01"
    tables = root / "reports/tables/block01"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    values, _, _, _ = load_purchase_data(root)
    purchase = series_for(values, level="national")
    anchor = float(purchase.loc[2025]) * 80
    panel["housing_80m2_estimated_eur"] = (
        panel.housing_bis_index / panel.loc[2025, "housing_bis_index"] * anchor
    )
    panel.to_csv(tables / "long_housing_compensation.csv", index_label="year")
    changes = (panel.iloc[-1] / panel.iloc[0] - 1) * 100
    changes = changes.loc[["housing_bis_index", "compensation_eur"]]
    changes.to_csv(tables / "long_housing_compensation_total_change.csv", header=["change_pct"])
    files = []
    footer = (
        "Vivienda estimada de 80 m\u00b2: tasaci\u00f3n MIVAU 2025 "
        "\u00d7 evoluci\u00f3n BIS; no precios observados por a\u00f1o.\n"
        "BIS: media de cuatro trimestres; 1975\u20131986 usa precios del \u00e1rea de Madrid. "
        "Fuentes y m\u00e9todos cambian en 1975, 1987 y 2007.\n"
        "AMECO: remuneraci\u00f3n por asalariado, incluidas cotizaciones empresariales. "
        "Euros a conversi\u00f3n fija de pesetas; no salario neto.\n"
        "Importes nominales, sin descontar inflaci\u00f3n. 2025 sujeto a revisiones. "
        "Sin extrapolar 1966\u20131970 ni usar previsiones de 2026\u20132027."
    )
    with plt.rc_context({"font.size": 11, "axes.facecolor": "#fafafa"}):
        for column, title, color, name in [
            (
                "compensation_eur",
                "Remuneraci\u00f3n anual por asalariado",
                "#9b626b",
                "23_long_compensation_history",
            ),
            (
                "housing_bis_index",
                "Valor estimado de una vivienda de 80 m\u00b2",
                "#207b8e",
                "24_long_housing_history",
            ),
        ]:
            fig, ax = plt.subplots(figsize=(13, 6.5))
            series = (
                panel[column]
                if column == "compensation_eur"
                else panel["housing_80m2_estimated_eur"]
            )
            ax.plot(series.index, series, color=color, lw=2.5)
            if column == "housing_bis_index":
                ax.axvspan(
                    1975,
                    1986,
                    color="#aaaaaa",
                    alpha=0.18,
                    label="1975\u20131986: precios del \u00e1rea de Madrid",
                )
                for year in (1975, 1987, 2007):
                    ax.axvline(year, color="#888888", ls=":", lw=1)
                ax.legend(loc="upper left", frameon=False)
            for year in (1971, 2025):
                value = series.loc[year]
                label = f"{year}: {value:,.0f}".replace(",", ".")
                label += " \u20ac"
                ax.annotate(
                    label,
                    (year, value),
                    xytext=(0, 12),
                    textcoords="offset points",
                    ha="center",
                    color=color,
                )
            ax.set(
                xlabel="A\u00f1o",
                ylim=(0, series.max() * 1.22),
                ylabel="Euros corrientes por asalariado"
                if column == "compensation_eur"
                else "Vivienda de 80 m\u00b2 estimada (euros corrientes)",
            )
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
            ax.grid(axis="y", alpha=0.2)
            ax.spines[["top", "right"]].set_visible(False)
            fig.suptitle(title, fontsize=17, fontweight="bold")
            fig.text(
                0.09,
                0.86,
                "Serie para Espa\u00f1a \u00b7 1971\u20132025 \u00b7 Subida total: "
                + f"+{changes[column]:,.1f} %".replace(",", "_")
                .replace(".", ",")
                .replace("_", "."),
                color=color,
                fontsize=12,
            )
            fig.text(0.09, 0.025, footer, fontsize=8.5, color="#555555")
            fig.tight_layout(rect=(0, 0.20, 1, 0.84))
            path = figures / f"{name}.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            files.append(path)
        fig, ax = plt.subplots(figsize=(12, 6.5))
        bars = ax.barh(
            [
                "Vivienda de 80 m\u00b2\n(valor estimado con BIS)",
                "Remuneraci\u00f3n por asalariado\n(incluye cotizaciones empresariales)",
            ],
            changes,
            color=["#207b8e", "#9b626b"],
            height=0.45,
        )
        ax.invert_yaxis()
        ax.bar_label(
            bars,
            labels=[
                f"+{v:,.1f} %".replace(",", "_").replace(".", ",").replace("_", ".")
                for v in changes
            ],
            padding=8,
            fontsize=14,
        )
        ax.set(xlabel="Subida acumulada nominal (%)", xlim=(0, changes.max() * 1.3))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f} %".replace(",", ".")))
        ax.grid(axis="x", alpha=0.18)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        fig.suptitle(
            "Cu\u00e1nto han subido la vivienda y la remuneraci\u00f3n",
            fontsize=17,
            fontweight="bold",
        )
        fig.text(
            0.07,
            0.85,
            "Mismo periodo: 1971\u20132025 \u00b7 54 a\u00f1os entre extremos",
            fontsize=12,
        )
        fig.text(0.07, 0.025, footer, fontsize=8.5, color="#555555")
        fig.tight_layout(rect=(0, 0.20, 1, 0.82))
        path = figures / "25_long_housing_compensation_change.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        files.append(path)
    return files, panel, changes
