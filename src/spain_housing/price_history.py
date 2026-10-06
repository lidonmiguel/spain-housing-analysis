"""Long housing histories, retaining source definitions and observed coverage."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import mapping, shape

from spain_housing.prices_analysis import (
    BUY,
    RENT,
    annual_changes,
    change,
    gov_bands,
    load_rental_snapshot,
    map_panel,
    series_for,
    style,
)


def real_series(series, cpi, reference_year):
    """Constant-reference-year prices, only at years with observed CPI."""
    if reference_year not in cpi.index:
        raise ValueError("Reference CPI year is not observed")
    return series * cpi.loc[reference_year] / cpi.reindex(series.index)


def history_summary(frame, cpi, keys):
    """Coverage, actual endpoint changes and explicitly bounded purchase-cycle extrema."""
    rows = []
    for group, data in frame.groupby(keys, dropna=False):
        if not isinstance(group, tuple):
            group = (group,)
        s = data.set_index("year").value.sort_index()
        if s.index.has_duplicates:
            raise ValueError("History must contain a single observation per year")
        first, last = int(s.index.min()), int(s.index.max())
        real = real_series(s, cpi, int(cpi.index.max())).dropna()
        pre = s.loc[(s.index >= 1995) & (s.index <= 2008)]
        post = s.loc[(s.index >= 2009) & (s.index <= 2015)]
        peak = int(pre.idxmax()) if len(pre) else None
        trough = int(post.idxmin()) if len(post) else None
        row = dict(zip(keys, group, strict=True))
        row.update(
            first_year=first,
            last_year=last,
            observed_years=len(s),
            missing_years=(last - first + 1) - len(s),
            first_value=s.loc[first],
            last_value=s.loc[last],
            nominal_change_pct=change(s, first, last) if len(s) >= 2 else np.nan,
            real_first_year=int(real.index.min()) if len(real) else None,
            real_last_year=int(real.index.max()) if len(real) else None,
            real_change_pct=change(real, real.index.min(), real.index.max())
            if len(real) >= 2
            else np.nan,
            precrisis_peak_year=peak,
            precrisis_peak_value=s.loc[peak] if peak is not None else np.nan,
            postcrisis_trough_year=trough,
            postcrisis_trough_value=s.loc[trough] if trough is not None else np.nan,
            peak_to_trough_pct=change(s, peak, trough),
            trough_to_latest_pct=change(s, trough, last),
            peak_to_latest_pct=change(s, peak, last),
        )
        rows.append(row)
    return pd.DataFrame(rows)


def government_history(frame, governments, cpi, level, metric):
    """Descriptive changes between fully observed years inside each presidency."""
    rows = []
    for gov in governments[governments.level == level].itertuples():
        s = series_for(frame, gov.code)
        start = pd.Timestamp(gov.start)
        end = pd.Timestamp(gov.end) if pd.notna(gov.end) and gov.end else pd.Timestamp("2026-01-01")
        years = [
            int(y)
            for y in s.index
            if pd.Timestamp(f"{y}-01-01") >= start and pd.Timestamp(f"{y + 1}-01-01") <= end
        ]
        row = dict(
            metric=metric,
            code=gov.code,
            name=gov.name,
            leader=gov.leader,
            party=gov.party,
            start=gov.start,
            end=gov.end,
            observed_complete_years=len(years),
            first_year=None,
            last_year=None,
            nominal_change_pct=np.nan,
            annualised_pct=np.nan,
            real_change_pct=np.nan,
        )
        if len(years) >= 2:
            a, b = min(years), max(years)
            pct = change(s, a, b)
            row.update(
                first_year=a,
                last_year=b,
                nominal_change_pct=pct,
                annualised_pct=100 * ((s.loc[b] / s.loc[a]) ** (1 / (b - a)) - 1),
            )
            if a in cpi.index and b in cpi.index:
                row["real_change_pct"] = 100 * ((1 + pct / 100) / (cpi.loc[b] / cpi.loc[a]) - 1)
        rows.append(row)
    return pd.DataFrame(rows)


def run_history(root):
    root = Path(root)
    snapshot = root / "data/snapshots/block01"
    figures = root / "reports/figures/history"
    tables = root / "reports/tables/history"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)

    def read(name):
        return pd.read_csv(snapshot / name, dtype={"code": str, "muniCode": str})

    values = read("valuations.csv")
    ipv = read("purchase_index.csv")
    rents = read("rent_general_history.csv")
    cpi = series_for(read("cpi.csv"))
    govs = read("governments.csv")
    municipal = read("municipal_purchase.csv")
    cities = read("selected_cities.csv")
    fiscal = load_rental_snapshot(snapshot)
    p = series_for(values, level="national")
    r = series_for(rents)
    t = read("purchase_transaction_total.csv")
    t = t.groupby("year").agg(value=("value", "mean"), quarters=("value", "count"))
    t = t.loc[t.quarters == 4, "value"]
    shared = sorted(set(series_for(ipv).index) & set(r.index) & set(cpi.index))
    a, b = shared[0], shared[-1]
    compare = pd.DataFrame(index=shared)
    compare.index.name = "year"
    for label, s in [("purchase", series_for(ipv)), ("rent", r)]:
        compare[label + "_nominal"] = s.loc[shared] / s.loc[a] * 100
        compare[label + "_real"] = compare[label + "_nominal"] / (cpi.loc[shared] / cpi.loc[a])
    compare["cpi"] = cpi.loc[shared] / cpi.loc[a] * 100
    compare.to_csv(tables / "national_common_history.csv", float_format="%.8f")
    national = pd.DataFrame(
        {
            "purchase_valuation_eur_m2": p,
            "purchase_transaction_eur_dwelling": t,
            "rent_ipva": r,
            "cpi": cpi,
        }
    )
    national.index.name = "year"
    national.to_csv(tables / "national_levels.csv", float_format="%.8f")
    summaries = {}
    for level in ["national", "region", "province"]:
        table = history_summary(values[values.level == level], cpi, ["code", "name"])
        table.to_csv(tables / f"{level}_purchase_history.csv", index=False, float_format="%.8f")
        summaries[level] = table
    named_municipal = municipal.merge(
        cities[["muniCode", "muni"]], left_on="code", right_on="muniCode"
    )
    named_municipal = named_municipal.rename(columns={"muni": "name"})
    history_summary(named_municipal, cpi, ["code", "name"]).to_csv(
        tables / "municipal_purchase_history.csv", index=False, float_format="%.8f"
    )
    history_summary(rents, cpi, ["code", "name"]).drop(
        columns=[
            c
            for c in summaries["national"].columns
            if c.startswith(("precrisis", "postcrisis", "peak_to", "trough_to"))
        ]
    ).to_csv(tables / "rent_index_history.csv", index=False, float_format="%.8f")
    fiscal_history = history_summary(fiscal, cpi, ["level", "code", "name", "unit"])
    fiscal_history.drop(
        columns=[
            c
            for c in fiscal_history.columns
            if c.startswith(("precrisis", "postcrisis", "peak_to", "trough_to"))
        ]
    ).to_csv(tables / "fiscal_rent_history.csv", index=False, float_format="%.8f")
    mandates = pd.concat(
        [
            government_history(
                values[values.level == "national"], govs, cpi, "national", "purchase_valuation"
            ),
            government_history(rents, govs, cpi, "national", "rent_ipva"),
            government_history(
                values[values.level == "region"], govs, cpi, "region", "purchase_valuation"
            ),
        ],
        ignore_index=True,
    )
    mandates.to_csv(tables / "government_history.csv", index=False, float_format="%.8f")
    rates = pd.DataFrame(
        {
            "purchase_ipv_pct": annual_changes(series_for(ipv)),
            "rent_ipva_pct": annual_changes(r),
            "cpi_pct": annual_changes(cpi),
        }
    )
    rates.index.name = "year"
    rates.to_csv(tables / "national_annual_changes.csv", float_format="%.8f")
    paths = []

    def save(fig, filename):
        fig.text(
            0.01,
            0.006,
            "Fuentes: INE y MIVAU · medias anuales completas · gobiernos: contexto, no causalidad",
            fontsize=8,
            color="#555",
        )
        fig.tight_layout(rect=[0, 0.025, 1, 0.97])
        path = figures / filename
        with plt.rc_context({"svg.fonttype": "none", "svg.hashsalt": "spain-housing-history"}):
            fig.savefig(path, metadata={"Date": None})
        plt.close(fig)
        paths.append(path)

    fig, axes = plt.subplots(3, 1, figsize=(12, 11))
    for ax, s, title, unit, color in [
        (axes[0], p, "Compra: tasación de vivienda libre, 1995–2025", "€/m²", BUY),
        (axes[1], t, "Compra: transacciones de segunda mano libre, 2004–2025", "€/vivienda", BUY),
        (axes[2], r, "Alquiler: índice general IPVA, 2011–2024", "Índice INE (base 2015)", RENT),
    ]:
        ax.plot(s.index, s.values, color=color, lw=2.4)
        style(ax, title, unit)
    save(fig, "01_national_long_history.svg")

    fig, axes = plt.subplots(2, 1, figsize=(13, 9))
    for ax, s, title, unit, color in [
        (axes[0], p, "Compra y presidencias nacionales desde 1995", "Tasación €/m²", BUY),
        (axes[1], r, "Alquiler y presidencias nacionales desde 2011", "IPVA", RENT),
    ]:
        ax.plot(s.index, s.values, color=color, lw=2.4)
        gov_bands(ax, govs, "national", "00", s.index.min(), s.index.max() + 0.4, labels=True)
        style(ax, title, unit)
    save(fig, "02_national_governments.svg")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for label, color in [("purchase", BUY), ("rent", RENT)]:
        title = "Compra (IPV)" if label == "purchase" else "Alquiler (IPVA)"
        axes[0].plot(compare.index, compare[label + "_nominal"], label=title, color=color, lw=2.4)
        axes[1].plot(compare.index, compare[label + "_real"], label=title, color=color, lw=2.4)
    axes[0].plot(compare.index, compare.cpi, "--", label="IPC", color="#777")
    for ax, title in zip(
        axes, ["Precios nominales", "Precios ajustados por IPC nacional"], strict=True
    ):
        style(ax, f"{title}, {a}–{b}", f"{a} = 100")
        ax.legend()
    save(fig, "03_common_nominal_real.svg")

    fig, axes = plt.subplots(2, 1, figsize=(12, 9))
    real = real_series(p, cpi, 2025).dropna()
    axes[0].plot(p.index, p, label="Nominal", color=BUY)
    axes[0].plot(real.index, real, label="Euros constantes de 2025 (desde 2002)", color="#8e5593")
    style(axes[0], "Compra: distinguir el cambio monetario del cambio real", "Tasación €/m²")
    axes[0].legend()
    for col, label, color in [
        ("purchase_ipv_pct", "Compra (IPV)", BUY),
        ("rent_ipva_pct", "Alquiler (IPVA)", RENT),
        ("cpi_pct", "IPC", "#777"),
    ]:
        axes[1].plot(rates.index, rates[col], label=label, color=color)
    axes[1].axhline(0, color="#555", lw=0.7)
    style(axes[1], "Variación anual: compra desde 2008, alquiler desde 2012", "% interanual")
    axes[1].legend()
    save(fig, "04_cycles_inflation_rates.svg")

    for level, boundary_file, number in [
        ("region", "communities.geojson", "05"),
        ("province", "provinces.geojson", "06"),
    ]:
        boundary = json.loads((snapshot / boundary_file).read_text())
        # Cartographic generalisation only; numerical tables keep all territories.
        for feature in boundary["features"]:
            geometry = shape(feature["geometry"])
            if geometry.geom_type == "MultiPolygon":
                from shapely.geometry import MultiPolygon

                parts = [part for part in geometry.geoms if part.area >= 0.0001]
                geometry = MultiPolygon(parts) if parts else geometry
            feature["geometry"] = mapping(geometry.simplify(0.025, preserve_topology=True))

        table = summaries[level].set_index("code")
        frame = values[values.level == level]
        fixed = {}
        real_fixed = {}
        for code in table.index:
            s = series_for(frame, code)
            fixed[code] = change(s, 1995, 2025)
            real_fixed[code] = change(real_series(s, cpi, 2025), 2002, 2025)
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        map_panel(
            axes[0], boundary, fixed, "Cambio nominal de tasación, 1995–2025", "%", diverging=True
        )
        map_panel(
            axes[1], boundary, real_fixed, "Cambio real de tasación, 2002–2025", "%", diverging=True
        )
        save(fig, f"{number}_{level}_long_growth_maps.svg")

    regions = values[(values.level == "region") & ~values.code.isin(["18", "19"])]
    fig, axes = plt.subplots(6, 3, figsize=(16, 19))
    for ax, (code, data) in zip(axes.flat, regions.groupby("code"), strict=False):
        s = data.set_index("year").value.sort_index()
        ax.plot(s.index, s, color=BUY, lw=1.8)
        gov_bands(ax, govs, "region", code, 1995, 2025.4)
        style(ax, data.name.iloc[0], "Tasación €/m²")
        ax.set_xticks([1995, 2005, 2015, 2025])
    axes.flat[-1].axis("off")
    from matplotlib.patches import Patch

    from spain_housing.prices_analysis import COLORS

    parties = sorted(set(govs[govs.level == "region"].party))
    fig.legend(
        handles=[
            Patch(color=COLORS.get(party, "#aaa"), label=party, alpha=0.4) for party in parties
        ],
        loc="upper center",
        ncol=8,
        fontsize=8,
    )
    save(fig, "07_regional_governments_1995.svg")

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    categories = [
        ("urban_category", ["large_city", "periphery"], ["Grandes ciudades", "Periferias"]),
        ("coastal_category", ["coastal", "inland"], ["Costa", "Interior"]),
    ]
    merged = municipal.merge(cities, left_on="code", right_on="muniCode")
    rental_city = fiscal[(fiscal.level == "municipality") & (fiscal.unit == "EUR/m2/month")]
    rental_city = rental_city.merge(cities, left_on="code", right_on="muniCode")
    composition = []
    for col, (category, groups, labels) in enumerate(categories):
        for row, frame, base, title in [
            (0, merged, 2005, "Compra: tasación, 2005–2025"),
            (1, rental_city, 2011, "Alquiler fiscal, 2011–2024"),
        ]:
            for group, label in zip(groups, labels, strict=True):
                f = frame[frame[category] == group]
                wide = f.pivot(index="year", columns="code", values="value")
                # Fixed balanced panel; never change cities contributing to the average.
                wide = wide.reindex(range(base, int(wide.index.max()) + 1)).dropna(axis=1)
                if wide.shape[1]:
                    index = (wide / wide.loc[base] * 100).mean(axis=1)
                    axes[row, col].plot(
                        index.index, index, label=f"{label} (n={wide.shape[1]})", lw=2
                    )
                    composition.extend(
                        dict(
                            metric=title,
                            category=category,
                            group=group,
                            code=code,
                            first_year=base,
                            last_year=int(wide.index.max()),
                        )
                        for code in wide.columns
                    )
            style(axes[row, col], title, f"{base} = 100 · media no ponderada")
            axes[row, col].legend()
    pd.DataFrame(composition).to_csv(tables / "profile_fixed_samples.csv", index=False)
    save(fig, "08_city_profiles_long_history.svg")

    findings = {
        "valuation_window": [int(p.index.min()), int(p.index.max())],
        "rent_window": [int(r.index.min()), int(r.index.max())],
        "common_window": [a, b],
        "purchase_ipv_nominal_pct": change(series_for(ipv), a, b),
        "rent_ipva_nominal_pct": change(r, a, b),
        "purchase_ipv_real_pct": change(compare.purchase_real, a, b),
        "rent_ipva_real_pct": change(compare.rent_real, a, b),
        "inflation_pct": change(cpi, a, b),
        "national_purchase_cycle": summaries["national"].iloc[0].to_dict(),
    }
    (tables / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2))
    pn, pr = findings["purchase_ipv_nominal_pct"], findings["purchase_ipv_real_pct"]
    rn, rr = findings["rent_ipva_nominal_pct"], findings["rent_ipva_real_pct"]
    report = f"""# Bloque 1: perspectiva histórica ampliada

