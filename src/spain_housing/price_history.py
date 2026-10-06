"""Long housing histories, retaining source definitions and observed coverage."""

from pathlib import Path

import numpy as np
import pandas as pd

from spain_housing.prices_analysis import change, series_for


def real_series(series, cpi, reference_year):
    """Constant-reference-year prices, only at years with observed CPI."""
    if reference_year not in cpi.index:
        raise ValueError("Reference CPI year is not observed")
    return series * cpi.loc[reference_year] / cpi.reindex(series.index)


def history_summary(frame, cpi, keys):
    """Coverage, actual endpoint changes and explicitly bounded purchase-cycle extrema."""
    rows = []
    for group, data in frame.groupby(keys, dropna=False):
        if not isinstance(group, tuple):
            group = (group,)
        s = data.set_index("year").value.sort_index()
        if s.index.has_duplicates:
            raise ValueError("History must contain a single observation per year")
        first, last = int(s.index.min()), int(s.index.max())
        real = real_series(s, cpi, int(cpi.index.max())).dropna()
        pre = s.loc[(s.index >= 1995) & (s.index <= 2008)]
        post = s.loc[(s.index >= 2009) & (s.index <= 2015)]
        peak = int(pre.idxmax()) if len(pre) else None
        trough = int(post.idxmin()) if len(post) else None
        row = dict(zip(keys, group, strict=True))
        row.update(
            first_year=first,
            last_year=last,
            observed_years=len(s),
            missing_years=(last - first + 1) - len(s),
            first_value=s.loc[first],
            last_value=s.loc[last],
            nominal_change_pct=change(s, first, last) if len(s) >= 2 else np.nan,
            real_first_year=int(real.index.min()) if len(real) else None,
            real_last_year=int(real.index.max()) if len(real) else None,
            real_change_pct=change(real, real.index.min(), real.index.max())
            if len(real) >= 2
            else np.nan,
            precrisis_peak_year=peak,
            precrisis_peak_value=s.loc[peak] if peak is not None else np.nan,
            postcrisis_trough_year=trough,
            postcrisis_trough_value=s.loc[trough] if trough is not None else np.nan,
            peak_to_trough_pct=change(s, peak, trough),
            trough_to_latest_pct=change(s, trough, last),
            peak_to_latest_pct=change(s, peak, last),
        )
        rows.append(row)
    return pd.DataFrame(rows)


def government_history(frame, governments, cpi, level, metric):
    """Descriptive changes between fully observed years inside each presidency."""
    rows = []
    for gov in governments[governments.level == level].itertuples():
        s = series_for(frame, gov.code)
        start = pd.Timestamp(gov.start)
        end = pd.Timestamp(gov.end) if pd.notna(gov.end) and gov.end else pd.Timestamp("2026-01-01")
        years = [
            int(y)
            for y in s.index
            if pd.Timestamp(f"{y}-01-01") >= start and pd.Timestamp(f"{y + 1}-01-01") <= end
        ]
        row = dict(
            metric=metric,
            code=gov.code,
            name=gov.name,
            leader=gov.leader,
            party=gov.party,
            start=gov.start,
            end=gov.end,
            observed_complete_years=len(years),
            first_year=None,
            last_year=None,
            nominal_change_pct=np.nan,
            annualised_pct=np.nan,
            real_change_pct=np.nan,
        )
        if len(years) >= 2:
            a, b = min(years), max(years)
            pct = change(s, a, b)
            row.update(
                first_year=a,
                last_year=b,
                nominal_change_pct=pct,
                annualised_pct=100 * ((s.loc[b] / s.loc[a]) ** (1 / (b - a)) - 1),
            )
            if a in cpi.index and b in cpi.index:
                row["real_change_pct"] = 100 * ((1 + pct / 100) / (cpi.loc[b] / cpi.loc[a]) - 1)
        rows.append(row)
    return pd.DataFrame(rows)


def run_history(root):
    """Use the same purchase-only block for historical and main entry points."""
    from spain_housing.prices_analysis import run_analysis

    return run_analysis(Path(root))
