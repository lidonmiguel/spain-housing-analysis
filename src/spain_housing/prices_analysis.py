"""Reproduce block 01 figures and results from the committed primary-source snapshots."""

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.patches import Patch, Polygon

COLORS = {
    "PP": "#2474b5",
    "PSOE": "#df5353",
    "PSOE + UP": "#a4508b",
    "PSOE + Sumar": "#dd7b9b",
    "PSC": "#df5353",
    "PNV": "#26846c",
    "ERC": "#d4a423",
    "ERC (funciones)": "#bda663",
    "JxCat": "#398a9f",
    "JxSÍ": "#55a2a2",
    "CiU": "#567f88",
    "PRC": "#9a772c",
    "FAC": "#727fa2",
    "CC": "#d08b32",
    "UPN": "#80549a",
    "GBai": "#65a54d",
    "Art.155 (PP nacional)": "#909090",
}
BUY = "#207b8e"
RENT = "#de7b36"


def change(series, first, last):
    """Endpoint change; missing dates are not replaced by nearest observations."""
    if first not in series.index or last not in series.index:
        return np.nan
    a, b = series.loc[first], series.loc[last]
    return 100 * (b / a - 1) if np.isfinite(a) and np.isfinite(b) and a > 0 else np.nan


def annual_changes(series):
    """Require consecutive years; never calculate across an unobserved year."""
    series = series.sort_index()
    result = series.pct_change(fill_method=None) * 100
    result.loc[series.index.to_series().diff() != 1] = np.nan
    return result


def series_for(frame, code="00", **filters):
    selected = frame[frame.code == code]
    for col, value in filters.items():
        selected = selected[selected[col] == value]
    if selected.duplicated("year").any():
        raise ValueError("Ambiguous series; select a single unit/contract/geographic level")
    return selected.set_index("year").value.sort_index()


def gov_bands(ax, governments, level, code, lo, hi, labels=False):
    rows = governments[(governments.level == level) & (governments.code == code)]
    for row in rows.itertuples():
        start = pd.Timestamp(row.start)
        end = pd.Timestamp(row.end) if pd.notna(row.end) and row.end else pd.Timestamp("2026-01-01")
        a = start.year + (start.dayofyear - 1) / (366 if start.is_leap_year else 365)
        b = end.year + (end.dayofyear - 1) / (366 if end.is_leap_year else 365)
        a, b = max(a, lo), min(b, hi)
        if b <= a:
            continue
        ax.axvspan(a, b, color=COLORS.get(row.party, "#aaa"), alpha=0.15, zorder=0)
        if labels and b - a > 1.25:
            ax.text(
                (a + b) / 2,
                0.98,
                row.party,
                transform=ax.get_xaxis_transform(),
                va="top",
                ha="center",
                fontsize=8,
                color="#38454f",
            )
    ax.set_xlim(lo, hi)


def style(ax, title, unit):
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel(unit)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)


def map_panel(ax, boundary, values, title, unit, diverging=False):
    finite = [v for v in values.values() if pd.notna(v)]
    if not finite:
        raise ValueError("No observed values for map")
    if diverging:
        limit = max(abs(min(finite)), abs(max(finite)), 1)
        norm, cmap = TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), plt.get_cmap("RdBu_r")
    else:
        norm, cmap = Normalize(min(finite), max(finite)), plt.get_cmap("YlOrRd")
    for feature in boundary["features"]:
        value = values.get(feature["properties"]["code"], np.nan)
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for polygon in polys:
            pts = np.asarray(polygon[0], dtype=float)
            if pts[:, 0].mean() < -12:  # Canary inset, explicitly labelled.
                pts = pts + [8.5, 8.2]
            ax.add_patch(
                Polygon(
                    pts,
                    facecolor=cmap(norm(value)) if pd.notna(value) else "#d7dde2",
                    edgecolor="white",
                    linewidth=0.45,
                )
            )
    ax.set_xlim(-10, 4.5)
    ax.set_ylim(35.0, 44.2)
    ax.set_aspect(1 / np.cos(np.deg2rad(40)))
    ax.set_axis_off()
    ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    ax.text(
        0.01,
        0.01,
        "Canarias reubicadas · gris: sin datos",
        transform=ax.transAxes,
        fontsize=7,
        color="#56616d",
    )
    plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.7, label=unit)


def endpoint_table(frame, first=2011, last=2024):
    rows = []
    for code, group in frame.groupby("code"):
        s = series_for(group, code)
        rows.append(
            {
                "code": code,
                "name": group.name.iloc[0] if "name" in group else code,
                "first_year": first,
                "last_year": last,
                "first_value": s.get(first, np.nan),
                "last_value": s.get(last, np.nan),
                "change_pct": change(s, first, last),
            }
        )
    return pd.DataFrame(rows)