La serie de compra por tasación empieza en **1995**, las transacciones por vivienda en **2004**,
el IPV en **2007** y el alquiler general IPVA en **2011**. Se usan años completos: compra
hasta **2025** y alquiler hasta **2024**. Los trimestres de 2026 quedan fuera de las medias anuales.

## Evolución nacional y contexto político

![Series largas](figures/history/01_national_long_history.svg)

Las medidas conservan sus definiciones: tasación de vivienda libre por m², importe medio de
transacciones de segunda mano libre por vivienda e índice fiscal de alquiler. No hay una serie
nacional comparable de alquiler en €/vivienda desde 1995; no se inventa agregando medianas locales.

![Gobiernos nacionales](figures/history/02_national_governments.svg)

Las franjas identifican presidencias o gabinetes nacionales
y el partido de la presidencia autonómica.
La coincidencia temporal no estima efectos causales.
La tabla por gobierno excluye años de transición,
expone la duración y anualiza el cambio; los periodos sin dos años completos quedan sin resultado.
Se conservan intervalos históricos del Senado; pueden existir interinidades breves no detalladas.

## Ventana común de compra y alquiler: {a}–{b}

| Medida nacional | Cambio nominal | Cambio real |
| --- | ---: | ---: |
| Compra, IPV | {pn:+.2f}% | {pr:+.2f}% |
| Alquiler, IPVA general | {rn:+.2f}% | {rr:+.2f}% |

