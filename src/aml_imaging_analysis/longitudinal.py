from __future__ import annotations

import pandas as pd


def compute_longitudinal_change(
    patient_df: pd.DataFrame,
    value_column: str,
    patient_id_column: str = "patient_id",
    time_column: str = "timepoint",
) -> pd.DataFrame:
    """Compute within-patient changes across longitudinal visits for AML analyses."""
    required = {patient_id_column, value_column, time_column}
    missing = required - set(patient_df.columns)
    if missing:
        raise ValueError(f"Missing required columns for longitudinal analysis: {sorted(missing)}")

    ordered = patient_df.sort_values([patient_id_column, time_column]).copy()
    ordered["delta_from_baseline"] = ordered.groupby(patient_id_column)[value_column].transform(lambda s: s - s.iloc[0])
    ordered["percent_change_from_baseline"] = ordered.groupby(patient_id_column)[value_column].transform(
        lambda s: ((s - s.iloc[0]) / s.iloc[0]) * 100 if s.iloc[0] != 0 else 0.0
    )
    return ordered.reset_index(drop=True)
