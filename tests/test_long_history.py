"""Check the historical euro conversion without mistaking it for observed prices."""

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from spain_housing.long_history import load_long_history
from spain_housing.prices_analysis import load_purchase_data, series_for

ROOT = Path(__file__).resolve().parents[1]


class LongHistoryTests(unittest.TestCase):
    def test_coverage_excludes_forecasts_and_incomplete_years(self):
        panel = load_long_history(ROOT)
        self.assertEqual(panel.index.tolist(), list(range(1971, 2026)))
        self.assertAlmostEqual(panel.loc[1971, "compensation_eur"], 932.36)
        self.assertAlmostEqual(panel.loc[2025, "compensation_eur"], 42260.52)

    def test_estimated_euros_match_anchor_and_preserve_price_growth(self):
        panel = load_long_history(ROOT)
        saved = pd.read_csv(
            ROOT / "reports/tables/block01/long_housing_compensation.csv", index_col="year"
        )
        values, _, _, _ = load_purchase_data(ROOT)
        anchor = series_for(values, level="national").loc[2025] * 80
        expected = panel.housing_bis_index / panel.loc[2025, "housing_bis_index"] * anchor
        np.testing.assert_allclose(saved.housing_80m2_estimated_eur, expected)
        self.assertAlmostEqual(saved.loc[2025, "housing_80m2_estimated_eur"], anchor)
        self.assertAlmostEqual(
            expected.iloc[-1] / expected.iloc[0],
            panel.housing_bis_index.iloc[-1] / panel.housing_bis_index.iloc[0],
        )
