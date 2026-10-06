import hashlib
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

root = Path(__file__).resolve().parents[1] / "data/raw/block01/governments"
root.mkdir(parents=True, exist_ok=True)


def get(n):
    if (root / f"{n:02d}.html").exists() and (root / f"{n:02d}.txt").exists():
        return {"id": n, "cached": True}
    url = f"https://www.senado.es/web/conocersenado/biblioteca/dossieresareastematicas/detalle/index.html?id=presidentes_gobiernos_{n:02d}&lang=es_ES"
    try:
        data = urlopen(url, timeout=45).read()
        s = data.decode()
        text = html.unescape(re.sub("<[^>]+>", "\n", s))
        text = "\n".join(t.strip() for t in text.splitlines() if t.strip())
        i = text.find("Presidentes del Gobierno")
        if i < 0:
            i = text.find("Presidentes de")
        text = text[i:]
        (root / f"{n:02d}.txt").write_text(text)
        (root / f"{n:02d}.html").write_bytes(data)
        print(n, text.splitlines()[0], flush=True)
        return {"id": n, "url": url, "title": text.splitlines()[0]}
    except Exception as e:
        print(n, e, flush=True)
        return {"id": n, "url": url, "error": str(e)}


def fetch_governments():
    with ThreadPoolExecutor(max_workers=5) as ex:
        records = list(ex.map(get, range(1, 18)))
    failures = [r for r in records if "error" in r]
    if failures:
        raise RuntimeError(f"Political source retrieval failed: {failures}")


cities = [
    ("08019", "Barcelona", "Barcelona", "large_city", "coastal"),
    ("28079", "Madrid", "Madrid", "large_city", "inland"),
    ("46250", "Valencia", "Valencia", "large_city", "coastal"),
    ("29067", "Málaga", "Málaga", "large_city", "coastal"),
    ("50297", "Zaragoza", "Zaragoza", "large_city", "inland"),
    ("41091", "Sevilla", "Sevilla", "large_city", "inland"),
    ("07040", "Palma", "Illes Balears", "large_city", "coastal"),
    ("03014", "Alicante", "Alicante", "large_city", "coastal"),
    ("47186", "Valladolid", "Valladolid", "large_city", "inland"),
    ("18087", "Granada", "Granada", "large_city", "inland"),
    ("14021", "Córdoba", "Córdoba", "large_city", "inland"),
    ("30030", "Murcia", "Murcia", "large_city", "inland"),
    ("15030", "A Coruña", "A Coruña", "large_city", "coastal"),
    ("39075", "Santander", "Cantabria", "large_city", "coastal"),
    ("33024", "Gijón", "Asturias", "large_city", "coastal"),
    ("33044", "Oviedo", "Asturias", "large_city", "inland"),
    ("08015", "Badalona", "Barcelona", "periphery", "coastal"),
    ("08101", "Hospitalet de Llobregat", "Barcelona", "periphery", "unclassified"),
    ("08279", "Terrassa", "Barcelona", "periphery", "inland"),
    ("08187", "Sabadell", "Barcelona", "periphery", "inland"),
    ("28065", "Getafe", "Madrid", "periphery", "inland"),
    ("28074", "Leganés", "Madrid", "periphery", "inland"),
    ("28006", "Alcobendas", "Madrid", "periphery", "inland"),
    ("45168", "Toledo", "Toledo", "selected_city", "inland"),
    ("09059", "Burgos", "Burgos", "selected_city", "inland"),
    ("24089", "León", "León", "selected_city", "inland"),
    ("37274", "Salamanca", "Salamanca", "selected_city", "inland"),
    ("11012", "Cádiz", "Cádiz", "selected_city", "coastal"),
    ("21041", "Huelva", "Huelva", "selected_city", "coastal"),
    ("12040", "Castellón de la Plana", "Castellón", "selected_city", "coastal"),
]
city_root = Path(__file__).resolve().parents[1] / "data/raw/block01/cities"
city_root.mkdir(parents=True, exist_ok=True)


def fetch(c):
    if (city_root / f"{c[0]}.json").exists():
        return json.loads((city_root / f"{c[0]}.json").read_text())
    code, name, prov, urban, coast = c
    url = "https://www.cartociudad.es/geocoder/api/geocoder/find?" + urlencode(
        {"q": f"{name}, {prov}"}
    )
    try:
        raw = urlopen(url, timeout=40).read()
        j = json.loads(raw)
        if j.get("muniCode") != code:
            raise ValueError(f"Returned {j.get('muniCode')} instead of {code}")
        row = {
            k: j[k]
            for k in ["muni", "muniCode", "lat", "lng", "provinceCode", "comunidadAutonomaCode"]
        }
        row.update(
            urban_category=urban,
            coastal_category=coast,
            url=url,
            raw_sha256=hashlib.sha256(raw).hexdigest(),
        )
        (city_root / f"{code}.json").write_text(json.dumps(row, ensure_ascii=False))
        print(code, name, "ok", flush=True)
        return row
    except Exception as e:
        print(code, name, str(e)[:100], flush=True)
        return {
            "muniCode": code,
            "muni": name,
            "urban_category": urban,
            "coastal_category": coast,
            "url": url,
            "error": str(e),
        }


def fetch_cities():
    with ThreadPoolExecutor(max_workers=5) as ex:
        rows = list(ex.map(fetch, cities))
    if any("error" in r for r in rows):
        raise RuntimeError("Municipal geocoding failed")
    (city_root / "selection.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    fetch_governments()
    fetch_cities()
