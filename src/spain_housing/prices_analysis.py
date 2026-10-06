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


def load_purchase_data(root):
    """Load observed purchase prices from 2000; preserve each series' definition."""
    snapshot = Path(root) / "data/snapshots/block01"
    values = pd.read_csv(snapshot / "valuations.csv", dtype={"code": str})
    values = values[values.year >= 2000].copy()
    municipal = pd.read_csv(snapshot / "municipal_purchase.csv", dtype={"code": str})
    cities = pd.read_csv(snapshot / "selected_cities.csv", dtype={"muniCode": str})
    municipal = municipal.merge(cities, left_on="code", right_on="muniCode", validate="many_to_one")
    municipal = municipal.rename(columns={"muni": "name"})
    cpi = series_for(pd.read_csv(snapshot / "cpi.csv", dtype={"code": str}))
    gov = pd.read_csv(snapshot / "governments.csv", dtype={"code": str})
    for frame, keys in [(values, ["level", "code", "year"]), (municipal, ["code", "year"])]:
        if frame.duplicated(keys).any() or not (frame.value > 0).all():
            raise ValueError("Purchase observations must be unique and positive")
    return values, municipal, cpi, gov


def run_analysis(root, preview_dir=None, vector=False):
    """Generate purchase-only block 1, with nominal history from 2000."""
    from spain_housing.price_history import government_history, history_summary, real_series

    root = Path(root)
    figures = root / "reports/figures/block01"
    tables = root / "reports/tables/block01"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    if preview_dir is not None:
        preview_dir = Path(preview_dir)
        preview_dir.mkdir(parents=True, exist_ok=True)
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
    values, municipal, cpi, gov = load_purchase_data(root)
    national = values[values.level == "national"]
    p = series_for(national)
    first, last = int(p.index.min()), int(p.index.max())
    shared = sorted(set(p.index) & set(cpi.index))
    base, end = int(shared[0]), int(shared[-1])
    comparison = pd.DataFrame(
        {
            "purchase_valuation_index": p.loc[shared] / p.loc[base] * 100,
            "general_prices_cpi_index": cpi.loc[shared] / cpi.loc[base] * 100,
        }
    )
    comparison.index.name = "year"
    comparison.to_csv(tables / "national_comparison.csv", float_format="%.8f")
    national_levels = pd.DataFrame({"valuation_eur_m2": p, "annual_change_pct": annual_changes(p)})
    national_levels.index.name = "year"
    national_levels.to_csv(tables / "national_levels.csv", float_format="%.8f")
    summaries = {}
    for level in ["national", "region", "province"]:
        summaries[level] = history_summary(values[values.level == level], cpi, ["code", "name"])
        summaries[level].to_csv(tables / f"{level}_purchase_history.csv", index=False)
    history_summary(municipal, cpi, ["code", "name"]).to_csv(
        tables / "municipal_purchase_history.csv", index=False
    )
    mandates = pd.concat(
        [
            government_history(values[values.level == level], gov, cpi, level, "purchase_valuation")
            for level in ["national", "region"]
        ],
        ignore_index=True,
    )
    mandates = mandates[mandates.observed_complete_years > 0].copy()
    mandates.to_csv(tables / "government_history.csv", index=False)
    files = []

    def save(fig, name, title):
        fig.suptitle(title, fontsize=14, fontweight="bold", x=0.03, ha="left")
        fig.text(
            0.03,
            0.008,
            "Fuentes: MIVAU / INE · años completos · gobiernos: contexto descriptivo",
            fontsize=8,
            color="#64727d",
        )
        fig.tight_layout(rect=[0, 0.035, 1, 0.95])
        path = figures / f"{name}.png"
        fig.savefig(path, dpi=100, bbox_inches="tight")
        if vector:
            with plt.rc_context({"svg.fonttype": "none"}):
                fig.savefig(figures / f"{name}.svg", metadata={"Date": None})
        if preview_dir is not None:
            shutil.copyfile(path, preview_dir / path.name)
        plt.close(fig)
        files.append(path)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(p.index, p, color=BUY, lw=2.5)
    style(ax, f"Tasación nacional de vivienda libre, {first}–{last}", "€/m²")
    save(fig, "01_national_levels", "Precio de compra de vivienda en España desde 2000")

    fig, (ax, events_ax) = plt.subplots(
        2,
        1,
        figsize=(13, 6.5),
        sharex=True,
        gridspec_kw={"height_ratios": [4, 1.25]},
    )
    gov_bands(ax, gov, "national", "00", first, last + 1, labels=True)
    ax.plot(p.index + 0.5, p, color=BUY, lw=2.5)
    style(ax, "Presidencias nacionales, hitos y evolución de la tasación", "€/m²")
    ax.set_xticks(range(first, last + 1, 5))
    ax.tick_params(labelbottom=True)
    events_ax.set_ylim(0, 1)
    events_ax.axis("off")
    # Annual reference markers, aligned with the annual prices at year + 0.5.
    # Crisis: Banco de España, Informe sobre la crisis financiera 2008–2014.
    # Sareb: Ley 9/2012 and RD 1559/2012; deduction: Ley 16/2012.
    # Rates: ECB official interest-rate history; housing: Ley 12/2023.
    events = [
        (2008, "Inicio de la crisis\ninmobiliaria", 0.75),
        (2012, "Creación de Sareb", 0.75),
        (2013, "Fin de la deducción\npor compra de vivienda", 0.16),
        (2022, "Inicio de subidas\nde tipos del BCE", 0.75),
        (2023, "Ley por el derecho\na la vivienda", 0.16),
    ]
    for year, label, label_y in events:
        x = year + 0.5
        ax.axvline(x, color="#64727d", lw=1, ls="--", alpha=0.7, zorder=1)
        events_ax.plot([x, x], [label_y + 0.05, 1], color="#64727d", lw=0.8, zorder=1)
        events_ax.text(
            x,
            label_y,
            f"{year}\n{label}",
            ha="center",
            va="top",
            fontsize=9,
            zorder=3,
            bbox={"facecolor": "#fbfcfd", "edgecolor": "none", "pad": 2},
        )
    events_ax.text(
        0,
        -0.4,
        "Hitos: BOE · Banco de España · BCE · referencias anuales",
        transform=events_ax.transAxes,
        fontsize=8,
        color="#64727d",
    )
    save(
        fig,
        "02_national_governments",
        "Compra y gobiernos: coincidencia temporal, sin atribución causal",
    )

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(shared, comparison.purchase_valuation_index, label="Compra: tasación €/m²", color=BUY)
    ax.plot(
        shared,
        comparison.general_prices_cpi_index,
        label="Precios generales (IPC)",
        color="#7c8993",
        ls="--",
    )
    ax.axhline(100, color="#888", lw=0.7)
    style(ax, f"Mismos años y base: {base}–{end}", f"{base} = 100")
    ax.legend()
    save(fig, "03_indexed_comparison", "Compra de vivienda frente a los precios generales")

    fig, ax = plt.subplots(figsize=(12, 5))
    rates = annual_changes(p)
    ax.bar(rates.index, rates, color=[BUY if v >= 0 else "#8f9ba5" for v in rates])
    ax.axhline(0, color="#555", lw=0.8)
    style(ax, "Variación entre años consecutivos, desde 2001", "% interanual · tasación")
    save(fig, "04_annual_changes", "Subidas y caídas anuales del precio de compra")

    cycle = summaries["national"].iloc[0]
    peak, trough = int(cycle.precrisis_peak_year), int(cycle.postcrisis_trough_year)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(p.index, p, color=BUY, lw=2.5)
    for year, name in [
        (peak, "Máximo 2000–2008"),
        (trough, "Mínimo 2009–2015"),
        (last, "Último año"),
    ]:
        ax.scatter(year, p.loc[year], color=BUY)
        ax.annotate(
            f"{name}: {year}",
            (year, p.loc[year]),
            xytext=(0, 15),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
    style(ax, "Extremos dentro de ventanas explícitas", "Tasación €/m²")
    save(fig, "05_purchase_cycle", "Auge, caída y recuperación del precio de compra")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    samples = []
    for ax, category, groups in [
        (
            axes[0],
            "urban_category",
            [("large_city", "Grandes ciudades"), ("periphery", "Periferias")],
        ),
        (axes[1], "coastal_category", [("coastal", "Costa"), ("inland", "Interior")]),
    ]:
        for group, label in groups:
            wide = municipal[municipal[category] == group].pivot(
                index="year", columns="code", values="value"
            )
            start, stop = int(municipal.year.min()), int(municipal.year.max())
            wide = wide.reindex(range(start, stop + 1)).dropna(axis=1)
            if wide.shape[1]:
                index = (wide / wide.loc[start] * 100).mean(axis=1)
                ax.plot(index.index, index, label=f"{label} (n={wide.shape[1]})", lw=2)
                samples.extend(
                    dict(
                        category=category, group=group, code=code, first_year=start, last_year=stop
                    )
                    for code in wide.columns
                )
        style(
            ax, f"Muestra fija de municipios, {start}–{stop}", f"{start} = 100 · media no ponderada"
        )
        ax.legend()
    pd.DataFrame(samples).to_csv(tables / "profile_fixed_samples.csv", index=False)
    save(fig, "06_territorial_profiles", "Compra: grandes ciudades, periferias, costa e interior")

    for level, boundary_name, filename in [
        ("region", "communities.geojson", "07_regional_maps"),
        ("province", "provinces.geojson", "12_provincial_maps"),
    ]:
        boundary = json.loads((root / "data/snapshots/block01" / boundary_name).read_text())
        frame = values[values.level == level]
        current, growth = {}, {}
        for code in frame.code.unique():
            s = series_for(frame, code)
            current[code] = s.get(last, np.nan)
            growth[code] = change(s, first, last)
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        map_panel(axes[0], boundary, current, f"Tasación {last}", "€/m²")
        map_panel(axes[1], boundary, growth, f"Cambio {first}–{last}", "%", diverging=True)
        save(fig, filename, "Precio de compra: nivel y cambio en el mismo periodo")

    regions = values[(values.level == "region") & ~values.code.isin(["18", "19"])]
    wide = regions.pivot(index="year", columns="name", values="value")
    heat = wide.pct_change(fill_method=None).iloc[1:].T
    fig, ax = plt.subplots(figsize=(15, 7))
    limit = max(abs(heat.min().min()), abs(heat.max().max()))
    im = ax.imshow(heat, aspect="auto", cmap="RdBu_r", vmin=-limit, vmax=limit)
    ax.set_yticks(range(len(heat.index)), heat.index)
    ax.set_xticks(range(len(heat.columns)), heat.columns, rotation=90)
    fig.colorbar(im, ax=ax, label="Variación anual de tasación (%)")
    save(fig, "08_regional_heatmap", "Cuándo subió o bajó el precio de compra en cada comunidad")

    fig, axes = plt.subplots(6, 3, figsize=(16, 19))
    for ax, (code, data) in zip(axes.flat, regions.groupby("code"), strict=False):
        s = series_for(data, code)
        gov_bands(ax, gov, "region", code, first, last + 1)
        ax.plot(s.index + 0.5, s, color=BUY, lw=1.8)
        style(ax, data.name.iloc[0], "Tasación €/m²")
        ax.set_xticks([2000, 2005, 2010, 2015, 2020, last])
        ax.tick_params(axis="x", labelsize=7)
    axes.flat[-1].axis("off")
    parties = sorted(set(gov[gov.level == "region"].party))
    fig.legend(
        handles=[Patch(color=COLORS.get(x, "#aaa"), label=x, alpha=0.4) for x in parties],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.96),
        ncol=8,
        fontsize=7,
    )
    save(fig, "09_regional_governments_purchase", "Compra y presidencias autonómicas desde 2000")

    observed = mandates[(mandates.metric == "purchase_valuation") & (mandates.code != "00")]
    observed = observed.dropna(subset=["annualised_pct"])
    fig, ax = plt.subplots(figsize=(13, 6))
    for party, data in observed.groupby("party"):
        ax.scatter(
            (data.first_year + data.last_year) / 2,
            data.annualised_pct,
            label=party,
            color=COLORS.get(party, "#888"),
            alpha=0.8,
        )
    ax.axhline(0, color="#555", lw=0.8)
    style(
        ax,
        "Cada punto: años completos observados dentro de una presidencia",
        "Cambio anualizado de tasación (%)",
    )
    ax.set_xlabel("Año central del periodo observado · fechas exactas en la tabla")
    ax.legend(ncol=6, fontsize=8)
    save(
        fig,
        "10_mandate_comparison",
        "Cambios de compra por periodo: contexto temporal, sin ranking de partidos",
    )

    start, stop = int(municipal.year.min()), int(municipal.year.max())
    selected = municipal[municipal.year == stop].copy()
    selected["growth_pct"] = [
        change(series_for(municipal, code), start, stop) for code in selected.code
    ]
    selected[
        ["code", "name", "year", "value", "growth_pct", "urban_category", "coastal_category"]
    ].to_csv(tables / "selected_municipalities.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    boundary = json.loads((root / "data/snapshots/block01/provinces.geojson").read_text())
    for ax, col, title, unit in [
        (axes[0], "value", f"Tasación {stop}", "€/m²"),
        (axes[1], "growth_pct", f"Cambio {start}–{stop}", "%"),
    ]:
        for feature in boundary["features"]:
            geom = feature["geometry"]
            polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            for polygon in polys:
                pts = np.asarray(polygon[0])
                if pts[:, 0].mean() < -12:
                    pts = pts + [8.5, 8.2]
                ax.add_patch(Polygon(pts, facecolor="#eee", edgecolor="white", linewidth=0.4))
        coords = selected[["lng", "lat"]].to_numpy().copy()
        coords[coords[:, 0] < -12] += [8.5, 8.2]
        plot = ax.scatter(
            coords[:, 0], coords[:, 1], c=selected[col], cmap="YlOrRd", s=55, edgecolor="#333"
        )
        ax.set(xlim=(-10, 4.5), ylim=(35, 44.2), title=title)
        ax.set_aspect(1 / np.cos(np.deg2rad(40)))
        ax.set_axis_off()
        ax.text(
            0.01,
            0.01,
            "Canarias reubicadas · solo 30 municipios seleccionados",
            transform=ax.transAxes,
            fontsize=7,
        )
        fig.colorbar(plot, ax=ax, shrink=0.7, label=unit)
    save(
        fig,
        "13_municipal_maps",
        "Compra en 30 municipios: selección de casos, no mapa nacional exhaustivo",
    )

    cases = ["Barcelona", "Madrid", "València", "Málaga", "Badalona", "L'Hospitalet de Llobregat"]
    names = [name for name in cases if name in set(municipal.name)]
    names += [name for name in municipal.name.unique() if name not in names][: 6 - len(names)]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex=True, sharey=True)
    case_values = municipal[municipal.name.isin(names)]
    price_step = 2000
    price_ceiling = np.ceil(case_values.value.max() / price_step) * price_step
    for ax, name in zip(axes.flat, names, strict=True):
        data = municipal[municipal.name == name].sort_values("year")
        ax.plot(data.year, data.value, color=BUY, lw=2)
        style(ax, name, "Tasación €/m²")
        ax.set_xlim(start, stop)
        ax.set_ylim(0, price_ceiling)
        ax.set_xticks(range(start, stop + 1, 5))
        ax.set_yticks(np.arange(0, price_ceiling + price_step, price_step))
        ax.tick_params(labelbottom=True, labelleft=True)
    save(fig, "15_municipal_cases", f"Casos municipales de compra, {start}–{stop}")

    findings = {
        "scope": "purchase_only",
        "main_measure": "free_housing_valuation_eur_m2",
        "national_window": [first, last],
        "cpi_comparison_window": [base, end],
        "municipal_window": [start, stop],
        "national_first_eur_m2": float(p.loc[first]),
        "national_last_eur_m2": float(p.loc[last]),
        "purchase_nominal_pct": change(p, first, last),
        "purchase_cpi_window_pct": change(p, base, end),
        "general_prices_pct": change(cpi, base, end),
        "purchase_real_pct": change(real_series(p, cpi, end).dropna(), base, end),
        "cycle": cycle.to_dict(),
        "figure_count": len(files),
    }
    (tables / "findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2))
    report = f"""# Bloque 1 · Precio de compra de vivienda en España

## Alcance y medida principal

Analizamos la **tasación media de vivienda libre en €/m²**, desde **{first} hasta {last}**.
Es una medida de valoración, no el precio anunciado ni el precio efectivo de cada compraventa.
Todas las figuras de este bloque usan esta misma medida. Los importes por vivienda y el IPV
se conservan como fuentes originales, pero no se mezclan con la tasación.
Se utilizan medias de años completos; los trimestres de 2026 quedan fuera.

## 1. Evolución nacional desde 2000

La tasación pasó de **{p.loc[first]:.2f} €/m²** en {first} a **{p.loc[last]:.2f} €/m²** en {last}:
un cambio acumulado del **{findings["purchase_nominal_pct"]:+.2f}%**.

![Evolución nacional](figures/block01/01_national_levels.png)
![Cambios anuales](figures/block01/04_annual_changes.png)
![Ciclo de compra](figures/block01/05_purchase_cycle.png)

El máximo dentro de 2000–2008 corresponde a **{peak}** y el mínimo dentro de 2009–2015 a
**{trough}**. La caída entre ambos fue del **{cycle.peak_to_trough_pct:.2f}%** y la variación
desde el mínimo hasta {last}, del **{cycle.trough_to_latest_pct:+.2f}%**.
Elegir el inicio o el final de un ciclo cambia la lectura del crecimiento acumulado.

## 2. Compra frente a los precios generales

![Comparación con precios generales](figures/block01/03_indexed_comparison.png)

Comparamos cuánto ha subido el precio de compra respecto a los precios generales, medidos
por el IPC. La ventana común es **{base}–{end}**, con **{base} = 100**: un valor de 120
representa una subida acumulada del 20 %, no un precio en euros.
La tasación aumentó **{findings["purchase_cpi_window_pct"]:+.2f}%** y los precios generales,
**{findings["general_prices_pct"]:+.2f}%**. El IPC disponible empieza en 2002.
El IPC no indica si los ingresos han crecido al mismo ritmo: esta comparación no mide
la accesibilidad económica de comprar una vivienda.

## 3. Comunidades y provincias

![Comunidades](figures/block01/07_regional_maps.png)
![Cambios anuales por comunidad](figures/block01/08_regional_heatmap.png)
![Provincias](figures/block01/12_provincial_maps.png)

Los mapas muestran el nivel de {last} y el cambio con extremos fijos **{first}–{last}**.
Las tablas incluyen cobertura, años ausentes y extremos del ciclo de cada territorio.
El gris representa falta de datos; Canarias se reubica por legibilidad. Los contornos
son ilustrativos y conservan la atribución de las geometrías originales.

## 4. Municipios y perfiles territoriales

![Perfiles](figures/block01/06_territorial_profiles.png)
![Municipios](figures/block01/13_municipal_maps.png)
![Casos municipales](figures/block01/15_municipal_cases.png)

Los datos municipales empiezan en **{start}** y llegan hasta **{stop}**. La selección
contiene 30 municipios y no representa todos los municipios de España. Los perfiles
comparan muestras fijas con todos los años observados: media no ponderada de índices
locales, base {start} = 100. La composición está en `profile_fixed_samples.csv`.

## 5. Gobiernos como contexto temporal

![Gobiernos nacionales](figures/block01/02_national_governments.png)
![Presidencias autonómicas](figures/block01/09_regional_governments_purchase.png)
![Periodos observados](figures/block01/10_mandate_comparison.png)

Las franjas identifican presidencias nacionales y el partido de la presidencia autonómica,
no todos los socios del gabinete. Los puntos de precio se sitúan a mitad de año porque
representan medias anuales. La tabla de mandatos utiliza solo años completos dentro
de cada presidencia, excluye años de transición y muestra fechas, cobertura y tasas
anualizadas. Los periodos sin dos años observados no tienen tasa de cambio.
El gráfico de mandatos sitúa cada periodo por su año central, para que el contexto
temporal sea visible. No clasifica partidos ni atribuye los cambios a sus políticas.

## Fuentes y reproducción

- [Notebook principal con código y resultados](../notebooks/01_prices.ipynb).
- [Notebook de cobertura y mandatos](../notebooks/01b_price_history.ipynb).
- [Tablas descargables](tables/block01/).
- [Código del análisis](../src/spain_housing/prices_analysis.py).
- [Fuentes y huellas SHA-256](../data/snapshots/block01/source_manifest.json).

Ejecutar `python scripts/run_block01.py`. No necesita descargar datos.
"""
    (root / "reports/block_01_prices.md").write_text(report, encoding="utf-8")
    (root / "reports/block_01_price_history.md").write_text(
        "# Bloque 1 · Historia del precio de compra desde 2000\n\n"
        "El histórico forma parte del [informe completo de compra](block_01_prices.md).\n\n"
        "Serie principal: tasación de vivienda libre en €/m², 2000–2025. "
        "Comparación con IPC: 2002–2025. Municipios seleccionados: 2005–2025.\n\n"
        "[Notebook de cobertura, ciclos y mandatos](../notebooks/01b_price_history.ipynb).\n",
        encoding="utf-8",
    )
    return files, findings
