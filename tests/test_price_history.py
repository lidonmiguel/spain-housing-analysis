"""Verify historical comparability and that missing coverage stays visible."""

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from spain_housing.price_history import government_history, history_summary, real_series

SNAPSHOT = Path(__file__).resolve().parents[1] / "data/snapshots/block01"


class HistoryTests(unittest.TestCase):
    def test_constant_prices_require_observed_inflation(self):
        s = pd.Series([100.0, 150.0, 180.0], index=[1995, 2002, 2025])
        cpi = pd.Series([100.0, 120.0], index=[2002, 2025])
        real = real_series(s, cpi, 2025)
        self.assertTrue(np.isnan(real.loc[1995]))
        self.assertAlmostEqual(real.loc[2002], real.loc[2025])
        with self.assertRaises(ValueError):
            real_series(s, cpi, 1995)

    def test_cycle_windows_and_real_coverage_are_explicit(self):
        frame = pd.DataFrame(
            dict(
                code=["00"] * 6,
                year=[1995, 2002, 2008, 2014, 2020, 2025],
                value=[50, 100, 200, 120, 250, 300],
            )
        )
        cpi = pd.Series([100, 120, 130, 140, 150], index=[2002, 2008, 2014, 2020, 2025])
        row = history_summary(frame, cpi, ["code"]).iloc[0]
        self.assertEqual(row.precrisis_peak_year, 2008)
        self.assertEqual(row.postcrisis_trough_year, 2014)
        self.assertAlmostEqual(row.peak_to_trough_pct, -40)
        self.assertEqual(row.real_first_year, 2002)
        self.assertEqual(row.missing_years, 25)
        self.assertAlmostEqual(row.real_change_pct, 100)

    def test_single_observation_is_not_zero_historical_growth(self):
        frame = pd.DataFrame(dict(code=["16"], year=[2024], value=[10.09]))
        row = history_summary(frame, pd.Series([120], index=[2024]), ["code"]).iloc[0]
        self.assertEqual(row.observed_years, 1)
        self.assertTrue(np.isnan(row.nominal_change_pct))
        self.assertTrue(np.isnan(row.real_change_pct))

    def test_historical_government_excludes_transition_years(self):
        frame = pd.DataFrame(
            dict(code=["00"] * 5, year=range(1995, 2000), value=[50, 80, 100, 110, 150])
        )
        gov = pd.DataFrame(
            [
                dict(
                    level="national",
                    code="00",
                    name="España",
                    leader="L",
                    party="P",
                    start="1996-05-04",
                    end="1999-06-01",
                )
            ]
        )
        row = government_history(
            frame, gov, pd.Series(100, index=range(1995, 2000)), "national", "valuation"
        ).iloc[0]
        self.assertEqual(row.first_year, 1997)
        self.assertEqual(row.last_year, 1998)
        self.assertAlmostEqual(row.nominal_change_pct, 10)

    def test_extended_sources_are_unique_and_overlap_existing_rent(self):
        rent = pd.read_csv(SNAPSHOT / "rent_general_history.csv", dtype={"code": str})
        self.assertFalse(rent.duplicated(["code", "year"]).any())
        self.assertEqual(rent.year.min(), 2011)
        old = pd.read_csv(SNAPSHOT / "rent_index.csv", dtype={"code": str})
        old = old[old.contract == "Total"]
        overlap = rent.merge(old, on=["code", "year"], suffixes=("_long", "_old"))
        self.assertEqual(len(overlap), len(old))
        np.testing.assert_allclose(overlap.value_long, overlap.value_old, atol=0.001)
        municipal = pd.read_csv(SNAPSHOT / "municipal_purchase.csv")
        self.assertEqual(municipal.year.min(), 2005)
        self.assertEqual(municipal.year.max(), 2025)
        self.assertEqual(len(municipal), 30 * 21)


if __name__ == "__main__":
    unittest.main()