IPC nacional: **{findings["inflation_pct"]:+.2f}%**. Ambos precios usan
el mismo año inicial y final.
La ventana reciente 2021–2024 y el desglose por antigüedad de contrato se conservan en el
[informe inicial](block_01_prices.md). No se comparan porcentajes
de ventanas distintas.

![Nominal y real](figures/history/03_common_nominal_real.svg)
![Ciclo e inflación](figures/history/04_cycles_inflation_rates.svg)

El IPC disponible en el snapshot comienza en **2002**: las series reales y sus tablas lo indican.
Los valores reales son euros de 2025 o índices relativos al año base especificado; deflactar no mide
accesibilidad económica, que requiere ingresos. Se utiliza IPC nacional también para territorios.

## Comunidades, provincias y municipios

![Comunidades](figures/history/05_region_long_growth_maps.svg)
![Provincias](figures/history/06_province_long_growth_maps.svg)

Se generalizan los contornos y se omiten islotes menores de aproximadamente 1 km².
Los mapas comparan extremos fijos: 1995–2025 nominal y 2002–2025 real. Las tablas territoriales
indican primer y último dato, cobertura y años ausentes. También identifican máximo anterior a
la crisis **dentro de 1995–2008**, mínimo posterior **dentro de 2009–2015**, caída y recuperación.
Son extremos de ventanas explícitas, no fechas universales del ciclo de todos los territorios.

