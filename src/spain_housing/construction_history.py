"""Verified official construction history, read offline."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_construction_history(root):
    from .demographics import construction_series, read_source

    folder = Path(root) / "data/snapshots/block02"
    path = folder / "construction_history_2000_2012.csv"
    meta = json.loads((folder / "construction_history_source.json").read_text(encoding="utf-8"))
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta["csv_sha256"]:
        raise ValueError("Construction history checksum mismatch")
    old = pd.read_csv(path).set_index("year")[["starts", "completions"]]
    recent = construction_series(read_source(root, "construction"))
    common = old.index.intersection(recent.index)
    if len(common) != 5:
        raise ValueError("Five overlapping construction years required")
    np.testing.assert_array_equal(old.loc[common], recent.loc[common, old.columns])
    data = pd.concat([old.loc[old.index < recent.index.min()], recent]).sort_index()
    if list(data.loc[2000:2025].index) != list(range(2000, 2026)):
        raise ValueError("Incomplete construction history")
    return data
