"""Official annual demographic/supply panels; no network access at analysis time."""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator

from .construction_history import load_construction_history

LABELS = {
    "price": "Tasación de vivienda libre",
    "population": "Población total",
    "adults": "Población de 18 años o más",
    "dwellings": "Parque total de viviendas",
    "households": "Hogares",
}
COLORS = ["#c25138", "#24688d", "#79539b", "#258477", "#c29324"]
FIGURES = [
    "01_price_population_stock",
    "02_dwellings_per_resident",
    "03_construction",
    "04_population_growth_components",
    "05_population_birthplace",
    "06_regional_comparison",
]


def read_source(root, name):
    """Verify the committed source bytes before reading a frozen raw snapshot."""
    directory = Path(root) / "data/snapshots/block02"
    manifest = json.loads((directory / "source_manifest.json").read_text())
    item = next(r for r in manifest["sources"] if r["name"] == name)
    path = Path(root) / item["snapshot_path"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != item["snapshot_sha256"]:
        raise ValueError(f"Source checksum mismatch: {name}")
    return pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)


def numeric(series):
    """Spanish CSV: thousands dots, decimal comma; missing values stay missing."""
    return pd.to_numeric(
        series.str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def january(frame):
    frame = frame[frame["Periodo"].str.match(r"^1 de enero de \d{4}$")].copy()
    frame["reference_year"] = frame["Periodo"].str[-4:].astype(int)
    frame["value"] = numeric(frame["Total"])
    return frame


def population_series(frame, status):
    data = january(frame[frame["Sexo"] == "Total"])
    total = data[data["Edad simple"] == "Todas las edades"].set_index("reference_year")["value"]
    # Total minus exact single-year ages 0–17 avoids summing overlapping age groups.
    ages = data["Edad simple"].str.extract(r"^(\d+) años?$")[0].astype(float)
    children = data[ages.between(0, 17)]
    counts = children.groupby("reference_year").size()
    if not counts.eq(18).all():
        raise ValueError("Every reference date must contain all 18 child ages")
    adults = total - children.groupby("reference_year")["value"].sum(min_count=18)
    result = pd.DataFrame({"population": total, "adults": adults})
    result["population_status"] = status
    return result


def combine_releases(definitive, provisional):
    """Keep definitive observations; use provisional only for later dates."""
    return pd.concat([definitive, provisional.loc[provisional.index > definitive.index.max()]])


def annual_change(series):
    """Differences require adjacent calendar years, never bridge a missing year."""
    ordered = series.sort_index()
    return ordered.diff().where(ordered.index.to_series().diff() == 1)


def common_index(frame):
    clean = frame.dropna().sort_index()
    if clean.empty or (clean <= 0).any().any():
        raise ValueError("Positive observations and a common base year are required")
    return clean.div(clean.iloc[0]).mul(100)


def construction_series(data):
    data = data.copy()
    data["year"] = data["Año"].astype(int)
    data["month"] = data["Mes_Numero"].astype(int)
    data["value"] = numeric(data["Valor"])
    data["code"] = data["CODAUTO"].astype(int)
    national = data[data["code"] == 0]
    key = ["year", "Estado", "Tipo_de_Vivienda", "month"]
    if national.duplicated(key).any():
        raise ValueError("Duplicate national construction observations")
    sizes = national.groupby(["year", "Estado", "Tipo_de_Vivienda"]).size()
    if not sizes.eq(12).all() or national["value"].isna().any():
        raise ValueError("Construction requires 12 months for each state/type")
    totals = national.groupby(["year", "Estado"])["value"].sum().unstack()
    provincial = data[data["code"] != 0].groupby(["year", "Estado"])["value"].sum().unstack()
    if not np.allclose(totals, provincial):
        raise ValueError("National and provincial construction totals disagree")
    return totals.rename(columns={"Terminadas": "completions", "Iniciadas": "starts"})


def load_panels(root):
    root = Path(root)
    pop = combine_releases(
        population_series(read_source(root, "population"), "definitivo"),
        population_series(read_source(root, "population_provisional"), "provisional"),
    )
    # A stock at 1 January y+1 represents the end of calendar year y.
    pop.index = pop.index - 1
    pop.index.name = "year"
    price_path = root / "data/snapshots/block01/valuations.csv"
    manifest = json.loads((root / "data/snapshots/block02/source_manifest.json").read_text())
    if hashlib.sha256(price_path.read_bytes()).hexdigest() != manifest["price_snapshot_sha256"]:
        raise ValueError("Price snapshot checksum mismatch")
    price = pd.read_csv(price_path)
    price = price[price.year.between(2000, 2025)]
    national_price = price[price.level == "national"].set_index("year")["value"].rename("price")
    stock = read_source(root, "stock")
    stock["year"] = stock["Año"].astype(int)
    stock["code"] = stock["CODAUTO"].astype(int)
    stock["value"] = numeric(stock["Valor"])
    stock = stock[stock["Tipo_Vivienda"] == "Viviendas_Totales"]
    # Stock has 50 provinces plus the combined Ceuta/Melilla unit (code 0).
    if stock.duplicated(["year", "CPRO", "code"]).any():
        raise ValueError("Duplicate dwelling-stock observations")
    if not stock.groupby("year").size().eq(51).all() or stock.value.isna().any():
        raise ValueError("Stock coverage must contain 51 complete territorial units")
    national_stock = stock.groupby("year")["value"].sum().rename("dwellings")
    hh = january(read_source(root, "households"))
    hh = hh[hh["Tamaño del hogar"] == "Total"].set_index("reference_year")["value"]
    hh.index = hh.index - 1
    hh = hh.rename("households")
    panel = pd.concat(
        [
            national_price,
            pop,
            national_stock,
            hh,
            load_construction_history(root),
        ],
        axis=1,
    ).sort_index()
    panel = panel.loc[2000:2025]
    panel.index.name = "year"
    panel["population_change"] = annual_change(panel.population)
    panel["net_household_formation"] = annual_change(panel.households)
    panel["formation_minus_completions"] = panel.net_household_formation - panel.completions
    panel["dwellings_per_1000_residents"] = panel.dwellings / panel.population * 1000
    panel["dwellings_per_1000_adults"] = panel.dwellings / panel.adults * 1000
    panel["price_change_pct"] = panel.price.pct_change(fill_method=None) * 100
    panel["population_change_pct"] = panel.population.pct_change(fill_method=None) * 100

    def birthplace(name, status):
        d = read_source(root, name)
        d = january(d[(d.Sexo == "Total") & (d.Nacionalidad == "Total")])
        result = d.pivot(index="reference_year", columns="País de nacimiento", values="value")
        result = result.rename(
            columns={
                "España": "born_spain",
                "Extranjero": "born_abroad",
                "Total": "population",
            }
        )
        if not np.allclose(
            result.born_spain + result.born_abroad, result.population, rtol=0, atol=1
        ):
            raise ValueError("Birthplace components must sum to the total population")
        result["status"] = status
        return result

    birth = combine_releases(
        birthplace("birthplace", "definitivo"), birthplace("birthplace_provisional", "provisional")
    )
    birth.index = birth.index - 1
    birth.index.name = "year"
    birth["change_born_spain"] = annual_change(birth.born_spain)
    birth["change_born_abroad"] = annual_change(birth.born_abroad)
    birth = birth.loc[2000:2025]

    def rate(name):
        d = read_source(root, name)
        if "Sexo" in d:
            d = d[d.Sexo == "Total"]
        d = d[d["Totales Territoriales"] == "Total Nacional"].copy()
        d["year"] = d.Periodo.astype(int)
        return pd.Series(numeric(d.Total).to_numpy(), index=d.year).sort_index()

    migration = pd.concat([rate("migration_old"), rate("migration_new")])
    if migration.index.duplicated().any():
        raise ValueError("Migration releases must not overlap")
    components = pd.DataFrame(
        {
            "natural_per_1000": rate("natural"),
            "migration_per_1000": migration,
            "growth_per_1000": rate("growth"),
        }
    ).loc[2008:2024]
    components["residual_per_1000"] = (
        components.growth_per_1000 - components.natural_per_1000 - components.migration_per_1000
    )
    components.index.name = "year"

    regional_hh = january(read_source(root, "households_regions"))
    regional_hh = regional_hh[
        (regional_hh["Tamaño del hogar"] == "Total")
        & (regional_hh["Comunidades y ciudades autónomas"] != "Total Nacional")
    ]
    regional_hh["code"] = regional_hh["Comunidades y ciudades autónomas"].str[:2].astype(int)
    regional_hh["year"] = regional_hh.reference_year - 1
    regional_hh = regional_hh.pivot(index="year", columns="code", values="value")
    regional_stock = stock[stock.code != 0].groupby(["year", "code"]).value.sum().unstack()
    regional_price = price[price.level == "region"].pivot(
        index="year", columns="code", values="value"
    )
    regional = []
    # ECP households begin January 2021: end-2020 is the common baseline.
    for code in range(1, 18):
        item = {"code": code, "start_year": 2020, "end_year": 2025}
        for name, data in [
            ("households", regional_hh),
            ("dwellings", regional_stock),
            ("price", regional_price),
        ]:
            a, b = data.loc[2020, code], data.loc[2025, code]
            if pd.isna(a) or pd.isna(b) or a <= 0:
                raise ValueError(f"Missing regional endpoint: {name}/{code}")
            item[f"{name}_change_pct"] = (b / a - 1) * 100
        item["name"] = price[(price.level == "region") & (price.code == code)].name.iloc[0]
        regional.append(item)
    return panel, birth, components, pd.DataFrame(regional)


def figure_style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.16,
            "figure.facecolor": "#faf9f6",
            "axes.facecolor": "#faf9f6",
            "savefig.facecolor": "#faf9f6",
        }
    )