def mandate_table(buy, rent, governments, cpi):
    records = []
    for row in governments[governments.level == "region"].itertuples():
        start = pd.Timestamp(row.start)
        end = pd.Timestamp(row.end) if pd.notna(row.end) and row.end else pd.Timestamp("2025-01-01")
        years = [
            y
            for y in range(2011, 2025)
            if pd.Timestamp(f"{y}-01-01") >= start and pd.Timestamp(f"{y + 1}-01-01") <= end
        ]
        a = series_for(buy, row.code)
        b = series_for(rent, row.code)
        common = [y for y in years if y in a.index and y in b.index and y in cpi.index]
        record = {
            "code": row.code,
            "name": row.name,
            "leader": row.leader,
            "party": row.party,
            "mandate_start": row.start,
            "mandate_end": row.end,
            "complete_common_years": len(common),
            "first_year": None,
            "last_year": None,
            "purchase_change_pct": np.nan,
            "rent_change_pct": np.nan,
            "purchase_annualised_pct": np.nan,
            "rent_annualised_pct": np.nan,
            "purchase_real_change_pct": np.nan,
            "rent_real_change_pct": np.nan,
        }
        if len(common) >= 2:
            first, last = common[0], common[-1]
            p, r = change(a, first, last), change(b, first, last)
            inflation = cpi.loc[last] / cpi.loc[first]
            record.update(
                first_year=first,
                last_year=last,
                purchase_change_pct=p,
                rent_change_pct=r,
                purchase_annualised_pct=100 * ((1 + p / 100) ** (1 / (last - first)) - 1),
                rent_annualised_pct=100 * ((1 + r / 100) ** (1 / (last - first)) - 1),
                purchase_real_change_pct=100 * ((1 + p / 100) / inflation - 1),
                rent_real_change_pct=100 * ((1 + r / 100) / inflation - 1),
            )
        records.append(record)
    return pd.DataFrame(records)


