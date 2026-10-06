"""Recover the earliest verified sources; retain the 2002 IPC break and BIS coverage."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/history1950"
OUT = ROOT / "data/snapshots/history1950"
URLS = {
    "ine_196.csv": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/196.csv",
    "ine_203.csv": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/203.csv",
    "ine_268.csv": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/268.csv",
    "ine_24079.csv": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/24079.csv",
    "ine_24077.csv": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/24077.csv",
    "bis_nominal.csv": "https://stats.bis.org/api/v1/data/BIS,WS_SPP,1.0/Q.ES.N.628?format=csv",
    "bis_real.csv": "https://stats.bis.org/api/v1/data/BIS,WS_SPP,1.0/Q.ES.R.628?format=csv",
    "bis_method.pdf": "https://www.bis.org/statistics/pp_selected_documentation.pdf",
    "ine_linking.html": "https://www.ine.es/ipc01/enlaces.htm",
}


def annual_months(frame, source_id, metric, segment, base):
    """Twelve observed monthly indices, with a documented source and original base."""
    data = frame[frame["Tipo de dato"] == "Índice"].copy()
    data["value"] = pd.to_numeric(data.Total.str.replace(",", ".", regex=False), errors="coerce")
    data["year"] = data.Periodo.str[:4].astype(int)
    if data.Periodo.duplicated().any():
        raise ValueError("Select one monthly series before aggregation")
    annual = data.groupby("year").agg(value=("value", "mean"), months=("value", "count"))
    annual = annual[(annual.months == 12) & annual.index.to_series().between(1950, 2025)]
    annual = annual.drop(columns="months").reset_index()
    annual["metric"], annual["segment"], annual["base"], annual["source_id"] = (
        metric,
        segment,
        base,
        source_id,
    )
    return annual


def build():
    RAW.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, url in URLS.items():
        if not (RAW / name).exists():
            with urlopen(
                Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=45
            ) as response:
                (RAW / name).write_bytes(response.read())
    annual = []
    for file, metric, segment, base in [
        ("ine_196.csv", "rent_cpi", "1961_2001", "1992=100"),
        ("ine_268.csv", "cpi_general", "1961_2001", "1992=100"),
        ("ine_24079.csv", "rent_cpi", "2002_2025", "2025=100"),
        ("ine_24077.csv", "cpi_general", "2002_2025", "2025=100"),
    ]:
        data = pd.read_csv(RAW / file, sep=";", dtype=str)
        annual.append(annual_months(data, file, metric, segment, base))
    annual = pd.concat(annual, ignore_index=True)
    annual.to_csv(OUT / "rental_cpi_segments.csv", index=False, float_format="%.8f")
    published = pd.read_csv(RAW / "ine_203.csv", sep=";", dtype=str)
    published = published[published["Tipo de dato"] == "Media anual"]
    published = published.assign(
        year=published.Periodo.astype(int),
        value=published.Total.str.replace(",", ".", regex=False).astype(float),
    )
    check = published.merge(
        annual[annual.metric.eq("rent_cpi") & annual.segment.eq("1961_2001")],
        on="year",
        suffixes=("_published", "_computed"),
    )
    if (check.value_published - check.value_computed).abs().max() > 0.001:
        raise ValueError("Historical rental monthly averages differ from INE annual release")
    bis = []
    for file, metric in [
        ("bis_nominal.csv", "purchase_nominal"),
        ("bis_real.csv", "purchase_real"),
    ]:
        d = pd.read_csv(RAW / file, dtype=str)
        if not (d.REF_AREA.eq("ES") & d.FREQ.eq("Q") & d.UNIT_MEASURE.eq("628")).all():
            raise ValueError("Unexpected BIS series")
        if d.TIME_PERIOD.duplicated().any():
            raise ValueError("Duplicate BIS quarters")
        d["year"] = d.TIME_PERIOD.str[:4].astype(int)
        d["value"] = pd.to_numeric(d.OBS_VALUE, errors="coerce")
        a = d.groupby("year").agg(value=("value", "mean"), quarters=("value", "count"))
        a = a[(a.quarters == 4) & (a.index <= 2025)].drop(columns="quarters").reset_index()
        a["metric"], a["base"], a["source_id"] = metric, "2010=100", file
        a["coverage"] = a.year.map(
            lambda y: (
                "OECD_historical"
                if y < 1975
                else "Madrid_area_proxy"
                if y < 1987
                else "national_per_m2"
                if y < 2007
                else "national_pure_price"
            )
        )
        bis.append(a)
    pd.concat(bis, ignore_index=True).to_csv(
        OUT / "purchase_bis.csv", index=False, float_format="%.8f"
    )
    manifest = []
    for name, url in URLS.items():
        file = RAW / name
        manifest.append(
            dict(
                source_file=name,
                url=url,
                bytes=file.stat().st_size,
                sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                retrieved_at_utc=datetime.fromtimestamp(
                    file.stat().st_mtime, timezone.utc
                ).isoformat(),
            )
        )
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    # Native indices are deliberately not spliced across 2001/2002 without a verified bridge.
    print("Built actual purchase 1971–2025 and rent/CPI 1961–2001 + 2002–2025 snapshots.")


if __name__ == "__main__":
    build()
