"""Known financial examples and invalid denominators, independent of real datasets."""

import math
import unittest

from spain_housing.indicators import (
    constant_price,
    mortgage_payment,
    per_1000,
    price_to_income_years,
    rent_to_income_pct,
)


class IndicatorTests(unittest.TestCase):
    def test_units_and_inflation(self):
        self.assertEqual(rent_to_income_pct(1000, 40000), 30)
        self.assertEqual(price_to_income_years(240000, 40000), 6)
        self.assertEqual(per_1000(500, 10000), 50)
        self.assertEqual(constant_price(120000, 120, 100), 100000)

    def test_mortgage_known_example(self):
        self.assertAlmostEqual(mortgage_payment(200000, 0.03, 30), 843.208067, places=5)
        self.assertEqual(mortgage_payment(120000, 0, 20), 500)
        self.assertEqual(mortgage_payment(0, 0.03, 30), 0)

    def test_invalid_values_do_not_produce_indicators(self):
        for value in [0, -1, math.nan, math.inf]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                rent_to_income_pct(1000, value)
        with self.assertRaises(ValueError):
            constant_price(100, 0, 100)
        with self.assertRaises(ValueError):
            per_1000(-1, 100)
        for years in [0, -1, 1.5, True]:
            with self.subTest(years=years), self.assertRaises(ValueError):
                mortgage_payment(200000, 0.03, years)


if __name__ == "__main__":
    unittest.main()