def finish(fig, title, note):
    for ax in fig.axes:
        if not title.startswith("La presión"):
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    fig.suptitle(title, fontsize=17, fontweight="bold", x=0.07, ha="left")
    fig.text(0.07, 0.025, note, fontsize=9, color="#555555", va="bottom")
    fig.tight_layout(rect=(0, 0.09, 1, 0.92))
    return fig


def make_figure(number, panel, birth, components, regional):
    figure_style()
    if number == 1:
        fig, ax = plt.subplots(figsize=(12, 6.5))
        counts = panel[["population", "dwellings"]].dropna()
        for column, color, label in [
            ("population", COLORS[1], "Población total (habitantes)"),
            ("dwellings", COLORS[3], "Viviendas totales"),
        ]:
            ax.plot(
                counts.index,
                counts[column],
                color=color,
                lw=2.6,
                marker="o",
                markersize=3.5,
                label=label,
            )
            for year in [counts.index[0], counts.index[-1]]:
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
            xlabel="Año",
            ylabel="Número de habitantes / viviendas",
            ylim=(0, counts.max().max() * 1.12),
        )
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda value, _: f"{value:,.0f}".replace(",", "."))
        )
        ax.legend(frameon=False, loc="lower right")
        return finish(
            fig,
            "Población y viviendas totales en España",
            "Fuentes: INE (población) y MIVAU (parque de viviendas). Datos al "
            "cierre de cada año; población de 2025 provisional.\n"
            "Viviendas totales: ocupadas, secundarias y vacías; no equiva"
            "le a viviendas en venta o alquiler.",
        )
    if number == 2:
        fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
        for ax, c, label, color in zip(
            axes,
            ["dwellings_per_1000_residents", "dwellings_per_1000_adults"],
            ["Por mil habitantes", "Por mil adultos"],
            COLORS[1:3],
        ):
            ax.plot(panel.index, panel[c], color=color, lw=2.5)
            ax.set(ylabel="Viviendas", title=label, ylim=(0, None))
        axes[1].set_xlabel("Año")
        return finish(
            fig,
            "Parque de viviendas en relación con la población",
            'España · MIVAU e INE · 2001–2025. Incluye viviendas ocupadas, '
            'secundarias y vacÃ\xadas.\n'
            'No mide viviendas disponibles en el mercado. Población de cierre de '
            '2025 provisional.',
        )
    if number == 3:
        fig, ax = plt.subplots(figsize=(15, 6.5))
        supply = panel.dropna(subset=["completions", "starts"])
        ax.bar(supply.index, supply.completions, color=COLORS[3], label="Viviendas terminadas")
        ax.plot(
            supply.index,
            supply.starts,
            color=COLORS[1],
            marker="o",
            markersize=4,
            lw=2,
            label="Viviendas iniciadas",
        )
        ax.set(ylabel="Número de viviendas", xlabel="Año", ylim=(0, None))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
        ax.set_xticks(range(2000, 2026, 2))
        ax.legend(frameon=False)
        return finish(
            fig,
            "Construcción de viviendas en España",
            "Fomento / MIVAU · 2000–2025 · Libres + protegidas. Iniciadas"
            " no equivale a terminadas.\n"
            "Boletín 2013 y serie actual: coincidencia exacta en 2008–2012. En"
            " 2000 se conserva el total publicado, con discrepancia de 1.000 e"
            "n subtotales.",
        )
    if number == 4:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(
            components.index - 0.2,
            components.natural_per_1000,
            0.4,
            color=COLORS[0],
            label="Saldo natural: nacimientos âˆ’ defunciones",
        )
        ax.bar(
            components.index + 0.2,
            components.migration_per_1000,
            0.4,
            color=COLORS[1],
            label="Saldo migratorio: entradas âˆ’ salidas",
        )
        ax.plot(
            components.index,
            components.growth_per_1000,
            color="#242424",
            lw=2,
            marker="o",
            label="Crecimiento total publicado",
        )
        ax.plot(
            components.index,
            components.residual_per_1000,
            color="#888888",
            ls=":",
            label="Residuo estadístico / revisiones",
        )
        ax.axhline(0, color="#444444", lw=0.8)
        ax.axvline(2020.5, color="#777777", ls="--", lw=1)
        ax.set(xlabel="Año", ylabel="Personas por 1.000 habitantes")
        ax.legend(frameon=False, fontsize=9, ncol=2)
        return finish(
            fig,
            "¿De dónde procede el crecimiento demográfico?",
            "España · INE IDB · 2008–2024. Cambio de estadística migratoria en 2021 "
            "(línea discontinua).\n"
            "Saldo natural incluye a todos los residentes. Las diferencias entre "
            "componentes y crecimiento se muestran, no se imputan.",
        )
    if number == 5:
        fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        for c, label, color in [
            ("born_spain", "Nacidos en España", COLORS[3]),
            ("born_abroad", "Nacidos en el extranjero", COLORS[1]),
        ]:
            axes[0].plot(birth.index, birth[c] / 1e6, label=label, color=color, lw=2.5)
        axes[0].set(
            ylabel="Millones de residentes",
            ylim=(0, None),
            title="Población residente por lugar de nacimiento",
        )
        axes[0].legend(frameon=False)
        axes[1].bar(
            birth.index - 0.2,
            birth.change_born_spain / 1000,
            0.4,
            color=COLORS[3],
            label="Cambio: nacidos en España",
        )
        axes[1].bar(
            birth.index + 0.2,
            birth.change_born_abroad / 1000,
            0.4,
            color=COLORS[1],
            label="Cambio: nacidos en el extranjero",
        )
        axes[1].axhline(0, color="#444444", lw=0.8)
        axes[1].set(ylabel="Cambio anual · miles de personas", xlabel="Año")
        axes[1].legend(frameon=False, fontsize=9)
        return finish(
            fig,
            "¿Qué grupos explican el cambio de población residente?",
            'España · INE ECP. Cierre de año: 1 de enero siguiente; cierre de '
            '2025 provisional.\n'
            "Lugar de nacimiento ≠ nacionalidad. Los cambios de estos grupos no "
            "equivalen al saldo migratorio.",
        )
    if number == 6:
        ordered = regional.sort_values("households_change_pct")
        fig, axes = plt.subplots(1, 3, figsize=(14, 8), sharey=True, sharex=True)
        for ax, c, color, label in zip(
            axes,
            ["households_change_pct", "dwellings_change_pct", "price_change_pct"],
            [COLORS[4], COLORS[3], COLORS[0]],
            ["Hogares", "Parque de viviendas", "Precio nominal"],
        ):
            ax.barh(ordered.name, ordered[c], color=color)
            ax.axvline(0, color="#444444", lw=0.8)
            ax.set(title=label, xlabel="Cambio acumulado (%)")
        return finish(
            fig,
            "La presión no se distribuye igual en todas las comunidades",
            "INE ECP y MIVAU · Cambio 2020–2025 · 17 comunidades, mismos extremos y "
            "misma escala porcentual.\n"
            "Stocks al cierre del año; precio medio anual. Ceuta/Melilla excluidas: "
            "parque publicado como unidad conjunta.",
        )
    raise ValueError("Figure number must be 1–6")