![Compra autonómica y partidos](figures/history/07_regional_governments_1995.svg)
![Perfiles municipales](figures/history/08_city_profiles_long_history.svg)

Compra municipal: **2005–2025**, selección de 30 casos. Alquiler fiscal por m² y por vivienda:
**2011–2024**, según cobertura. Los perfiles usan una muestra fija con todos los años observados,
media no ponderada de índices locales; el número de ciudades y su composición se publican.
Navarra y País Vasco mantienen sus fechas de inicio fiscal (2021 y 2024). Las tablas de alquiler
no asignan máximos anteriores a 2008 a series que empiezan después.

## Código y resultados reproducibles

- [Notebook con cálculos visibles y resultados](../notebooks/01b_price_history.ipynb).
- [Tablas históricas completas](tables/history/), incluidas cobertura, ciclos y presidencias.
- [Código del análisis](../src/spain_housing/price_history.py).
- [Fuentes originales y SHA-256](../data/snapshots/block01/source_manifest.json).

Ejecutar `python scripts/run_price_history.py` desde la raíz. No requiere descargar fuentes.
La ampliación del IPVA procede de la tabla INE 59056 (general por edificación), sin encadenar
porcentajes redondeados de notas de prensa ni extrapolar contratos nuevos hacia atrás.
"""
    (root / "reports/block_01_price_history.md").write_text(report, encoding="utf-8")
    return paths, findings
