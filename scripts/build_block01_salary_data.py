"""Snapshot de salario medio bruto anual (INE EAES, tabla 28185).

Ejecutar desde cualquier directorio. Reutiliza el CSV original si ya existe;
--refresh descarga de nuevo la fuente y actualiza la trazabilidad.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/28185.csv"


def normalize_salary(raw_path):
    frame = pd.read_csv(raw_path, sep=";", encoding="utf-8-sig", dtype=str)
    selected = frame.loc[
        frame["Secciones de la CNAE 2009"].eq("B_S Todas las secciones")
        & frame["Sexo"].eq("Ambos sexos")
    ]
    result = pd.DataFrame({
        "year": pd.to_numeric(selected["Periodo"], errors="raise"),
        "gross_annual_eur": pd.to_numeric(
            selected["Total"].str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False), errors="raise"
        ),
    }).sort_values("year").reset_index(drop=True)
    if result.empty or result.year.duplicated().any() or result.isna().any().any():
        raise ValueError("La serie salarial está vacía, tiene duplicados o valores ausentes")
    if not result.gross_annual_eur.gt(0).all():
        raise ValueError("El salario debe ser positivo")
    if result.year.tolist() != list(range(result.year.min(), result.year.max() + 1)):
        raise ValueError("La serie salarial contiene años ausentes")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    raw = ROOT / "data/raw/block01/ine_eaes_28185.csv"
    provenance = ROOT / "data/snapshots/block01/salary_source.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    provenance.parent.mkdir(parents=True, exist_ok=True)
    if args.refresh or not raw.exists():
        with urlopen(URL, timeout=60) as response:
            raw.write_bytes(response.read())
        retrieved = datetime.now(timezone.utc).isoformat()
    elif provenance.exists():
        retrieved = json.loads(provenance.read_text())["retrieved_at_utc"]
    else:
        retrieved = datetime.fromtimestamp(raw.stat().st_mtime, timezone.utc).isoformat()
    salary = normalize_salary(raw)
    salary.to_csv(provenance.with_name("salary.csv"), index=False, float_format="%.2f")
    provenance.write_text(json.dumps({
        "dataset_url": URL,
        "table_url": "https://www.ine.es/jaxiT3/Tabla.htm?t=28185",
        "retrieved_at_utc": retrieved,
        "sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
        "selection": {"Secciones de la CNAE 2009": "B_S Todas las secciones",
                      "Sexo": "Ambos sexos"},
        "unit": "EUR brutos por trabajador y año",
        "coverage": "Asalariados cubiertos por EAES; secciones B–S; España",
        "period_start": int(salary.year.min()),
        "period_end": int(salary.year.max()),
        "notes": "Media, no mediana; todas las nacionalidades; no renta por habitante",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Salario anual: {salary.year.min()}–{salary.year.max()}, {len(salary)} años")


if __name__ == "__main__":
    main()
