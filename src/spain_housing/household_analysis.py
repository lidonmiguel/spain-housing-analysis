"""Household growth accounting; descriptive, not a causal price model."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from .demographics import january, read_source


def decompose_households(population, households):
    data = pd.DataFrame({"population": population, "households": households}).dropna().sort_index()
    if (data <= 0).any().any():
        raise ValueError("Positive population and household counts required")
    q = data.households / data.population
    adjacent = data.index.to_series().diff().eq(1)
    data["residents_per_household_ratio"] = 1 / q
    data["population_component"] = (data.population.diff() * (q + q.shift()) / 2).where(adjacent)
    data["household_intensity_component"] = (
        q.diff() * (data.population + data.population.shift()) / 2
    ).where(adjacent)
    data["household_change"] = data.households.diff().where(adjacent)
    valid = data.dropna(subset=["household_change"])
    np.testing.assert_allclose(
        valid.population_component + valid.household_intensity_component,
        valid.household_change,
        atol=1e-6,
        rtol=0,
    )
    return data


def single_person_history(root):
    """Keep observed historic points and source breaks; do not interpolate."""
    import hashlib

    folder = Path(root) / "data/snapshots/block02"
    meta = json.loads(
        (folder / "single_person_households_history_source.json").read_text(encoding="utf-8")
    )
    path = folder / "single_person_households_history.csv"
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta["extracted_csv_sha256"]:
        raise ValueError("Historic household snapshot checksum mismatch")
    historical = pd.read_csv(path).set_index("year")
    epa_path = folder / "households_epa_65269.csv"
    epa_meta = json.loads((folder / "households_epa_source.json").read_text(encoding="utf-8"))
    if hashlib.sha256(epa_path.read_bytes()).hexdigest() != epa_meta["sha256"]:
        raise ValueError("EPA household snapshot checksum mismatch")
    raw = pd.read_csv(epa_path, sep=";", encoding="utf-8-sig", dtype=str)
    raw = raw[
        (raw["Número de activos en el hogar"] == "Total") & raw.Periodo.str.endswith("T4")
    ].copy()
    raw["year"] = raw.Periodo.str[:4].astype(int)
    from .demographics import numeric

    raw["value"] = numeric(raw.Total) * 1000
    wide = raw.pivot(index="year", columns="Número de personas en el hogar", values="value").loc[
        2002:2025
    ]
    recent = pd.DataFrame(
        {
            "total_households": wide["Total"],
            "single_person_households": wide["Una persona"],
            "source": "EPA",
        }
    )
    recent["reference"] = [f"{year}T4" for year in recent.index]
    data = pd.concat([historical.loc[[2001]], recent]).sort_index()
    if list(data.index) != list(range(2001, 2026)):
        raise ValueError("Incomplete yearly household history")
    if (
        data.index.duplicated().any()
        or data[["total_households", "single_person_households"]].isna().any().any()
    ):
        raise ValueError("Duplicate or missing household observations")
    data["single_person_share_pct"] = data.single_person_households / data.total_households * 100
    data.to_csv(
        Path(root) / "reports/tables/block02/single_person_households_history.csv",
        float_format="%.6f",
    )
    return data


def single_person_history_figures(data):
    figures = []
    for column, title, ylabel, percent in [
        (
            "single_person_households",
            "Hogares de una persona en España",
            "Número de hogares",
            False,
        ),
        (
            "single_person_share_pct",
            "Porcentaje de hogares de una persona en España",
            "Porcentaje de todos los hogares",
            True,
        ),
    ]:
        fig, ax = plt.subplots(figsize=(18, 7))
        for source, marker, color in [
            ("Censo", "D", "#555555"),
            ("EPA", "o", "#24688d"),
        ]:
            part = data[data.source == source]
            # Reindex annual segments to preserve any missing years as visible gaps.
            series = part[column].reindex(range(int(part.index.min()), int(part.index.max()) + 1))
            ax.plot(
                series.index,
                series,
                marker=marker,
                color=color,
                lw=2.5,
                ls="none" if source == "Censo" else "-",
                label=source,
            )
            for i, (year, value) in enumerate(part[column].items()):
                label = (
                    f"{value:.2f}%".replace(".", ",")
                    if percent
                    else f"{value:,.0f}".replace(",", ".")
                )
                ax.annotate(
                    label,
                    (year, value),
                    xytext=(0, 12 if i % 2 == 0 else -20),
                    textcoords="offset points",
                    ha="center",
                    fontsize=8,
                    rotation=0,
                    color=color,
                )
        ax.set(
            title=title,
            xlabel="Año",
            ylabel=ylabel,
            xlim=(2000, 2026),
            ylim=(0, data[column].max() * 1.2),
        )
        ax.set_xticks(range(2001, 2026))
        ax.tick_params(axis="x", labelrotation=45, labelsize=9)
        if not percent:
            ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
        ax.grid(axis="y", alpha=0.18)
        ax.legend(frameon=False, loc="lower right", title="Fuente INE")
        fig.text(
            0.07,
            0.025,
            "INE · Censo: noviembre de 2001. EPA: cuarto trimestre de cada año"
            ", 2002–2025. Todas las edades, viviendas familiares.\n"
            "Unipersonales = una persona. Porcentaje sobre hogares totales de "
            "la misma fuente y fecha, no sobre todo el parque de viviendas.\n"
            "Cambios metodológicos y de base poblacional de la EPA; el censo s"
            "e muestra separado. No se interpolan datos.",
            fontsize=9,
            color="#555555",
        )
        fig.tight_layout(rect=(0, 0.15, 1, 1))
        figures.append(fig)
    return figures


def dwelling_household_totals_figure(panel, root):
    """INE demographic counts with explicitly marked internal interpolation."""
    import hashlib

    directory = Path(root) / "data/snapshots/block02"
    metadata = json.loads((directory / "single_person_households_history_source.json").read_text())
    historical_path = directory / "single_person_households_history.csv"
    if hashlib.sha256(historical_path.read_bytes()).hexdigest() != metadata["extracted_csv_sha256"]:
        raise ValueError("Historical household checksum mismatch")
    historical = pd.read_csv(historical_path).set_index("year")
    raw = january(read_source(root, "households"))
    raw = raw[raw["Tama\u00f1o del hogar"] == "Total"].copy()
    raw["year"] = raw.reference_year - 1
    recent = raw.set_index("year").value.sort_index().loc[2020:2025]
    observed = pd.concat([historical.total_households, recent]).sort_index()
    if observed.index.duplicated().any():
        raise ValueError("Overlapping household observations")
    counts = panel.loc[2001:2025, ["dwellings"]].copy()
    counts["households"] = observed.reindex(counts.index)
    counts["estimated"] = counts.households.isna()
    counts["households"] = counts.households.interpolate(method="index", limit_area="inside")
    if counts.households.isna().any() or (counts.households <= 0).any():
        raise ValueError("Missing or invalid interpolated households")
    counts["source"] = historical.source.reindex(counts.index)
    counts.loc[recent.index, "source"] = "ECP"
    counts.loc[counts.estimated, "source"] = "Linear interpolation (not INE data)"
    counts.to_csv(Path(root) / "reports/tables/block02/dwellings_households_totals.csv")
    fig, ax = plt.subplots(figsize=(15, 7))
    ax.plot(
        counts.index,
        counts.dwellings,
        color="#258477",
        lw=2.6,
        marker="o",
        markersize=4,
        label="Viviendas totales (MIVAU)",
    )
    for left, right in zip(counts.index[:-1], counts.index[1:]):
        estimated_segment = counts.loc[[left, right], "estimated"].any()
        ax.plot(
            [left, right],
            counts.loc[[left, right], "households"],
            color="#c25138",
            lw=2.6,
            ls="--" if estimated_segment else "-",
        )
    official = counts[~counts.estimated]
    estimated = counts[counts.estimated]
    ax.scatter(
        official.index,
        official.households,
        color="#c25138",
        s=26,
        label="Hogares: datos oficiales INE",
        zorder=3,
    )
    ax.scatter(
        estimated.index,
        estimated.households,
        edgecolors="#c25138",
        facecolors="white",
        s=28,
        label="Hogares: estimaci\u00f3n interpolada",
        zorder=3,
    )
    for column, color in (("dwellings", "#258477"), ("households", "#c25138")):
        for year in (counts.index.min(), counts.index.max()):
            value = counts.loc[year, column]
            ax.annotate(
                f"{value:,.0f}".replace(",", "."),
                (year, value),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                color=color,
                fontsize=10,
            )
    ax.set(
        title="Viviendas y hogares en Espa\u00f1a",
        xlabel="A\u00f1o",
        ylabel="N\u00famero de viviendas / hogares",
        ylim=(0, counts.dwellings.max() * 1.15),
    )
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ax.set_xticks(range(2001, 2026, 2))
    ax.tick_params(axis="x", labelrotation=45)
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, loc="lower right")
    fig.text(
        0.07,
        0.025,
        "Hogares INE: Censos 2001/2011; ECH 2013\u20132019; ECP 2020\u20132025.\n"
        "2002\u20132010 y 2012: interpolaci\u00f3n lineal propia (trazos discontinuos). "
        "No son datos publicados por el INE.\n"
        "Censos: noviembre; ECH/ECP: enero siguiente. Cambios de m\u00e9todo "
        "limitan la comparabilidad; ECP reciente provisional.\n"
        "MIVAU: parque total al cierre de a\u00f1o. La diferencia no mide "
        "viviendas disponibles.",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    return fig
