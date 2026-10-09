"""Annual immigration of foreign nationals by previous country of residence."""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from .demographics import numeric

# Explicit individual countries: exclude continental totals and residual groups.
COUNTRIES = (
    "Bélgica",
    "Bulgaria",
    "Dinamarca",
    "Finlandia",
    "Francia",
    "Irlanda",
    "Italia",
    "Países Bajos",
    "Polonia",
    "Portugal",
    "Alemania",
    "Rumanía",
    "Suecia",
    "Lituania",
    "Noruega",
    "Reino Unido",
    "Suiza",
    "Ucrania",
    "Moldavia",
    "Rusia",
    "Argelia",
    "Gambia",
    "Ghana",
    "Guinea",
    "Guinea Ecuatorial",
    "Mali",
    "Marruecos",
    "Mauritania",
    "Nigeria",
    "Senegal",
    "Estados Unidos de América",
    "México",
    "Canadá",
    "Cuba",
    "Honduras",
    "Nicaragua",
    "República Dominicana",
    "Argentina",
    "Bolivia",
    "Brasil",
    "Colombia",
    "Chile",
    "Ecuador",
    "Paraguay",
    "Perú",
    "Uruguay",
    "Venezuela",
    "Bangladesh",
    "China",
    "Filipinas",
    "India",
    "Pakistán",
)


def load_immigration_provenance(root):
    directory = Path(root) / "data/snapshots/block02"
    frames = []
    for table in (24295, 69690):
        path = directory / f"immigration_provenance_{table}.csv"
        metadata = json.loads(path.with_suffix(".json").read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest() != metadata["sha256"]:
            raise ValueError(f"Immigration source checksum mismatch: {table}")
        raw = pd.read_csv(path, sep=";", dtype=str)
        if table == 69690:
            raw = raw[raw.Sexo == "Ambos sexos"]
            country_column = "País de procedencia"
        else:
            country_column = "País de origen"
        raw = raw.copy()
        raw["arrivals"] = numeric(raw.Total)
        raw["year"] = raw.Periodo.astype(int)
        raw["country"] = raw[country_column]
        totals = raw.pivot(index=["year", "country"], columns="Nacionalidad", values="arrivals")
        complete = totals.dropna()
        if not np.allclose(
            complete.Total, complete["Española"] + complete.Extranjero, rtol=0, atol=2
        ):
            raise ValueError("Nationality components disagree with totals")
        foreign = raw[(raw.Nacionalidad == "Extranjero") & raw.country.isin(COUNTRIES)]
        if table == 24295:
            foreign = foreign[foreign.year <= 2020]
        if foreign.arrivals.isna().any() or (foreign.arrivals < 0).any():
            raise ValueError("Missing or negative country arrivals")
        frames.append(foreign[["year", "country", "arrivals"]])
    data = pd.concat(frames, ignore_index=True).sort_values(["year", "country"])
    if data.duplicated(["year", "country"]).any():
        raise ValueError("Duplicate country/year observations")
    if sorted(data.year.unique()) != list(range(2008, 2025)):
        raise ValueError("Expected all years from 2008 to 2024")
    if not data.groupby("year").size().eq(len(COUNTRIES)).all():
        raise ValueError("Incomplete country coverage")
    folder = Path(root) / "reports/tables/block02"
    folder.mkdir(parents=True, exist_ok=True)
    data.to_csv(folder / "immigration_provenance.csv", index=False)
    rankings = pd.concat([top_countries(data, year) for year in sorted(data.year.unique())])
    rankings.to_csv(folder / "immigration_provenance_top15.csv", index=False)
    return data


def top_countries(data, year):
    ranked = (
        data[data.year == year]
        .sort_values(["arrivals", "country"], ascending=[False, True])
        .head(15)
        .copy()
    )
    if len(ranked) != 15:
        raise ValueError("Each year must have fifteen ranked countries")
    ranked["rank"] = range(1, 16)
    return ranked


def global_top15_provenance_figure(data, root):
    """One fixed ranking by accumulated arrivals, plotted across all years."""
    ranking = data.groupby("country").arrivals.sum().sort_values(ascending=False).head(15)
    years = sorted(data.year.unique())
    wide = data.pivot(index="year", columns="country", values="arrivals").loc[years, ranking.index]
    if wide.isna().any().any():
        raise ValueError("Missing annual values for the global ranking")
    folder = Path(root) / "reports/tables/block02"
    wide.to_csv(folder / "immigration_provenance_global_top15_years.csv")
    ranking.rename("accumulated_arrivals").to_csv(
        folder / "immigration_provenance_global_top15.csv"
    )
    fig, ax = plt.subplots(figsize=(18, 9))
    colors = plt.get_cmap("tab20").colors
    for i, country in enumerate(ranking.index):
        ax.plot(
            wide.index,
            wide[country],
            color="#b66b70" if country == "Colombia" else colors[i],
            lw=2.2,
            marker="o",
            markersize=4,
            label=country,
        )
    ax.axvline(2020.5, color="#777777", ls=":", lw=1.3)
    ax.text(
        2020.6,
        wide.max().max() * 1.08,
        "Cambio de estad\u00edstica",
        color="#666666",
        fontsize=9,
        va="top",
    )
    ax.set(
        xlabel="A\u00f1o",
        ylabel="Llegadas anuales de personas de nacionalidad extranjera",
        ylim=(0, wide.max().max() * 1.12),
    )
    ax.set_xticks(years)
    ax.tick_params(axis="x", labelrotation=45)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ax.grid(axis="y", alpha=0.2)
    ax.legend(
        title="Pa\u00edses por llegadas acumuladas",
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        frameon=False,
        fontsize=10,
    )
    fig.suptitle(
        "Evoluci\u00f3n de las llegadas de extranjeros por pa\u00eds de procedencia",
        fontsize=17,
        fontweight="bold",
        x=0.07,
        ha="left",
    )
    fig.text(
        0.07,
        0.025,
        "INE \u00b7 2008\u20132024 \u00b7 Top quince fijo: pa\u00edses con m\u00e1s "
        "llegadas acumuladas "
        "en todo el periodo, entre los publicados individualmente.\n"
        "Cada punto muestra las llegadas de ese a\u00f1o, no el acumulado ni residentes totales. "
        "Procedencia = pa\u00eds de residencia anterior.\n"
        "Estad\u00edstica de Migraciones hasta 2020; EMCR desde 2021. El cambio de "
        "estad\u00edstica limita la comparabilidad. Sin predicciones.",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.13, 1, 0.94))
    return fig
