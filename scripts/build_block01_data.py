"""Build audited block-01 snapshots from primary-source releases (no synthetic data)."""

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import pandas as pd
from fetch_block01_context import fetch_cities, fetch_governments
from shapely.geometry import mapping, shape

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/block01"
OUT = ROOT / "data/snapshots/block01"
OUT.mkdir(parents=True, exist_ok=True)
URLS = {
    "valuations.csv": "https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP006_01.csv",
    "rent.xlsx": "https://cdn.mivau.gob.es/portal-web-mivau/vivienda/serpavi/2026-03_09_bd_SERPAVI_2011-2024%20-%20DEFINITIVO%20WEB_v2.xlsx",
    "ipv_quarterly.csv": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/79563.csv",
    "ine_59056.csv": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/59056.csv",
    "ipva.csv": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/59004.csv",
    "cpi.csv": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/50913.csv",
    "municipal_purchase.xls": "https://apps.fomento.gob.es/BoletinOnline2/sedal/35103500.XLS",
    "purchase_total.xls": "https://apps.fomento.gob.es/BoletinOnline2/sedal/34020170.XLS",
}
REGIONS = {
    "01": "Andalucía",
    "02": "Aragón",
    "03": "Asturias",
    "04": "Illes Balears",
    "05": "Canarias",
    "06": "Cantabria",
    "07": "Castilla y León",
    "08": "Castilla-La Mancha",
    "09": "Cataluña",
    "10": "Comunitat Valenciana",
    "11": "Extremadura",
    "12": "Galicia",
    "13": "Comunidad de Madrid",
    "14": "Región de Murcia",
    "15": "Navarra",
    "16": "País Vasco",
    "17": "La Rioja",
    "18": "Ceuta",
    "19": "Melilla",
    "00": "España",
}


def normalise(value):
    value = unicodedata.normalize("NFKD", str(value).lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in value if not unicodedata.combining(c)))


def numbers(series):
    return pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def annual_complete(frame, keys, value="value"):
    """Arithmetic mean of four observed quarters; never annualise partial years."""
    result = (
        frame.groupby(keys, dropna=False)
        .agg(value=(value, "mean"), quarters=(value, "count"))
        .reset_index()
    )
    return result.loc[result.quarters == 4].drop(columns="quarters")


def write(frame, name):
    frame.to_csv(OUT / name, index=False, float_format="%.8f")


