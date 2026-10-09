"""Protect fiscal-profile selection, comparison windows and percentage-point gaps."""

import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from spain_housing.salary_analysis import (
    GROSS,
    HOUSING,
    NET,
    earnings_series,
    load_salary_comparison,
    variation_gaps,
)

ROOT = Path(__file__).resolve().parents[1]


class SalaryAnalysisTests(unittest.TestCase):
    def test_snapshot_decodes_gross_and_net_not_total_employer_cost(self):
        dataset = json.loads(
            (ROOT / "data/snapshots/block01/salary_eurostat.json").read_text(encoding="utf-8")
        )["data"]
        gross, status = earnings_series(dataset, "GRS")
        net, _ = earnings_series(dataset, "NET")
        self.assertAlmostEqual(gross.loc[2023], 30249.96)
        self.assertAlmostEqual(net.loc[2023], 23597.08)
        self.assertEqual(status.loc[2024], "b")

    def test_common_window_and_deflation_preserve_housing_wage_ratio(self):
        panel, nominal, real = load_salary_comparison(ROOT)
        self.assertEqual(panel.index.tolist(), list(range(2000, 2024)))
        self.assertEqual(list(nominal.columns), [HOUSING, GROSS, NET])
        np.testing.assert_allclose(real.iloc[-1], nominal.iloc[-1])
        for wage in [GROSS, NET]:
            np.testing.assert_allclose(nominal[HOUSING] / nominal[wage], real[HOUSING] / real[wage])

    def test_gap_is_difference_of_rates_and_never_bridges_missing_year(self):
        amounts = pd.DataFrame(
            {HOUSING: [100, 108, 150, 165], GROSS: [100, 103, 100, 102], NET: [100, 104, 100, 101]},
            index=[2002, 2003, 2005, 2006],
        )
        gaps = variation_gaps(amounts)
        self.assertEqual(gaps.index.tolist(), [2003, 2006])
        self.assertAlmostEqual(gaps.iloc[0, 0], 5)
        self.assertAlmostEqual(gaps.iloc[0, 1], 4)
        self.assertAlmostEqual(gaps.iloc[1, 0], 8)
        self.assertAlmostEqual(gaps.iloc[1, 1], 9)

    def test_saved_gap_table_matches_frozen_sources(self):
        _, nominal, _ = load_salary_comparison(ROOT)
        expected = variation_gaps(nominal)
        actual = pd.read_csv(
            ROOT / "reports/tables/block01/housing_salary_variation_gap.csv", index_col="year"
        )
        self.assertEqual(actual.index.tolist(), list(range(2001, 2024)))
        self.assertEqual(list(actual.columns), list(expected.columns))
        np.testing.assert_allclose(actual, expected, atol=1e-8)


if __name__ == "__main__":
    unittest.main()