def markdown_table(frame, columns, headings=None, limit=None):
    selected = frame[columns].head(limit) if limit else frame[columns]
    lines = [
        "| " + " | ".join(headings or columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in selected.itertuples(index=False, name=None):
        parts = []
        for value in row:
            if pd.isna(value):
                parts.append("Sin datos")
            elif isinstance(value, (float, np.floating)):
                parts.append(f"{value:,.2f}")
            else:
                parts.append(str(value).replace("|", "/"))
        lines.append("| " + " | ".join(parts) + " |")
    return "\n".join(lines)


def load_rental_snapshot(snapshot):
    """Combine the two non-overlapping, versioned year partitions."""
    return pd.concat(
        [
            pd.read_csv(Path(snapshot) / name, dtype={"code": str})
            for name in ["rental_medians_2011_2017.csv.gz", "rental_medians_2018_2024.csv.gz"]
        ],
        ignore_index=True,
    )


def run_analysis(root, preview_dir=None, vector=False):
    root = Path(root)
    if preview_dir is not None:
        preview_dir = Path(preview_dir)
        preview_dir.mkdir(parents=True, exist_ok=True)
    snapshot = root / "data/snapshots/block01"
    figures = root / "reports/figures/block01"
    tables = root / "reports/tables/block01"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelcolor": "#38454f",
            "text.color": "#23343d",
            "figure.facecolor": "#fbfcfd",
            "axes.facecolor": "#fbfcfd",
            "svg.hashsalt": "spain-housing-block01",
        }
    )
    frames = {}
    for name in [
        "purchase_index",
        "rent_index",
        "cpi",
        "valuations",
        "governments",
        "municipal_purchase",
        "selected_cities",
        "purchase_transaction_total",
    ]:
        frames[name] = pd.read_csv(snapshot / f"{name}.csv", dtype={"code": str, "muniCode": str})
    # Keep the original report's municipal comparison window explicit.
    # The extended histories are generated separately by price_history.py.
    frames["municipal_purchase"] = (
        frames["municipal_purchase"]
        .loc[frames["municipal_purchase"].year.between(2011, 2024)]
        .copy()
    )
    frames["governments"] = (
        frames["governments"]
        .loc[
            (frames["governments"].start <= "2024-12-31")
            & (frames["governments"].end.isna() | (frames["governments"].end >= "2011-01-01"))
        ]
        .copy()
    )
    rentals = load_rental_snapshot(snapshot)
    buy = frames["purchase_index"]
    rent = frames["rent_index"]
    values = frames["valuations"]
    gov = frames["governments"]
    cpi = series_for(frames["cpi"])
    p = series_for(buy)
    r = series_for(rent, contract="Total")
    valuation = series_for(values, level="national")
    regional_rent = rentals.query('level == "region" and unit == "EUR/m2/month"').copy()
    regional_value = values.query('level == "region"').copy()
    region_names = dict(buy[["code", "name"]].drop_duplicates().itertuples(index=False, name=None))
    region_codes = sorted(code for code in region_names if "01" <= code <= "17")
    files = []

    def save(fig, name, subtitle):
        fig.suptitle(subtitle, fontsize=14, fontweight="bold", x=0.03, ha="left")
        fig.text(
            0.03,
            0.01,
            "Fuentes: INE / MIVAU · datos observados · contexto político descriptivo",
            fontsize=8,
            color="#64727d",
        )
        fig.tight_layout(rect=[0, 0.035, 1, 0.95])
        path = figures / f"{name}.png"
        fig.savefig(path, dpi=100, bbox_inches="tight")
        if vector:
            fig.savefig(figures / f"{name}.svg", metadata={"Date": None}, bbox_inches="tight")
        if preview_dir is not None:
            shutil.copyfile(path, preview_dir / path.name)
        plt.close(fig)
        files.append(path)

    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    axes[0].plot(valuation.index, valuation, color=BUY, linewidth=2.5)
    style(axes[0], "Valor tasado: media de 4 trimestres", "€/m² · vivienda libre")
    trans = frames["purchase_transaction_total"]
    axes[1].plot(trans.year + (trans.quarter - 1) / 4, trans.value, color=BUY, linewidth=2)
    style(axes[1], "Compraventa: valor medio trimestral", "€/vivienda · libre de segunda mano")
    axes[2].plot(r.index, r, "o-", color=RENT, linewidth=2.5)
    style(axes[2], "Alquiler: índice nacional IPVA", "Índice INE · 2015 = 100")
    axes[2].set_xticks(r.index)
    save(fig, "01_national_levels", "1. Evolución nacional: medidas distintas, unidades explícitas")

    fig, axes = plt.subplots(2, 1, figsize=(13, 8))
    for ax, s, title, color in [
        (axes[0], p, "Compraventa · IPV", BUY),
        (axes[1], r, "Alquiler · IPVA", RENT),
    ]:
        gov_bands(ax, gov, "national", "00", s.index.min(), s.index.max() + 0.8, labels=True)
        ax.plot(s.index + 0.5, s, "o-", color=color, linewidth=2.5)
        style(ax, title, "Índice de la fuente · media anual")
    save(fig, "02_national_governments", "2. Los precios y el calendario de gobiernos nacionales")

    common = sorted(set(p.index) & set(r.index) & set(cpi.index))
    first, last = common[0], common[-1]
    comparison = pd.DataFrame(
        {
            "year": common,
            "purchase_nominal_index": p.loc[common].to_numpy() / p.loc[first] * 100,
            "rent_nominal_index": r.loc[common].to_numpy() / r.loc[first] * 100,
            "cpi_index": cpi.loc[common].to_numpy() / cpi.loc[first] * 100,
        }
    )
    comparison["purchase_real_index"] = (
        comparison.purchase_nominal_index / comparison.cpi_index * 100
    )
    comparison["rent_real_index"] = comparison.rent_nominal_index / comparison.cpi_index * 100
    comparison.to_csv(tables / "national_comparison.csv", index=False)
    # Use the full general rental history for this comparison only.
    chart_rent = series_for(
        pd.read_csv(snapshot / "rent_general_history.csv", dtype={"code": str})
    )
    chart_years = sorted(set(p.index) & set(chart_rent.index) & set(cpi.index))
    chart_first, chart_last = chart_years[0], chart_years[-1]
    fig, ax = plt.subplots(figsize=(12, 5))
    for s, label, color in [
        (p, "Compraventa (IPV)", BUY),
        (chart_rent, "Alquiler (IPVA)", RENT),
        (cpi, "Precios generales (IPC)", "#7c8993"),
    ]:
        index = s.loc[chart_years] / s.loc[chart_first] * 100
        ax.plot(chart_years, index, "o-", label=label, color=color, lw=2.5)
    ax.legend(frameon=False)
    ax.set_xticks([chart_first, 2014, 2017, 2020, chart_last])
    style(ax, f"Ventana común {chart_first}–{chart_last}", f"{chart_first} = 100")
    save(
        fig,
        "03_indexed_comparison",
        "Compra y alquiler frente a los precios generales",
    )

    fig, axes = plt.subplots(2, 1, figsize=(13, 7))
    for ax, s, label, color in [
        (axes[0], p, "Compraventa (IPV)", BUY),
        (axes[1], r, "Alquiler (IPVA)", RENT),
    ]:
        growth = annual_changes(s)
        ax.bar(growth.index, growth, color=[color if v >= 0 else "#8f9ba5" for v in growth])
        ax.axhline(0, color="#495965", lw=0.7)
        style(ax, label, "Variación anual (%)")
    save(
        fig,
        "04_annual_changes",
        "Subidas y bajadas: la trayectoria no es una línea continua de crecimiento",
    )

    fig, axes = plt.subplots(2, 1, figsize=(13, 8))
    for ax, s, label, color in [(axes[0], p, "Compraventa", BUY), (axes[1], r, "Alquiler", RENT)]:
        years = sorted(set(s.index) & set(cpi.index))
        base = years[0]
        nominal = s.loc[years] / s.loc[base] * 100
        real = nominal / (cpi.loc[years] / cpi.loc[base])
        gov_bands(ax, gov, "national", "00", base, years[-1] + 0.8)
        ax.plot(np.array(years) + 0.5, nominal, label="Nominal", color=color, lw=2.3)
        ax.plot(
            np.array(years) + 0.5,
            real,
            label="Ajustado por IPC nacional",
            color=color,
            ls="--",
            lw=2.3,
        )
        style(ax, label, f"{base} = 100 · nominal y real")
        ax.legend(frameon=False)
    save(fig, "05_inflation", "3. Descontar la inflación cambia la lectura de las subidas")

    cities = frames["selected_cities"].rename(columns={"muniCode": "code", "muni": "name"})
    city_buy = frames["municipal_purchase"].merge(cities, on="code", validate="many_to_one")
    city_rent = rentals.query('level == "municipality" and unit == "EUR/m2/month"').merge(
        cities.drop(columns="name"), on="code", validate="many_to_one"
    )
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    groups = [
        (
            "urban_category",
            ["large_city", "periphery"],
            ["Ciudades seleccionadas", "Periferias seleccionadas"],
        ),
        (
            "coastal_category",
            ["coastal", "inland"],
            ["Costa seleccionada", "Interior seleccionado"],
        ),
    ]
    sample_counts = []
    for row, (frame, label) in enumerate([(city_buy, "Tasación"), (city_rent, "Alquiler")]):
        for col, (attribute, cats, labels) in enumerate(groups):
            for category, title in zip(cats, labels):
                subset = frame[frame[attribute] == category].copy()
                valid = [
                    code
                    for code, g in subset.groupby("code")
                    if set(range(2011, 2025)) <= set(g.year)
                ]
                subset = subset[subset.code.isin(valid)]
                baselines = subset[subset.year == 2011].set_index("code").value
                subset["indexed"] = subset.value / subset.code.map(baselines) * 100
                s = subset.groupby("year").indexed.mean()
                axes[row, col].plot(s.index, s, lw=2.3, label=f"{title} (n={len(valid)})")
                sample_counts.append(
                    {
                        "market": label,
                        "group": title,
                        "municipalities": len(valid),
                        "change_2011_2024_pct": s.get(2024, np.nan) - 100,
                    }
                )
            style(axes[row, col], label, "2011 = 100 · media municipal sin ponderar")
            axes[row, col].legend(frameon=False, fontsize=8)
    pd.DataFrame(sample_counts).to_csv(tables / "territorial_profiles.csv", index=False)
    save(
        fig,
        "06_territorial_profiles",
        "4. Perfiles territoriales: muestra fija y explícita de 30 municipios",
    )

    region_purchase = endpoint_table(regional_value)
    region_rental = endpoint_table(regional_rent)
    province_purchase = endpoint_table(values.query('level == "province"'))
    province_rental = endpoint_table(
        rentals.query('level == "province" and unit == "EUR/m2/month"')
    )
    for prefix, a, b in [
        ("regional", region_purchase, region_rental),
        ("provincial", province_purchase, province_rental),
    ]:
        combined = a.merge(b, on="code", how="outer", suffixes=("_purchase", "_rent"))
        combined.to_csv(tables / f"{prefix}_levels_and_growth.csv", index=False)
        boundary = json.loads(
            (
                snapshot / ("communities.geojson" if prefix == "regional" else "provinces.geojson")
            ).read_text()
        )
        fig, axes = plt.subplots(2, 2, figsize=(15, 11))
        for ax, table, field, title, unit, diverging in [
            (axes[0, 0], a, "last_value", "Tasación · 2024", "€/m²", False),
            (
                axes[0, 1],
                b,
                "last_value",
                "Alquiler mediano · 2024",
                "€/m²/mes · vivienda colectiva",
                False,
            ),
            (axes[1, 0], a, "change_pct", "Cambio de tasación · 2011–2024", "% nominal", True),
            (axes[1, 1], b, "change_pct", "Cambio de alquiler · 2011–2024", "% nominal", True),
        ]:
            map_panel(
                ax, boundary, table.set_index("code")[field].to_dict(), title, unit, diverging
            )
        save(
            fig,
            "07_regional_maps" if prefix == "regional" else "12_provincial_maps",
            "5. Comunidades: nivel y crecimiento"
            if prefix == "regional"
            else "7. Provincias: diferencias dentro del país",
        )

    fig, axes = plt.subplots(1, 2, figsize=(16, 9))
    for ax, frame, title in [
        (axes[0], buy[buy.code.isin(region_codes)], "Compraventa · IPV"),
        (axes[1], regional_rent, "Alquiler · mediana SERPAVI"),
    ]:
        matrix = frame.pivot(index="code", columns="year", values="value").reindex(region_codes)
        matrix = matrix.reindex(columns=range(2011, 2025))
        growth = matrix.pct_change(axis=1, fill_method=None).iloc[:, 1:] * 100
        limit = max(np.nanmax(np.abs(growth.to_numpy())), 1)
        image = ax.imshow(growth, aspect="auto", cmap="RdBu_r", vmin=-limit, vmax=limit)
        ax.set_yticks(range(len(region_codes)), [region_names[c] for c in region_codes])
        ax.set_xticks(range(len(growth.columns)), growth.columns, rotation=90)
        ax.set_title(title, loc="left")
        plt.colorbar(image, ax=ax, shrink=0.7, label="Variación anual (%)")
    save(fig, "08_regional_heatmap", "Ritmos anuales: distintas trayectorias territoriales")

    for label, frame, color in [("purchase", buy, BUY), ("rent", regional_rent, RENT)]:
        fig, axes = plt.subplots(6, 3, figsize=(17, 20))
        for ax, code in zip(axes.flat, region_codes):
            s = series_for(frame, code).reindex(range(2011, 2025))
            gov_bands(ax, gov, "region", code, 2011, 2025)
            if s.notna().any():
                base = s.dropna().iloc[0]
                ax.plot(s.index + 0.5, s / base * 100, color=color, lw=2)
            else:
                ax.text(0.5, 0.5, "Sin datos de alquiler", transform=ax.transAxes, ha="center")
            base_year = int(s.first_valid_index()) if s.notna().any() else 2011
            style(ax, region_names[code], f"{base_year} = 100")
            ax.set_xticks([2011, 2015, 2019, 2023])
        axes.flat[-1].set_axis_off()
        handles = [
            Patch(color=color, alpha=0.4, label=party)
            for party, color in COLORS.items()
            if party in set(gov.query('level == "region"').party)
        ]
        axes.flat[-1].legend(handles=handles, loc="center", ncol=2, fontsize=9, frameon=False)
        save(
            fig,
            f"09_regional_governments_{label}",
            "6. Presidencias autonómicas y precios · partido de presidencia, no coalición completa",
        )

    mandates = mandate_table(buy, regional_rent, gov, cpi)
    mandates.to_csv(tables / "regional_mandate_changes.csv", index=False)
    eligible = mandates.dropna(subset=["purchase_annualised_pct", "rent_annualised_pct"])
    fig, ax = plt.subplots(figsize=(12, 7))
    for party, group in eligible.groupby("party"):
        ax.scatter(
            group.purchase_annualised_pct,
            group.rent_annualised_pct,
            c=COLORS.get(party, "#666"),
            label=party,
            alpha=0.8,
            s=65,
            edgecolors="white",
        )
    ax.axhline(0, color="#666", lw=0.7)
    ax.axvline(0, color="#666", lw=0.7)
    style(
        ax,
        "Cada punto: un periodo observado dentro de un mandato",
        "Alquiler: cambio anualizado (%)",
    )
    ax.set_xlabel("Compraventa (IPV): cambio anualizado (%)")
    ax.legend(frameon=False, ncol=3)
    save(
        fig,
        "10_mandate_comparison",
        "Comparación descriptiva: años completos comunes, sin atribución causal",
    )

    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    municipal_tables = []
    boundary = json.loads((snapshot / "communities.geojson").read_text())
    for row, (frame, label) in enumerate([(city_buy, "Tasación"), (city_rent, "Alquiler")]):
        endpoint = endpoint_table(frame).merge(
            cities[["code", "lat", "lng"]], on="code", validate="one_to_one"
        )
        endpoint["market"] = label
        municipal_tables.append(endpoint)
        for col, (field, title) in enumerate(
            [("last_value", f"{label} · 2024"), ("change_pct", f"{label} · cambio 2011–2024")]
        ):
            ax = axes[row, col]
            for feature in boundary["features"]:
                geom = feature["geometry"]
                polygons = (
                    geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
                )
                for polygon in polygons:
                    pts = np.array(polygon[0])
                    if pts[:, 0].mean() < -12:
                        continue
                    ax.add_patch(Polygon(pts, facecolor="#e5eaee", edgecolor="white", lw=0.5))
            observed = endpoint.dropna(subset=[field, "lat", "lng"])
            cmap = "YlOrRd" if col == 0 else "RdBu_r"
            vmax = max(abs(observed[field].min()), abs(observed[field].max()), 1)
            norm = (
                Normalize(observed[field].min(), observed[field].max())
                if col == 0
                else TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
            )
            dots = ax.scatter(
                observed.lng,
                observed.lat,
                c=observed[field],
                cmap=cmap,
                norm=norm,
                s=60,
                edgecolors="white",
                lw=0.5,
                zorder=3,
            )
            ax.set_xlim(-10, 4.5)
            ax.set_ylim(35.0, 44.2)
            ax.set_aspect(1 / np.cos(np.deg2rad(40)))
            ax.set_axis_off()
            ax.set_title(title, loc="left", fontweight="bold")
            plt.colorbar(
                dots,
                ax=ax,
                shrink=0.7,
                label=("€/m²" if row == 0 else "€/m²/mes") if col == 0 else "% nominal",
            )
    municipal = pd.concat(municipal_tables, ignore_index=True)
    municipal.to_csv(tables / "selected_municipalities.csv", index=False)
    save(
        fig,
        "13_municipal_maps",
        "Municipios: puntos geolocalizados de una muestra explícita de 30 ciudades",
    )

    selected_totals = rentals.query(
        'level == "municipality" and unit == "EUR/dwelling/month" and year == 2024'
    )
    selected_totals = selected_totals[selected_totals.code.isin(cities.code)].sort_values("value")
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.barh(selected_totals.name, selected_totals.value, color=RENT)
    style(ax, "Mediana mensual por vivienda colectiva · 2024", "Municipio")
    ax.set_xlabel("€/vivienda/mes · alquiler declarado, no oferta anunciada")
    selected_totals.to_csv(tables / "municipal_rent_per_dwelling_2024.csv", index=False)
    save(
        fig,
        "14_municipal_rent_totals",
        "El coste por vivienda: diferencias dentro de la muestra municipal",
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    for ax, frame, title in [
        (axes[0], city_buy, "Tasación · €/m²"),
        (axes[1], city_rent, "Alquiler · €/m²/mes"),
    ]:
        for code in ["08019", "08015", "28079", "28065", "46250", "50297"]:
            s = series_for(frame, code)
            name = cities.set_index("code").loc[code, "name"]
            ax.plot(s.index, s, label=name, lw=2)
        style(ax, title, title.split("·")[1].strip())
        ax.legend(frameon=False, fontsize=8)
    save(
        fig,
        "15_municipal_cases",
        "Casos definidos: Barcelona/Badalona, Madrid/Getafe, Valencia y Zaragoza",
    )

    fig, ax = plt.subplots(figsize=(12, 5))
    for contract in ["Total", "Nuevo contrato", "Contrato existente"]:
        s = series_for(rent, contract=contract)
        ax.plot(s.index, s / s.loc[2021] * 100, "o-", label=contract, lw=2.3)
    ax.set_xticks([2021, 2022, 2023, 2024])
    style(ax, "IPVA nacional según antigüedad del contrato", "2021 = 100")
    ax.legend(frameon=False)
    save(
        fig,
        "16_rent_contracts",
        "Un mismo mercado, ritmos distintos: contratos nuevos y existentes",
    )

    buy_change, rent_change, inflation = (
        change(p, first, last),
        change(r, first, last),
        change(cpi, first, last),
    )
    national_rows = []
    for leader, party, start, end in [
        ("Zapatero", "PSOE", "2004-04-17", "2011-12-21"),
        ("Rajoy", "PP", "2011-12-21", "2018-06-02"),
        ("Sánchez", "PSOE; coaliciones desde 2020", "2018-06-02", "2026-01-01"),
    ]:
        record = {"president": leader, "political_context": party}
        for market, observed in [("purchase", p), ("rent", r)]:
            years = [
                y
                for y in observed.index
                if pd.Timestamp(f"{y}-01-01") >= pd.Timestamp(start)
                and pd.Timestamp(f"{y + 1}-01-01") <= pd.Timestamp(end)
            ]
            record[f"{market}_window"] = (
                f"{min(years)}–{max(years)}" if len(years) >= 2 else "Insuficiente"
            )
            record[f"{market}_change_pct"] = (
                change(observed, min(years), max(years)) if len(years) >= 2 else np.nan
            )
        national_rows.append(record)
    national_periods = pd.DataFrame(national_rows)
    national_periods.to_csv(tables / "national_presidential_periods.csv", index=False)
    party_rows = []
    for party, group in eligible.groupby("party"):
        party_rows.append(
            {
                "party_of_presidency": party,
                "observed_intervals": len(group),
                "purchase_rising": int((group.purchase_change_pct > 0).sum()),
                "purchase_falling": int((group.purchase_change_pct < 0).sum()),
                "rent_rising": int((group.rent_change_pct > 0).sum()),
                "rent_falling": int((group.rent_change_pct < 0).sum()),
            }
        )
    party_patterns = pd.DataFrame(party_rows)
    party_patterns.to_csv(tables / "party_observed_patterns.csv", index=False)
    findings = {
        "common_window": [first, last],
        "purchase_nominal_change_pct": buy_change,
        "rent_nominal_change_pct": rent_change,
        "cpi_change_pct": inflation,
        "purchase_real_change_pct": 100 * ((1 + buy_change / 100) / (1 + inflation / 100) - 1),
        "rent_real_change_pct": 100 * ((1 + rent_change / 100) / (1 + inflation / 100) - 1),
        "purchase_2007_2025_change_pct": change(p, 2007, 2025),
        "purchase_trough_year": int(p.idxmin()),
        "valuation_2024_eur_m2": valuation.loc[2024],
        "new_contract_rent_change_pct": change(
            series_for(rent, contract="Nuevo contrato"), first, last
        ),
        "existing_contract_rent_change_pct": change(
            series_for(rent, contract="Contrato existente"), first, last
        ),
        "regional_rental_coverage": len(regional_rent.code.unique()),
        "rental_municipalities_2024": int(
            rentals.query('level == "municipality" and year == 2024').code.nunique()
        ),
        "selected_municipalities": len(cities),
        "mandate_comparisons_with_two_years": len(eligible),
    }
    (tables / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2))
    source_urls = json.loads((snapshot / "source_manifest.json").read_text())
    top_rent = region_rental.sort_values("last_value", ascending=False).head(5)
    top_growth = region_rental.sort_values("change_pct", ascending=False).head(5)
    falling = (eligible.purchase_change_pct < 0).sum()
    rising = (eligible.purchase_change_pct > 0).sum()
    profiles_md = markdown_table(
        pd.DataFrame(sample_counts),
        ["market", "group", "municipalities", "change_2011_2024_pct"],
        ["Medida", "Grupo de muestra", "Municipios", "Cambio 2011–2024 (%)"],
    )
    rent_md = markdown_table(
        top_rent,
        ["name", "last_value", "change_pct"],
        ["Territorio", "€/m²/mes", "Cambio 2011–2024 (%)"],
    )
    national_md = markdown_table(
        national_periods,
        [
            "president",
            "political_context",
            "purchase_window",
            "purchase_change_pct",
            "rent_window",
            "rent_change_pct",
        ],
        ["Presidencia", "Contexto", "Compra: años", "IPV (%)", "Alquiler: años", "IPVA (%)"],
    )
    patterns_md = markdown_table(
        party_patterns,
        [
            "party_of_presidency",
            "observed_intervals",
            "purchase_rising",
            "purchase_falling",
            "rent_rising",
            "rent_falling",
        ],
        [
            "Presidencia",
            "Intervalos",
            "Compra sube",
            "Compra baja",
            "Alquiler sube",
            "Alquiler baja",
        ],
    )
    report = f"""# Evolución de la vivienda en España: precios, territorio y contexto político

**Perspectiva histórica ampliada:**
[Compra desde 1995 y alquiler desde 2011](block_01_price_history.md).
Este informe conserva las ventanas iniciales y la comparación reciente.

**Análisis ejecutado con datos reales.** Publicaciones recuperadas el 6 de octubre de 2026.
Las series anuales de compraventa llegan a 2025; alquileres fiscales e IPVA, a 2024.
Los trimestres de 2026 se muestran únicamente en la serie trimestral de valor por vivienda.

## 1. Evolución nacional

En la ventana común **{first}–{last}**, el índice de compraventa (IPV) aumentó
**{buy_change:.2f}%** y el índice de alquiler (IPVA), **{rent_change:.2f}%**.
Desde 2007 hasta 2025, el IPV cambió **{findings["purchase_2007_2025_change_pct"]:.2f}%**;
su mínimo anual dentro de esa serie aparece en **{findings["purchase_trough_year"]}**.
La trayectoria incluye caídas y recuperación: elegir únicamente un tramo ascendente
ocultaría parte de la historia. El valor tasado medio de 2024, calculado como media
simple de los cuatro trimestres, es **{valuation.loc[2024]:,.2f} €/m²**.

![Niveles nacionales](figures/block01/01_national_levels.png)
![Comparación común](figures/block01/03_indexed_comparison.png)

La comparación con los precios generales abarca **2011–2024**, el periodo completo
con datos disponibles de compra, alquiler general e IPC; base **2011 = 100**.

![Cambios anuales](figures/block01/04_annual_changes.png)

El valor de transacciones por vivienda corresponde a vivienda libre de segunda mano;
la tasación por m² y el IPV no miden exactamente el mismo universo. El IPVA es un
índice de alquileres, no euros por vivienda. No se ha fabricado una mediana nacional
en euros a partir de medianas regionales.

## 2. Gobiernos nacionales

Las franjas distinguen presidencias del PSOE y PP y las etapas de coalición nacional
PSOE–UP y PSOE–Sumar. Los puntos anuales se sitúan a mitad de año: representan medias
anuales, no una medición precisa el día del cambio de gobierno. Las caídas posteriores
a 2007 y la recuperación atraviesan distintas etapas políticas; el gráfico permite
localizar esas etapas, pero no identifica responsabilidad causal.

![Gobiernos nacionales](figures/block01/02_national_governments.png)

**Cambios entre años completos disponibles dentro de cada presidencia:**

{national_md}

Los periodos tienen distinta duración y parten de momentos diferentes del ciclo.
Se agrupan las coaliciones de Sánchez bajo su presidencia en esta tabla, mientras
el gráfico conserva sus etapas. El alquiler no tiene observaciones comparables
para Zapatero o Rajoy en el IPVA recuperado: «insuficiente» no significa estabilidad.

## 3. Inflación y crecimiento real

Entre {first} y {last}, el IPC general aumentó **{inflation:.2f}%**. Al descontarlo,
el cambio del IPV es **{findings["purchase_real_change_pct"]:.2f}%**, frente a
**{findings["rent_real_change_pct"]:.2f}%** para el IPVA. Estos cambios reales no miden
el esfuerzo de cada hogar: para eso se necesitan ingresos y gasto individuales.

![Inflación](figures/block01/05_inflation.png)

## 4. Grandes ciudades, periferias, costa e interior

Se comparan **30 municipios seleccionados de forma explícita**, usando una muestra
fija con observaciones en los 14 años 2011–2024. Cada municipio se rebasa a 2011=100
y recibe el mismo peso. Los grupos son descriptivos de esta muestra y **no son
estimaciones representativas de toda la costa o todas las periferias españolas**.
La categoría urbana y la costera son dimensiones separadas.

![Perfiles territoriales](figures/block01/06_territorial_profiles.png)

{profiles_md}

## 5. Comunidades autónomas

Los mapas separan el precio de 2024 y el crecimiento 2011–2024. La cobertura del
alquiler fiscal de 2024 comprende las 17 comunidades más Ceuta y Melilla. **Navarra
solo aporta datos desde 2021 y País Vasco desde 2024**: aparecen en el mapa de niveles,
pero su crecimiento 2011–2024 queda en gris. No se extrapola la cobertura ausente.
Una región puede tener precios altos y crecimiento moderado, o precios inicialmente
bajos y una subida intensa: niveles y variaciones responden a preguntas distintas.

![Mapas autonómicos](figures/block01/07_regional_maps.png)
![Variaciones anuales](figures/block01/08_regional_heatmap.png)

**Mayores medianas regionales de alquiler de la cobertura observada, 2024:**

{rent_md}

**Mayores crecimientos nominales de la mediana regional de alquiler:**

{markdown_table(top_growth, ["name", "change_pct"], ["Territorio", "Cambio 2011–2024 (%)"])}

## 6. Gobiernos autonómicos

Se han incorporado presidencias de las **17 comunidades**, extraídas de los dosieres
del Senado y sus referencias a nombramientos oficiales. Las franjas regionales
muestran **la adscripción de la presidencia**, no la composición completa del gabinete.
Esto evita convertir un gobierno de coalición en un gobierno monocolor por omisión.
Cataluña identifica el periodo del artículo 155 y el intervalo de funciones posterior
a la inhabilitación de Torra. Las fechas se basan en nombramiento por real decreto;
pueden diferir unos días de la toma de posesión. Interinidades menores no quedan
completamente representadas por la lista de nombramientos y deben leerse con esa limitación.

![Presidencias y compra](figures/block01/09_regional_governments_purchase.png)
![Presidencias y alquiler](figures/block01/09_regional_governments_rent.png)

La tabla compara exclusivamente **años completos comunes dentro de cada intervalo**,
con al menos dos observaciones. De {len(mandates)} intervalos regionales registrados,
**{len(eligible)}** permiten comparar ambas medidas. En ellos hay **{rising}** periodos
con subida del IPV y **{falling}** con bajada. Los intervalos sin años suficientes
quedan registrados como insuficientes; no reciben un crecimiento de cero.
Los cambios se refieren al periodo observado entre medias anuales, no al mandato completo.
El ajuste real de esta tabla utiliza el IPC nacional, no el IPC de cada comunidad.

![Comparación de intervalos](figures/block01/10_mandate_comparison.png)

[Tabla completa de periodos y cambios](tables/block01/regional_mandate_changes.csv).
No se agregan comunidades y etapas en un ranking causal de partidos. Para establecer
si una política causó un cambio harán falta medidas concretas y un diseño comparativo.

## 7. Provincias y municipios

La fuente fiscal incluye **{findings["rental_municipalities_2024"]} municipios con datos
de alquiler en 2024**. Los mapas provinciales utilizan todas las observaciones
comparables disponibles. Los mapas municipales geolocalizan los 30 casos seleccionados
con CartoCiudad, verificando que el código INE devuelto coincide con el previsto.
Las tasaciones municipales se obtienen de la tabla del ministerio para municipios
mayores de 25.000 habitantes; no se repite un valor provincial como si fuera municipal.

![Mapas provinciales](figures/block01/12_provincial_maps.png)
![Mapas municipales](figures/block01/13_municipal_maps.png)
![Alquiler por vivienda](figures/block01/14_municipal_rent_totals.png)
![Casos municipales](figures/block01/15_municipal_cases.png)

Los importes por vivienda son medianas de alquiler declarado de vivienda colectiva.
Una mediana por vivienda depende de la superficie y composición del parque: no basta
para concluir que el precio por m² es mayor en el mismo grado.

## 8. Lectura política de los resultados

Este bloque establece **cuándo, cuánto y dónde** cambian los precios. No contrasta aún
causas como turismo, falta de construcción, concentración de propiedad o efectos de
leyes. Ninguno de esos mecanismos queda probado únicamente por coincidir con un gobierno.

**Dirección observada del cambio por partido de la presidencia autonómica:**

{patterns_md}

Se cuentan intervalos de territorios, no viviendas, votantes ni mandatos completos.
La cobertura y duración son desiguales: esta tabla permite revisar afirmaciones
absolutas como «solo sube bajo un partido», pero no mide qué partido lo hace mejor.
La adscripción de la presidencia tampoco identifica qué socios aprobaron una medida.

El alquiler de contratos nuevos crece **{findings["new_contract_rent_change_pct"]:.2f}%**
en {first}–{last}, frente a **{findings["existing_contract_rent_change_pct"]:.2f}%** en
contratos existentes. Es una diferencia importante para interpretar discursos que
mezclan la situación de quien busca vivienda con la de quien conserva un contrato.

![Antigüedad del contrato](figures/block01/16_rent_contracts.png)

## Fuentes, reproducción y límites

- INE: IPV (tabla 79563), IPVA (59004) e IPC general (50913).
- MIVAU: valor tasado libre por m²; SERPAVI 2011–2024, vivienda colectiva, medianas;
  transacciones de segunda mano por vivienda y tasaciones municipales.
- Senado: dosieres históricos de presidentes autonómicos; BOE y Moncloa para contexto nacional.
- CartoCiudad (IGN): posiciones de los municipios seleccionados.
- Code for Germany / Click That 'Hood: límites de comunidades y provincias, simplificados
  para ilustración; geometrías fechadas en 2014. Se unen por códigos oficiales, no
  por el atributo autonómico del fichero provincial, cuya codificación es diferente.

Los promedios anuales de tasación son medias simples de cuatro trimestres; no están
ponderados por número de tasaciones. Las medianas fiscales cambian con la composición
del parque declarado y no son índices de precio constante ni anuncios de nuevos alquileres.
Los precios están separados por concepto. Se eliminan duplicados exactos del fichero
original de tasaciones de Navarra antes
de comprobar que hay cuatro trimestres distintos; se rechazan valores contradictorios.
No se extrapolan 2026 parcial ni cobertura
fiscal ausente. Los gráficos políticos son descriptivos, sin controles ni estimación causal.

Ejecutar desde la raíz: `python scripts/run_block01.py`. El notebook también reproduce
las figuras con los snapshots versionados, sin descargar 71 MB durante cada ejecución.
Para reconstruir desde las publicaciones originales: `python scripts/build_block01_data.py`
El script recupera también los registros políticos y la selección geográfica documentados.
Las URL y SHA-256 de los ficheros se conservan en el manifiesto.

"""
    report += "\n".join(f"- [{item['source_file']}]({item['url']})" for item in source_urls)
    (root / "reports/block_01_prices.md").write_text(report + "\n", encoding="utf-8")
    return files, findings
