"""Check timing, age boundaries, aggregation and source integrity."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from spain_housing.demographics import (
    annual_change,
    common_index,
    construction_series,
    load_panels,
    population_series,
    read_source,
)

ROOT = Path(__file__).resolve().parents[1]


class DemographicTests(unittest.TestCase):
    def test_changes_do_not_bridge_missing_years(self):
        result = annual_change(pd.Series([100, 110, 150], index=[2000, 2001, 2003]))
        self.assertEqual(result.loc[2001], 10)
        self.assertTrue(pd.isna(result.loc[2003]))

    def test_indices_share_base_and_missingness(self):
        data = pd.DataFrame({"a": [10, 20, 30], "b": [np.nan, 80, 100]}, index=[2000, 2001, 2002])
        indexed = common_index(data)
        self.assertEqual(indexed.index[0], 2001)
        np.testing.assert_allclose(indexed.iloc[0], [100, 100])
        np.testing.assert_allclose(indexed.iloc[1], [150, 125])

    def test_age_18_is_an_adult_and_only_january_is_used(self):
        rows = [
            {
                "Edad simple": "Todas las edades",
                "Sexo": "Total",
                "Periodo": "1 de enero de 2021",
                "Total": "1.000",
            }
        ]
        rows += [
            {
                "Edad simple": f"{a} años",
                "Sexo": "Total",
                "Periodo": "1 de enero de 2021",
                "Total": "10",
            }
            for a in range(19)
        ]
        rows += [
            {
                "Edad simple": "Todas las edades",
                "Sexo": "Total",
                "Periodo": "1 de julio de 2021",
                "Total": "2.000",
            }
        ]
        result = population_series(pd.DataFrame(rows), "fixture")
        self.assertEqual(result.loc[2021, "adults"], 820)
        self.assertEqual(len(result), 1)
        with self.assertRaises(ValueError):
            population_series(pd.DataFrame(rows).drop(index=1), "fixture")

    def test_incomplete_or_duplicate_construction_is_rejected(self):
        data = read_source(ROOT, "construction")
        with self.assertRaises(ValueError):
            construction_series(pd.concat([data, data[data.CODAUTO == "0"].iloc[:1]]))
        national_row = data.index[data.CODAUTO == "0"][0]
        with self.assertRaises(ValueError):
            construction_series(data.drop(index=national_row))

    def test_real_sources_preserve_accounting_and_timing(self):
        panel, birth, components, regional = load_panels(ROOT)
        raw = read_source(ROOT, "population")
        selected = raw[
            (raw.Sexo == "Total")
            & (raw["Edad simple"] == "Todas las edades")
            & (raw.Periodo == "1 de enero de 2025")
        ].Total.iloc[0]
        self.assertEqual(panel.loc[2024, "population"], float(selected.replace(".", "")))
        self.assertEqual(panel.loc[2025, "population_status"], "provisional")
        np.testing.assert_allclose(birth.born_spain + birth.born_abroad, birth.population)
        np.testing.assert_allclose(
            birth.change_born_spain.dropna() + birth.change_born_abroad.dropna(),
            panel.loc[birth.change_born_spain.dropna().index, "population_change"],
            atol=2,  # Published birthplace integers can differ from older decimal totals.
        )
        self.assertTrue((panel.adults <= panel.population).all())
        self.assertTrue(panel.loc[:2019, "net_household_formation"].isna().all())
        self.assertEqual(set(regional.code), set(range(1, 18)))
        self.assertEqual(components.index.max(), 2024)

    def test_modified_snapshot_is_rejected(self):
        import json

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "data/snapshots/block02"
            folder.mkdir(parents=True)
            source = ROOT / "data/snapshots/block02/source_manifest.json"
            manifest = json.loads(source.read_text())
            item = next(x for x in manifest["sources"] if x["name"] == "natural")
            (folder / "source_manifest.json").write_text(json.dumps(manifest))
            (Path(tmp) / item["snapshot_path"]).write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "checksum"):
                read_source(tmp, "natural")


if __name__ == "__main__":
    unittest.main()
