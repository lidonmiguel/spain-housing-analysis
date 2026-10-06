"""Read municipal valuation prices by headers, across the MIVAU Excel layouts."""

import re
import unicodedata

import pandas as pd


def normalise(value):
    value = unicodedata.normalize("NFKD", str(value).lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in value if not unicodedata.combining(c)))


def valuation_columns(frame):
    """Locate municipality and total price; never use the tasaciones count."""
    if not any("eurosm2" in normalise(v) for v in frame.to_numpy().flat):
        raise ValueError("Municipal valuation sheet is missing the euros/m² unit")
    for row_number, row in enumerate(frame.itertuples(index=False, name=None)):
        labels = [normalise(v) if pd.notna(v) else "" for v in row]
        if "municipio" not in labels:
            continue
        price_headers = [
            col
            for col, label in enumerate(labels)
            if label in {"valormedio", "valortasadodevivienda"}
        ]
        if len(price_headers) != 1:
            continue
        first = price_headers[0]
        following = [col for col in range(first + 1, len(labels)) if labels[col]]
        last = following[0] if following else len(labels)
        totals = {
            col
            for lower_row in range(row_number + 1, min(row_number + 4, len(frame)))
            for col in range(first, last)
            if normalise(frame.iloc[lower_row, col]) == "total"
        }
        if len(totals) == 1:
            return labels.index("municipio"), totals.pop()
    raise ValueError("Cannot identify the total municipal valuation price column")


def municipal_quarters(book, names, first_year=2005, last_year=2025):
    """Extract observed quarterly prices for the exact curated name matches."""
    observations = []
    for sheet in book.sheet_names:
        match = re.match(r"T([1-4])A(\d{4})", sheet)
        if not match:
            continue
        quarter, year = map(int, match.groups())
        if not first_year <= year <= last_year:
            continue
        frame = pd.read_excel(book, sheet, header=None)
        municipality_col, price_col = valuation_columns(frame)
        for row in frame.itertuples(index=False, name=None):
            code = names.get(normalise(row[municipality_col]))
            value = pd.to_numeric(row[price_col], errors="coerce")
            if code and pd.notna(value) and value > 0:
                observations.append(
                    {"code": code, "year": year, "quarter": quarter, "value": value}
                )
    result = pd.DataFrame(observations, columns=["code", "year", "quarter", "value"])
    if result.duplicated(["code", "year", "quarter"]).any():
        raise ValueError("Ambiguous municipal purchase match")
    return result
