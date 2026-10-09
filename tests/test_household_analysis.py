"""Check that household-growth components behave in independent edge cases."""

import unittest

import numpy as np
import pandas as pd

from spain_housing.household_analysis import decompose_households


class HouseholdAccountingTests(unittest.TestCase):
    def test_unchanged_population_assigns_growth_to_intensity(self):
        data = decompose_households(
            pd.Series([100, 100], index=[2020, 2021]), pd.Series([40, 50], index=[2020, 2021])
        )
        self.assertEqual(data.loc[2021, "population_component"], 0)
        self.assertAlmostEqual(data.loc[2021, "household_intensity_component"], 10)

    def test_constant_occupancy_assigns_growth_to_population(self):
        data = decompose_households(
            pd.Series([100, 120], index=[2020, 2021]), pd.Series([40, 48], index=[2020, 2021])
        )
        self.assertAlmostEqual(data.loc[2021, "population_component"], 8)
        self.assertEqual(data.loc[2021, "household_intensity_component"], 0)

    def test_opposing_components_cancel_and_missing_year_is_not_bridged(self):
        data = decompose_households(
            pd.Series([100, 120, 140], index=[2020, 2021, 2023]),
            pd.Series([40, 40, 50], index=[2020, 2021, 2023]),
        )
        self.assertGreater(data.loc[2021, "population_component"], 0)
        self.assertLess(data.loc[2021, "household_intensity_component"], 0)
        self.assertAlmostEqual(
            data.loc[2021, "population_component"]
            + data.loc[2021, "household_intensity_component"],
            0,
        )
        self.assertTrue(np.isnan(data.loc[2023, "household_change"]))


if __name__ == "__main__":
    unittest.main()
