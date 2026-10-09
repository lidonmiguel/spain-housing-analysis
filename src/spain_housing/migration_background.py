"""Frozen INE migration-background estimates, independent of citizenship."""
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MaxNLocator


def load_migration_background(root):
    """INE ECH: all ages. Derive both-foreign-parent group from published margins."""
    import re
    folder = Path(root) / "data/snapshots/block02"
    meta = json.loads((folder / "migration_background_ine_source.json").read_text(encoding="utf-8"))
    def read_px(name):
        item = next(x for x in meta["sources"] if x["filename"] == name + ".px")
        raw = (folder / item["filename"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("INE migration snapshot checksum mismatch")
        text = raw.decode("cp850")
        dims = []
        for keyword in ["STUB", "HEADING"]:
            dims += re.findall(r'"([^"]+)"', re.search(keyword + r'=(.*?);', text, re.S).group(1))
        labels = {d: re.findall(r'"([^"]+)"', re.search(
            r'VALUES\("' + re.escape(d) + r'"\)=(.*?);', text, re.S).group(1)) for d in dims}
        tokens = re.findall(r'"\.\."|[-+]?\d+(?:\.\d+)?', text.split("DATA=", 1)[1])
        values = np.array([float(t) if t != '".."' else np.nan for t in tokens])
        return values.reshape([len(labels[d]) for d in dims]), labels
    population, labels = read_px("migration_background_ine")
    children, child_labels = read_px("migration_children_ine")
    years = list(labels["periodo"])
    if years != child_labels["periodo"]:
        raise ValueError("INE tables have different reference years")
    # Native-born children table contains only people with at least one foreign-born
    # parent. Spain/unknown margins are disjoint here; subtract them from that total.
    all_children = children[:, 0, 0, 0, 0]
    mother_spain = children[:, 1, 0, 0, 0]
    father_spain = children[:, 0, 1, 0, 0]
    mother_unknown = children[:, -1, 0, 0, 0]
    father_unknown = children[:, 0, -1, 0, 0]
    both_abroad = all_children - mother_spain - father_spain - mother_unknown - father_unknown
    total = population[:, 0, 0, 0]
    abroad = population[:, 0, 2, 0]
    native = population[:, 0, 1, 0]
    known_rest = population[:, 1, 1, 0] + population[:, 0, 1, 1] - population[:, 1, 1, 1]
    result = pd.DataFrame({
        "total": total, "born_abroad": abroad,
        "born_spain_both_parents_abroad": both_abroad,
        "migration_background": abroad + both_abroad,
        "rest": total - abroad - both_abroad,
        "native_at_least_one_parent_spain": known_rest,
        "unclassified_parent_origin": native - both_abroad - known_rest,
    }, index=[int(y) for y in years]).mul(1000).sort_index()
    if result.isna().any().any() or (result < -300).any().any():
        raise ValueError("Missing or inconsistent INE migration aggregates")
    result.index.name = "year"
    # Never replace missing detailed cells with zero; use published total margins.
    return result


def migration_background_figure(data):
    fig, ax = plt.subplots(figsize=(12, 6.5))
    fig.patch.set_facecolor("#faf9f6")
    ax.set_facecolor("#faf9f6")
    for column, label, color in [
        ("total", "Población total", "#24688d"),
        ("rest", "Resto de la población", "#258477"),
        ("migration_background", "Población de origen inmigrante", "#79539b"),
    ]:
        ax.plot(data.index, data[column], label=label, color=color, lw=2.5, marker="o")
        for year, value in data[column].items():
            ax.annotate(f"{value:,.0f}".replace(",", "."), (year, value),
                        xytext=(0, 10), textcoords="offset points", ha="center",
                        color=color, fontsize=9)
    ax.set(title="Población por origen migratorio en España", xlabel="Año",
           ylabel="Personas", ylim=(0, data.total.max() * 1.13))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", ".")))
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, loc="center left")
    fig.text(0.07, 0.025,
             'INE · Encuesta Continua de Hogares · 2014–2020 · Todas las edades, '
             'viviendas familiares; referencia: 1 de enero.\n'
             'Origen inmigrante: nacidos fuera + nacidos aquí con ambos padres '
             'nacidos fuera; incluye nacionalizados.\n'
             'Resto = total menos origen inmigrante identificado; incluye casos sin '
             'datos suficientes de los padres. Estimaciones redondeadas.',
             fontsize=8.5, color="#555555")
    fig.tight_layout(rect=(0.02, 0.15, 0.98, 1))
    return fig
