"""Prevent the historical tasaciones-count/price column mix-up."""

import unittest
from unittest.mock import patch

import pandas as pd

from spain_housing.municipal_data import municipal_quarters, valuation_columns


class MunicipalDataTests(unittest.TestCase):
    def test_prices_across_both_excel_layouts(self):
        old = pd.DataFrame(
            [
                [None, "Unidad: euros/m2", None, None, None, None],
                [None, "Provincia", "Municipio", "Valor medio", None, "Tasaciones"],
                [None, None, None, "Total", None, "Total"],
                [None, None, "Madrid", 3657.0, None, 15474],
            ]
        )
        new = pd.DataFrame(
            [
                [None, "Unidad: euros/m2", None, None, None, None, None, None],
                [
                    None,
                    "Provincia",
                    "Municipio",
                    "Valor tasado de vivienda",
                    None,
                    None,
                    None,
                    "Número de tasaciones",
                ],
                [
                    None,
                    None,
                    None,
                    "Hasta cinco años",
                    "Con más de cinco años",
                    "Total",
                    None,
                    "Total",
                ],
                [None, None, "Madrid", 3283.9, 3297.0, 3296.3, None, 7717],
            ]
        )
        self.assertEqual(valuation_columns(old), (2, 3))
        self.assertEqual(valuation_columns(new), (2, 5))
        book = type("Book", (), {"sheet_names": ["T1A2006 ", "T1A2010", "T1A2026"]})()
        with patch("spain_housing.municipal_data.pd.read_excel", side_effect=[old, new]):
            result = municipal_quarters(book, {"madrid": "28079"})
        self.assertEqual(result.value.tolist(), [3657.0, 3296.3])
        self.assertEqual(result.year.tolist(), [2006, 2010])

    def test_unknown_headers_fail_instead_of_guessing(self):
        frame = pd.DataFrame(
            [
                ["Unidad: euros/m2", None, None],
                ["Municipio", "Tasaciones", "Total"],
                ["Madrid", 15474, 3657],
            ]
        )
        with self.assertRaises(ValueError):
            valuation_columns(frame)

    def test_committed_madrid_history_contains_prices(self):
        from pathlib import Path

        path = Path(__file__).resolve().parents[1] / "data/snapshots/block01/municipal_purchase.csv"
        data = pd.read_csv(path, dtype={"code": str})
        madrid = data[data.code == "28079"].set_index("year").value
        self.assertAlmostEqual(madrid.loc[2006], 3700.575)
        self.assertAlmostEqual(madrid.loc[2009], 3421.850)
