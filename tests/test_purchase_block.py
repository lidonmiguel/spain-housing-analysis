"""Verify the purchase-only scope and actual comparison windows."""

import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from spain_housing.prices_analysis import load_purchase_data, series_for

ROOT = Path(__file__).resolve().parents[1]


class PurchaseBlockTests(unittest.TestCase):
    def test_block_does_not_require_rental_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "data/snapshots/block01"
            snapshot.mkdir(parents=True)
            for name in [
                "valuations",
                "municipal_purchase",
                "selected_cities",
                "cpi",
                "governments",
            ]:
                shutil.copyfile(
                    ROOT / "data/snapshots/block01" / f"{name}.csv", snapshot / f"{name}.csv"
                )
            values, municipal, cpi, _ = load_purchase_data(directory)
            self.assertEqual(values.year.min(), 2000)
            self.assertEqual(values.year.max(), 2025)
            self.assertEqual(municipal.year.min(), 2005)
            self.assertEqual(municipal.year.max(), 2025)
            self.assertEqual(cpi.index.min(), 2002)

    def test_comparison_uses_same_valuation_and_exact_common_years(self):
        values, _, cpi, _ = load_purchase_data(ROOT)
        p = series_for(values, level="national")
        table = pd.read_csv(
            ROOT / "reports/tables/block01/national_comparison.csv", index_col="year"
        )
        self.assertEqual(list(table.index), list(range(2002, 2026)))
        self.assertEqual(
            list(table.columns), ["purchase_valuation_index", "general_prices_cpi_index"]
        )
        np.testing.assert_allclose(
            table.purchase_valuation_index, p.loc[table.index] / p.loc[2002] * 100
        )
        np.testing.assert_allclose(
            table.general_prices_cpi_index, cpi.loc[table.index] / cpi.loc[2002] * 100
        )

    def test_government_results_are_only_purchase_and_complete_years(self):
        table = pd.read_csv(ROOT / "reports/tables/block01/government_history.csv")
        self.assertEqual(set(table.metric), {"purchase_valuation"})
        observed = table.dropna(subset=["first_year", "last_year"])
        self.assertTrue((observed.first_year >= 2000).all())
        self.assertTrue((observed.last_year <= 2025).all())
        self.assertTrue((observed.last_year > observed.first_year).all())


if __name__ == "__main__":
    unittest.main()
