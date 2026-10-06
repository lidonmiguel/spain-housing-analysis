"""Historical coverage, source breaks and comparable deflation."""

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from spain_housing.long_history import compare_window, rental_changes

SNAPSHOT = Path(__file__).resolve().parents[1] / "data/snapshots/history1950"


class LongHistoryTests(unittest.TestCase):
    def setUp(self):
        self.purchase = pd.read_csv(SNAPSHOT / "purchase_bis.csv")
        self.rental = pd.read_csv(SNAPSHOT / "rental_cpi_segments.csv")

    def test_1950_is_an_unobserved_horizon_not_filled_data(self):
        self.assertEqual(self.purchase.year.min(), 1971)
        self.assertEqual(self.rental.year.min(), 1961)
        for data, keys in [
            (self.purchase, ["year", "metric"]),
            (self.rental, ["year", "metric", "segment"]),
        ]:
            self.assertFalse(data.duplicated(keys).any())
            self.assertTrue(np.isfinite(data.value).all())
            self.assertTrue((data.value > 0).all())
        with self.assertRaises(ValueError):
            compare_window(self.purchase, self.rental, 1950, 1960)

    def test_madrid_proxy_is_not_labelled_national(self):
        data = self.purchase[self.purchase.metric == "purchase_nominal"].set_index("year")
        self.assertTrue(data.loc[1975:1986, "coverage"].eq("Madrid_area_proxy").all())
        self.assertEqual(data.loc[1987, "coverage"], "national_per_m2")
        self.assertEqual(data.loc[2007, "coverage"], "national_pure_price")
        self.assertAlmostEqual(data.loc[2010, "value"], 100, places=3)

    def test_annual_change_never_crosses_cpi_break(self):
        rates = rental_changes(self.rental).set_index("year")
        self.assertTrue(np.isnan(rates.loc[2002, "nominal_pct"]))
        self.assertTrue(np.isnan(rates.loc[2002, "real_pct"]))
        self.assertTrue(np.isfinite(rates.loc[2003, "nominal_pct"]))
        with self.assertRaises(ValueError):
            compare_window(self.purchase, self.rental, 1987, 2025)

    def test_equal_price_and_cpi_growth_gives_zero_real_change(self):
        purchase = pd.DataFrame(
            dict(year=[2002, 2003], metric=["purchase_nominal"] * 2, value=[100, 160])
        )
        rental = pd.DataFrame(
            dict(
                year=[2002, 2003] * 2,
                metric=["rent_cpi"] * 2 + ["cpi_general"] * 2,
                segment=["2002_2025"] * 4,
                value=[50, 80, 200, 320],
            )
        )
        frame = compare_window(purchase, rental, 2002, 2003)
        self.assertAlmostEqual(frame.purchase_real.loc[2003], 100)
        self.assertAlmostEqual(frame.rent_real.loc[2003], 100)
        self.assertAlmostEqual(frame.purchase_nominal.loc[2003], 160)


if __name__ == "__main__":
    unittest.main()