def findings(panel, birth, components):
    first, last = panel.loc[2001], panel.loc[2025]
    changes = {
        c: float((last[c] / first[c] - 1) * 100)
        for c in ["price", "population", "adults", "dwellings"]
    }
    recent = panel.loc[2021:2025]
    b = birth.dropna(subset=["change_born_spain", "change_born_abroad"]).iloc[-1]
    return {
        "period": [2001, 2025],
        "changes_pct": changes,
        "recent_period": [2021, 2025],
        "recent_completions": float(recent.completions.sum()),
        "recent_net_household_formation": float(recent.net_household_formation.sum()),
        "recent_formation_minus_completions": float(recent.formation_minus_completions.sum()),
        "latest_birthplace_year": int(b.name),
        "latest_change_born_spain": float(b.change_born_spain),
        "latest_change_born_abroad": float(b.change_born_abroad),
        "latest_components_year": int(components.index.max()),
        "latest_components_per_1000": components.iloc[-1].to_dict(),
    }


def run_analysis(root):
    root = Path(root)
    panels = load_panels(root)
    table_dir = root / "reports/tables/block02"
    figure_dir = root / "reports/figures/block02"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    for name, data in zip(
        ["annual_panel", "birthplace", "growth_components", "regional_comparison"], panels
    ):
        data.to_csv(
            table_dir / f"{name}.csv", index=name != "regional_comparison", float_format="%.8f"
        )
    for number, name in enumerate(FIGURES, 1):
        fig = make_figure(number, *panels)
        fig.savefig(figure_dir / f"{name}.png", dpi=150)
        plt.close(fig)
    from .demographic_publication import publish_demographics

    additional = publish_demographics(root, panels)
    from .demographic_publication import publish_demographics

    additional = publish_demographics(root, panels)
    result = findings(*panels[:3])
    result["figure_count"] = len(FIGURES) + len(additional)
    result["figure_count"] = len(FIGURES) + len(additional)
    (table_dir / "findings.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return panels, result


def population_dwelling_use_figure(panel, root):
    """Compare population with the official stock classified by dwelling use."""
    figure_style()
    stock = read_source(root, "stock")
    stock["year"] = stock["A\u00f1o"].astype(int)
    stock["value"] = numeric(stock["Valor"])
    categories = {
        "Viviendas_Totales": "dwellings",
        "Vivienda_Principal": "principal_dwellings",
        "Vivienda_No_Principal": "non_principal_dwellings",
    }
    selected = stock[stock.Tipo_Vivienda.isin(categories)]
    if selected.value.isna().any():
        raise ValueError("Missing dwelling-use observations")
    if not selected.groupby(["year", "Tipo_Vivienda"]).size().eq(51).all():
        raise ValueError("Incomplete territorial coverage for dwelling use")
    counts = selected.groupby(["year", "Tipo_Vivienda"]).value.sum().unstack()
    counts = counts.rename(columns=categories)
    if not np.allclose(
        counts.dwellings,
        counts.principal_dwellings + counts.non_principal_dwellings,
        rtol=0,
        atol=2,
    ):
        raise ValueError("Dwelling-use components do not match the total")
    counts = counts.join(panel.population, how="inner").dropna()
    if not np.array_equal(counts.dwellings, panel.loc[counts.index, "dwellings"]):
        raise ValueError("Dwelling totals disagree with the first figure")
    directory = Path(root) / "reports/tables/block02"
    directory.mkdir(parents=True, exist_ok=True)
    counts.to_csv(directory / "population_dwelling_use.csv")
    fig, ax = plt.subplots(figsize=(14, 7))
    series = [
        ("population", COLORS[1], "Poblaci\u00f3n total (habitantes)"),
        ("dwellings", COLORS[3], "Viviendas totales"),
        ("principal_dwellings", COLORS[0], "Viviendas principales"),
        ("non_principal_dwellings", COLORS[2], "Viviendas no principales"),
    ]
    for column, color, label in series:
        ax.plot(
            counts.index, counts[column], color=color, lw=2.5, marker="o", markersize=3, label=label
        )
        for year in (counts.index.min(), counts.index.max()):
            value = counts.loc[year, column]
            ax.annotate(
                f"{value:,.0f}".replace(",", "."),
                (year, value),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                color=color,
                fontsize=9,
            )
    ax.set(
        xlabel="A\u00f1o",
        ylabel="N\u00famero de habitantes / viviendas",
        ylim=(0, counts.max().max() * 1.12),
    )
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}".replace(",", ".")))
    ax.legend(frameon=False, loc="upper left")
    return finish(
        fig,
        "Poblaci\u00f3n y viviendas por uso en Espa\u00f1a",
        "INE y MIVAU \u00b7 2001\u20132025 "
        "\u00b7 Cierre de a\u00f1o; poblaci\u00f3n de 2025 provisional.\n"
        "Principales: residencia habitual. No principales: otros usos y viviendas vac\u00edas.\n"
        "Esta clasificaci\u00f3n no mide habitabilidad ni disponibilidad para compra o alquiler.",
    )
