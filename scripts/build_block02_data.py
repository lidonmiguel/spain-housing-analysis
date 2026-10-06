"""Download official releases and freeze exact CSV bytes for offline analysis."""

import argparse
import gzip
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
INE = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/"
MIVAU = "https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/"
SOURCES = {
    "population": ("population.csv", INE + "56934.csv", "personas", "definitivo"),
    "population_provisional": ("59583.csv", INE + "59583.csv", "personas", "provisional"),
    "birthplace": ("79276.csv", INE + "79276.csv", "personas", "definitivo"),
    "birthplace_provisional": ("79273.csv", INE + "79273.csv", "personas", "provisional"),
    "households": ("60135.csv", INE + "60135.csv", "hogares", "ECP, puede revisarse"),
    "households_regions": ("60131.csv", INE + "60131.csv", "hogares", "ECP, puede revisarse"),
    "stock": ("stock.csv", MIVAU + "CSV/VDP002_01.csv", "viviendas", "estimación"),
    "construction": ("construction.csv", MIVAU + "CSV/VDP005_01.csv", "viviendas", "estimación"),
    "natural": ("1416.csv", INE + "1416.csv", "personas por 1.000 habitantes", "IDB"),
    "migration_old": ("5227.csv", INE + "5227.csv", "personas por 1.000 habitantes", "2008–2020"),
    "migration_new": (
        "61769.csv",
        INE + "61769.csv",
        "personas por 1.000 habitantes",
        "desde 2021",
    ),
    "growth": ("5224.csv", INE + "5224.csv", "personas por 1.000 habitantes", "IDB"),
}


def build(refresh=False):
    raw = ROOT / "data/raw/block02"
    snapshot = ROOT / "data/snapshots/block02"
    raw.mkdir(parents=True, exist_ok=True)
    snapshot.mkdir(parents=True, exist_ok=True)

    def fetch(item):
        name, (filename, url, units, release) = item
        path = raw / filename
        if refresh or not path.exists():
            data = urlopen(url, timeout=60).read()
            if b";" not in data[:500] or b"<html" in data[:500].lower():
                raise ValueError(f"Expected a source CSV: {url}")
            path.write_bytes(data)
        data = path.read_bytes()
        packed = gzip.compress(data, mtime=0)
        out = snapshot / (name + ".csv.gz")
        out.write_bytes(packed)
        return {
            "name": name,
            "url": url,
            "units": units,
            "release": release,
            "retrieved_at_utc": datetime.fromtimestamp(
                path.stat().st_mtime, timezone.utc
            ).isoformat(),
            "raw_sha256": hashlib.sha256(data).hexdigest(),
            "snapshot_sha256": hashlib.sha256(packed).hexdigest(),
            "snapshot_path": str(out.relative_to(ROOT)),
            "license_url": (
                "https://www.ine.es/aviso_legal"
                if "ine.es" in url
                else "https://creativecommons.org/licenses/by/4.0/"
            ),
        }

    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, SOURCES.items()))
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": records,
        "price_source": (
            "data/snapshots/block01/valuations.csv; same annual MIVAU series as notebook 1"
        ),
        "price_snapshot_sha256": hashlib.sha256(
            (ROOT / "data/snapshots/block01/valuations.csv").read_bytes()
        ).hexdigest(),
        "methodology_urls": [
            MIVAU + "Info/Readme_VDP002_01.pdf",
            MIVAU + "Info/Readme_VDP005_01.pdf",
            "https://www.ine.es/metodologia/metodologia_idb.pdf",
        ],
    }
    (snapshot / "source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Frozen {len(records)} official inputs in {snapshot.relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Download new releases explicitly")
    build(parser.parse_args().refresh)
