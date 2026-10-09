"""Published demographic figures: one entry point for scripts and notebooks."""

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .demographics import population_dwelling_use_figure
from .household_analysis import (
    dwelling_household_totals_figure,
    single_person_history,
    single_person_history_figures,
)
from .immigration_provenance import global_top15_provenance_figure, load_immigration_provenance
from .migration_background import load_migration_background, migration_background_figure


def ratios_table_figure(panel, root):
    ratios = pd.DataFrame(
        {
            "viviendas_por_1000_habitantes": panel.dwellings / panel.population * 1000,
            "viviendas_por_1000_adultos": panel.dwellings / panel.adults * 1000,
        }
    )
    # Tabla en imagen: valores absolutos de las ratios, sin redondeos intermedios.
    selected = ratios.loc[[2001, 2005, 2010, 2015, 2020, 2025]]
    fig = plt.figure(figsize=(10, 2.3 + 0.48 * len(selected)))
    ax = fig.add_axes([0.05, 0.22, 0.9, 0.62])
    fig.patch.set_facecolor("#ffffff")
    ax.axis("off")
    rows = [
        [str(year), *[f"{v:.2f}".replace(".", ",") for v in row]]
        for year, row in selected.iterrows()
    ]
    table = ax.table(
        cellText=rows,
        colLabels=["Año", "Viviendas por\n1.000 habitantes", "Viviendas por\n1.000 adultos (18+)"],
        cellLoc="center",
        colWidths=[0.18, 0.41, 0.41],
        bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#d0d0d0")
        cell.PAD = 0.08
        cell.set_text_props(va="center", ha="center", color="#252525")
        if row == 0:
            cell.set_facecolor("#dedede")
            cell.set_height(cell.get_height() * 1.65)
            cell.set_text_props(color="#252525", weight="bold", fontsize=12, linespacing=1.35)
        else:
            cell.set_facecolor("#f2f2f2" if row % 2 else "white")
            if col == 0:
                cell.set_text_props(weight="bold")
    fig.suptitle(
        "Viviendas por habitante y por adulto en España", fontsize=16, fontweight="bold", y=0.95
    )
    fig.text(
        0.05,
        0.06,
        "Fuentes: INE y MIVAU. Parque total de viviendas; datos al cierre del año.\n"
        "Población de 2025 provisional. Incluye viviendas ocupadas, secundarias y vacías.",
        fontsize=9,
        color="#555555",
    )
    image_path = root / "reports/figures/block02/02_ratios_table.png"
    fig.savefig(image_path, dpi=180, facecolor=fig.get_facecolor())
    return fig


def publish_demographics(root, panels):
    root = Path(root)
    panel = panels[0]
    directory = root / "reports/figures/block02"
    names = []

    def save(name, fig):
        fig.savefig(directory / f"{name}.png", dpi=150)
        plt.close(fig)
        names.append(name)

    save("11_population_dwelling_use", population_dwelling_use_figure(panel, root))
    save("02_ratios_table", ratios_table_figure(panel, root))
    migration = load_migration_background(root)
    migration.to_csv(root / "reports/tables/block02/migration_background.csv")
    save("07_migration_background", migration_background_figure(migration))
    history = single_person_history(root)
    for name, fig in zip(
        ["08_single_person_households", "09_single_person_households_share"],
        single_person_history_figures(history),
        strict=True,
    ):
        save(name, fig)
    save("10_dwellings_households_totals", dwelling_household_totals_figure(panel, root))
    save(
        "12_immigration_provenance",
        global_top15_provenance_figure(load_immigration_provenance(root), root),
    )
    notebook = json.loads((root / "notebooks/02_demographics.ipynb").read_text(encoding="utf-8"))
    report = []
    for cell in notebook["cells"]:
        source = "".join(cell["source"])
        if cell["cell_type"] == "markdown":
            report.append(source)
        elif source.startswith("show("):
            for name in re.findall(r"['\"]([^'\"]+)['\"]", source):
                report.append(f"![{name}](figures/block02/{name}.png)")
    (root / "reports/block_02_demographics.md").write_text(
        "\n\n".join(report) + "\n", encoding="utf-8"
    )
    return names