def build():
    RAW.mkdir(parents=True, exist_ok=True)
    fetch_governments()
    fetch_cities()
    for name in ["communities.geojson", "provinces.geojson"]:
        target = RAW / name
        if not target.exists():
            url = (
                "https://raw.githubusercontent.com/codeforgermany/click_that_hood/"
                f"main/public/data/spain-{name}"
            )
            with urlopen(url, timeout=120) as response:
                target.write_bytes(response.read())
    for name, url in URLS.items():
        if not (RAW / name).exists():
            with urlopen(url, timeout=120) as response:
                (RAW / name).write_bytes(response.read())
        if (RAW / name).stat().st_size == 0:
            raise ValueError(f"Empty primary source: {name}")

    # INE transaction price index, rebased by INE to 2025; preserve source definition.
    data = pd.read_csv(RAW / "ipv_quarterly.csv", sep=";", dtype=str)
    data = data[
        (data["General, vivienda nueva y de segunda mano"] == "General")
        & (data["Índices y tasas"] == "Índice")
    ].copy()
    data["code"] = data["Comunidades y Ciudades Autónomas"].str[:2].fillna("00")
    data["year"] = data.Periodo.str[:4].astype(int)
    data["value"] = numbers(data.Total)
    prices = annual_complete(data, ["code", "year"])
    prices["name"] = prices.code.map(REGIONS)
    write(prices, "purchase_index.csv")

    data = pd.read_csv(RAW / "ipva.csv", sep=";", dtype=str)
    data = data[data["Tipo de dato"] == "Índice"].copy()
    data["code"] = data["Comunidades y Ciudades Autónomas"].str[:2].fillna("00")
    data["year"] = data.Periodo.astype(int)
    data["value"] = numbers(data.Total)
    data = data.rename(columns={"Antigüedad del contrato de arrendamiento": "contract"})
    data["name"] = data.code.map(REGIONS)
    write(data[["code", "name", "year", "contract", "value"]], "rent_index.csv")

    # Long general IPVA; do not fabricate older contract-specific observations.
    history = pd.read_csv(RAW / "ine_59056.csv", sep=";", dtype=str)
    history = history[
        (history["Tipo de dato"] == "Índice") & (history["Tipo de edificación"] == "Total")
    ].copy()
    history["code"] = history["Comunidades y Ciudades Autónomas"].str[:2].fillna("00")
    history["year"] = history.Periodo.astype(int)
    history["value"] = numbers(history.Total)
    history["name"] = history.code.map(REGIONS)
    write(
        history[["code", "name", "year", "value"]].dropna(subset=["value"]),
        "rent_general_history.csv",
    )

    data = pd.read_csv(RAW / "cpi.csv", sep=";", dtype=str)
    data = data[
        (data["Grupos ECOICOP"] == "Índice general") & (data["Tipo de dato"] == "Índice")
    ].copy()
    data["code"] = data["Comunidades y Ciudades Autónomas"].str[:2]
    data.loc[data["Comunidades y Ciudades Autónomas"] == "Nacional", "code"] = "00"
    data["year"] = data.Periodo.str[:4].astype(int)
    data["value"] = numbers(data.Total)
    cpi = data.groupby(["code", "year"]).agg(value=("value", "mean"), months=("value", "count"))
    cpi = cpi[cpi.months == 12].drop(columns="months").reset_index()
    write(cpi, "cpi.csv")

    data = pd.read_csv(RAW / "valuations.csv", sep=";", dtype={"CPRO": str, "CODAUTO": str})
    data = data[data["Régimen"] == "Libre"].drop_duplicates().copy()
    data["value"] = pd.to_numeric(data.Valor, errors="coerce")
    data["year"] = data["Año"].astype(int)
    data["level"] = "province"
    data.loc[data.Provincia == "Total CCAA", "level"] = "region"
    data.loc[data.Comunidad_Autónoma == "Total nacional", "level"] = "national"
    data["code"] = data.CPRO.str.zfill(2)
    regional = data.level.isin(["region", "national"])
    data.loc[regional, "code"] = data.loc[regional, "CODAUTO"].str.zfill(2)
    data.loc[data.level == "national", "code"] = "00"
    data.loc[data.Comunidad_Autónoma == "Murcia, Region de", "code"] = "14"
    data["name"] = data.Provincia
    data.loc[regional, "name"] = data.loc[regional, "code"].map(REGIONS)
    data = data.dropna(subset=["code", "name"])
    if data.duplicated(["level", "code", "year", "Trimestre"]).any():
        raise ValueError("Conflicting quarterly valuations after exact duplicate removal")
    values = annual_complete(data, ["level", "code", "name", "year"])
    # Some single-province communities appear only once in the ministerial source.
    # Reuse identical territories, not estimates; label the provenance explicitly.
    values["territory_reuse"] = False
    for region, province in {
        "04": "07",
        "06": "39",
        "17": "26",
        "18": "51",
        "19": "52",
    }.items():
        if values.query('level == "region" and code == @region').empty:
            rows = values.query('level == "province" and code == @province').copy()
            rows["level"], rows["code"], rows["name"], rows["territory_reuse"] = (
                "region",
                region,
                REGIONS[region],
                True,
            )
            values = pd.concat([values, rows], ignore_index=True)
    for region, province in {"03": "33", "13": "28", "14": "30", "15": "31"}.items():
        if values.query('level == "province" and code == @province').empty:
            rows = values.query('level == "region" and code == @region').copy()
            rows["level"], rows["code"], rows["territory_reuse"] = "province", province, True
            values = pd.concat([values, rows], ignore_index=True)
    write(values, "valuations.csv")

    # SERPAVI medians: collective dwellings (VC), not asking prices or all dwelling types.
    book = pd.ExcelFile(RAW / "rent.xlsx")
    rentals = []
    for sheet, level, code_col, name_col in [
        ("CCAA", "region", "CCAA", "LITCCAA"),
        ("Provincias", "province", "CPRO", "LITPRO"),
        ("Municipios", "municipality", "CUMUN", "NMUN"),
    ]:
        frame = pd.read_excel(book, sheet)
        frame = frame[frame[code_col].notna()].copy()
        codes = (
            frame[code_col].astype(int).astype(str).str.zfill(5 if level == "municipality" else 2)
        )
        for year in range(2011, 2025):
            yy = str(year)[-2:]
            for field, unit in [
                ("ALQM2_LV_M_VC_", "EUR/m2/month"),
                ("ALQTBID12_M_VC_", "EUR/dwelling/month"),
            ]:
                rental = pd.DataFrame(
                    {
                        "level": level,
                        "code": codes,
                        "name": frame[name_col],
                        "year": year,
                        "unit": unit,
                        "value": pd.to_numeric(frame[field + yy], errors="coerce"),
                        "dwellings": pd.to_numeric(frame["BI_ALVHEPCO_TVC_" + yy], errors="coerce"),
                    }
                )
                rentals.append(rental)
    rentals = pd.concat(rentals, ignore_index=True).dropna(subset=["value"])
    rentals = rentals[rentals.value > 0]
    write(rentals[rentals.year <= 2017], "rental_medians_2011_2017.csv.gz")
    write(rentals[rentals.year >= 2018], "rental_medians_2018_2024.csv.gz")

    # Nominal transaction EUR/dwelling (free-market second-hand only).
    book = pd.ExcelFile(RAW / "purchase_total.xls")
    totals = []
    for sheet in book.sheet_names:
        frame = pd.read_excel(book, sheet, header=None)
        headings = next(
            i for i in range(20) if frame.iloc[i].astype(str).str.contains("Año 20").any()
        )
        for col in range(2, frame.shape[1]):
            heading = frame.iloc[headings, col]
            if not isinstance(heading, str) or not re.search(r"Año (\d{4})", heading):
                continue
            year = int(re.search(r"Año (\d{4})", heading)[1])
            for _, row in frame.iloc[headings + 3 :].iterrows():
                if normalise(row.iloc[1]) != "totalnacional":
                    continue
                for q in range(4):
                    if col + q < len(row):
                        value = pd.to_numeric(row.iloc[col + q], errors="coerce")
                        if pd.notna(value):
                            totals.append({"year": year, "quarter": q + 1, "value": value})
    total = pd.DataFrame(totals).drop_duplicates(["year", "quarter"], keep="last")
    write(total.sort_values(["year", "quarter"]), "purchase_transaction_total.csv")

    # Municipal purchase: exact curated matches; no fuzzy automatic assignment.
    cities = json.loads((RAW / "cities/selection.json").read_text())
    aliases = {
        "08019": ["Barcelona"],
        "28079": ["Madrid"],
        "46250": ["Valencia"],
        "07040": ["Palma de Mallorca", "Palma"],
        "03014": ["Alicante/Alacant", "Alicante"],
        "15030": ["Coruña (A)", "A Coruña"],
        "08101": [
            "Hospitalet de Llobregat (L')",
            "Hospitalet de Llobregat",
            "L'Hospitalet de Llobregat",
        ],
        "12040": ["Castellón de la Plana", "Castellón de la Plana/Castelló de la Plana"],
    }
    names = {}
    for city in cities:
        for name in aliases.get(city["muniCode"], [city["muni"]]):
            names[normalise(name)] = city["muniCode"]
    book = pd.ExcelFile(RAW / "municipal_purchase.xls")
    municipal = []
    for sheet in book.sheet_names:
        match = re.match(r"T([1-4])A(\d{4})", sheet)
        if not match:
            continue
        q, year = map(int, match.groups())
        if not 2005 <= year <= 2025:
            continue
        frame = pd.read_excel(book, sheet, header=None)
        for _, row in frame.iterrows():
            if len(row) < 6:
                continue
            code = names.get(normalise(row.iloc[2]))
            value = pd.to_numeric(row.iloc[5], errors="coerce")
            if code and pd.notna(value) and value > 0:
                municipal.append({"code": code, "year": year, "quarter": q, "value": value})
    municipal = pd.DataFrame(municipal)
    if municipal.duplicated(["code", "year", "quarter"]).any():
        raise ValueError("Ambiguous municipal purchase match")
    write(annual_complete(municipal, ["code", "year"]), "municipal_purchase.csv")
    write(pd.DataFrame(cities).drop(columns=["error"], errors="ignore"), "selected_cities.csv")

    # Senate appointment facts, exact decree dates; party of presidency, not full cabinet.
    months = {
        m: i + 1
        for i, m in enumerate(
            [
                "enero",
                "febrero",
                "marzo",
                "abril",
                "mayo",
                "junio",
                "julio",
                "agosto",
                "septiembre",
                "octubre",
                "noviembre",
                "diciembre",
            ]
        )
    }
    senate_regions = {
        1: "16",
        2: "09",
        3: "12",
        4: "01",
        5: "03",
        6: "06",
        7: "17",
        8: "14",
        9: "10",
        10: "02",
        11: "08",
        12: "05",
        13: "15",
        14: "11",
        15: "04",
        16: "13",
        17: "07",
    }
    governments = []
    for number, code in senate_regions.items():
        lines = (RAW / f"governments/{number:02d}.txt").read_text().splitlines()
        source = f"https://www.senado.es/web/conocersenado/biblioteca/dossieresareastematicas/detalle/index.html?id=presidentes_gobiernos_{number:02d}&lang=es_ES"
        rows = []
        for i, line in enumerate(lines):
            if not line.startswith("Nombramiento:"):
                continue
            match = re.search(r"(\d+)/(\d{4}),?\s+(?:de\s+)?(\d{1,2})\s+de\s+(\w+)", line)
            party = re.findall(
                r"\((PP|PSOE|PSC|PNV|ERC|JxCat|JxSÍ|CiU|PRC|FAC|CC|UPN|GBai)\)", lines[i - 1]
            )
            if not match or not party or match[4] not in months:
                continue
            _, year, day, month = match.groups()
            date = f"{year}-{months[month]:02d}-{int(day):02d}"
            rows.append(
                {
                    "level": "region",
                    "code": code,
                    "name": REGIONS[code],
                    "leader": lines[i - 1],
                    "party": party[-1],
                    "start": date,
                    "source_url": source,
                    "date_basis": "royal_decree_appointment",
                }
            )
        rows = sorted(rows, key=lambda r: r["start"])
        for i, row in enumerate(rows):
            row["end"] = rows[i + 1]["start"] if i + 1 < len(rows) else ""
            if row["start"] <= "2025-12-31" and (not row["end"] or row["end"] >= "1995-01-01"):
                governments.append(row)
    gov = pd.DataFrame(governments)
    # Expose constitutional intervention and interim period rather than mislabelling Torra.
    gov.loc[(gov.code == "09") & (gov.party == "PP"), "party"] = "Art.155 (PP nacional)"
    mask = (gov.code == "09") & (gov.party == "JxCat")
    gov.loc[mask, "end"] = "2020-09-28"
    interim = gov[mask].iloc[0].to_dict()
    interim.update(
        leader="Pere Aragonès (funciones)",
        party="ERC (funciones)",
        start="2020-09-28",
        end="2021-05-21",
        date_basis="court_disqualification",
    )
    gov = pd.concat([gov, pd.DataFrame([interim])], ignore_index=True)
    national = [
        ("1993-07-09", "1996-05-04", "PSOE", "Felipe González"),
        ("1996-05-04", "2004-04-17", "PP", "José María Aznar"),
        ("2004-04-17", "2011-12-21", "PSOE", "José Luis Rodríguez Zapatero"),
        ("2011-12-21", "2018-06-02", "PP", "Mariano Rajoy"),
        ("2018-06-02", "2020-01-13", "PSOE", "Pedro Sánchez"),
        ("2020-01-13", "2023-11-21", "PSOE + UP", "Pedro Sánchez"),
        ("2023-11-21", "", "PSOE + Sumar", "Pedro Sánchez"),
    ]
    for start, end, party, leader in national:
        gov = pd.concat(
            [
                gov,
                pd.DataFrame(
                    [
                        dict(
                            level="national",
                            code="00",
                            name="España",
                            leader=leader,
                            party=party,
                            start=start,
                            end=end,
                            date_basis="president_or_cabinet_inauguration",
                            source_url={
                                "1993-07-09": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-1993-18045",
                                "1996-05-04": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-1996-9942",
                            }.get(
                                start,
                                "https://www.lamoncloa.gob.es/presidente/presidentes/Paginas/index.aspx",
                            ),
                        )
                    ]
                ),
            ],
            ignore_index=True,
        )
    write(gov, "governments.csv")
    for file, prop in [("communities.geojson", "cod_ccaa"), ("provinces.geojson", "cod_prov")]:
        original = json.loads((RAW / file).read_text())
        features = []
        for feature in original["features"]:
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "code": feature["properties"][prop],
                        "name": feature["properties"]["name"],
                    },
                    "geometry": mapping(
                        shape(feature["geometry"]).simplify(0.012, preserve_topology=True)
                    ),
                }
            )
        (OUT / file).write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    manifest = []
    for name, url in URLS.items():
        manifest.append(
            {
                "source_file": name,
                "url": url,
                "sha256": hashlib.sha256((RAW / name).read_bytes()).hexdigest(),
                "bytes": (RAW / name).stat().st_size,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
    for name in ["communities.geojson", "provinces.geojson"]:
        manifest.append(
            {
                "source_file": name,
                "url": f"https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/spain-{name}",
                "sha256": hashlib.sha256((RAW / name).read_bytes()).hexdigest(),
                "bytes": (RAW / name).stat().st_size,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
    for number in range(1, 18):
        name = f"governments/{number:02d}.html"
        manifest.append(
            {
                "source_file": name,
                "url": (
                    "https://www.senado.es/web/conocersenado/biblioteca/"
                    "dossieresareastematicas/detalle/index.html?"
                    f"id=presidentes_gobiernos_{number:02d}&lang=es_ES"
                ),
                "sha256": hashlib.sha256((RAW / name).read_bytes()).hexdigest(),
                "bytes": (RAW / name).stat().st_size,
                "retrieved_at_utc": datetime.fromtimestamp(
                    (RAW / name).stat().st_mtime, timezone.utc
                ).isoformat(),
            }
        )
    for item in cities:
        manifest.append(
            {
                "source_file": f"cities/{item['muniCode']}.json",
                "url": item["url"],
                "sha256": item["raw_sha256"],
                "hash_scope": "original_api_response",
                "retrieved_at_utc": datetime.fromtimestamp(
                    (RAW / f"cities/{item['muniCode']}.json").stat().st_mtime, timezone.utc
                ).isoformat(),
            }
        )
    (OUT / "source_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Built real-data snapshots:", OUT)


if __name__ == "__main__":
    build()
