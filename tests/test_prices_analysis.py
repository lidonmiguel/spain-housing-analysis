"""Guard against false year-on-year changes, mixed series and fabricated coverage."""

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from spain_housing.prices_analysis import (
    annual_changes,
    change,
    endpoint_table,
    load_rental_snapshot,
    mandate_table,
    series_for,
)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/snapshots/block01"


class PriceAnalysisTests(unittest.TestCase):
    def test_missing_year_does_not_become_annual_growth(self):
        s = pd.Series([100.0, 120.0, 132.0], index=[2011, 2013, 2014])
        rates = annual_changes(s)
        self.assertTrue(np.isnan(rates.loc[2013]))
        self.assertAlmostEqual(rates.loc[2014], 10)
        self.assertTrue(np.isnan(change(s, 2012, 2014)))

    def test_missing_start_keeps_level_but_not_growth(self):
        data = pd.DataFrame({"code": ["16"], "year": [2024], "value": [10.09]})
        table = endpoint_table(data)
        self.assertEqual(table.last_value.iloc[0], 10.09)
        self.assertTrue(np.isnan(table.change_pct.iloc[0]))

    def test_mixed_units_raise_instead_of_silently_averaging(self):
        frame = pd.DataFrame({"code": ["00", "00"], "year": [2024, 2024], "value": [100, 500]})
        with self.assertRaises(ValueError):
            series_for(frame)

    def test_mandate_excludes_both_transition_years(self):
        frame = pd.DataFrame(
            {"code": ["01"] * 5, "year": range(2011, 2016), "value": [90, 100, 110, 121, 150]}
        )
        gov = pd.DataFrame(
            [
                {
                    "level": "region",
                    "code": "01",
                    "name": "A",
                    "leader": "L",
                    "party": "P",
                    "start": "2011-06-01",
                    "end": "2015-06-01",
                }
            ]
        )
        result = mandate_table(frame, frame, gov, pd.Series(100, index=range(2011, 2016)))
        self.assertEqual(result.first_year.iloc[0], 2012)
        self.assertEqual(result.last_year.iloc[0], 2014)
        self.assertAlmostEqual(result.purchase_change_pct.iloc[0], 21)
        self.assertAlmostEqual(result.purchase_annualised_pct.iloc[0], 10)

    def test_snapshots_have_unique_positive_observations_and_full_price_coverage(self):
        for file, keys in [
            ("purchase_index.csv", ["code", "year"]),
            ("valuations.csv", ["level", "code", "year"]),
            ("rental_medians_2011_2017.csv.gz", ["level", "code", "year", "unit"]),
            ("rental_medians_2018_2024.csv.gz", ["level", "code", "year", "unit"]),
            ("municipal_purchase.csv", ["code", "year"]),
        ]:
            data = pd.read_csv(SNAPSHOT / file, dtype={"code": str})
            with self.subTest(file=file):
                self.assertFalse(data.duplicated(keys).any())
                self.assertTrue(np.isfinite(data.value).all())
                self.assertTrue((data.value > 0).all())
        values = pd.read_csv(SNAPSHOT / "valuations.csv", dtype={"code": str})
        current = values[values.year == 2024]
        self.assertEqual(current[current.level == "region"].code.nunique(), 19)
        self.assertEqual(current[current.level == "province"].code.nunique(), 52)
        rental = load_rental_snapshot(SNAPSHOT)
        regions = rental[rental.level == "region"]
        self.assertEqual(regions[regions.code == "15"].year.min(), 2021)
        self.assertEqual(regions[regions.code == "16"].year.min(), 2024)


if __name__ == "__main__":
    unittest.main()
