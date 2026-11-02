from __future__ import annotations

import pandas as pd


def summarize_response_features(
    df: pd.DataFrame,
    feature_column: str,
    response_column: str = "treatment_response",
    patient_id_column: str = "patient_id",
    time_column: str = "timepoint",
) -> pd.DataFrame:
    """Summarize patient-level feature changes by treatment-response group.

    This supports a clinically interpretable AML analysis workflow in which imaging or
    biological measurements are compared across response categories after aligning
    all records by patient ID and longitudinal timepoint.
    """
    required_columns = {patient_id_column, response_column, time_column, feature_column}
    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    patient_table = df.sort_values([patient_id_column, time_column]).copy()
    patient_table[response_column] = patient_table.groupby(patient_id_column)[response_column].transform("first")
    patient_table[feature_column] = pd.to_numeric(patient_table[feature_column], errors="coerce").fillna(0.0)

    first_measure = (
        patient_table.groupby(patient_id_column, as_index=False)
        .agg({feature_column: "first"})
        .rename(columns={feature_column: "baseline_value"})
    )
    last_measure = (
        patient_table.groupby(patient_id_column, as_index=False)
        .agg({feature_column: "last"})
        .rename(columns={feature_column: "followup_value"})
    )
    response_map = (
        patient_table[[patient_id_column, response_column]]
        .drop_duplicates()
        .rename(columns={response_column: "response_group"})
    )

    summary = first_measure.merge(last_measure, on=patient_id_column, how="inner")
    summary = summary.merge(response_map, on=patient_id_column, how="inner")
    summary["feature_change"] = summary["followup_value"] - summary["baseline_value"]

    grouped = (
        summary.groupby("response_group", as_index=False)
        .agg(mean_change=("feature_change", "mean"), patient_count=(patient_id_column, "count"))
        .sort_values("response_group")
        .reset_index(drop=True)
    )
    return grouped


def build_response_signature(
    df: pd.DataFrame,
    feature_column: str,
    response_column: str = "treatment_response",
    patient_id_column: str = "patient_id",
    time_column: str = "timepoint",
) -> pd.DataFrame:
    """Return a ranked AML response signature highlighting average feature changes by response group."""
    summary = summarize_response_features(
        df=df,
        feature_column=feature_column,
        response_column=response_column,
        patient_id_column=patient_id_column,
        time_column=time_column,
    )
    summary["abs_mean_change"] = summary["mean_change"].abs()
    return summary.sort_values("abs_mean_change", ascending=False).drop(columns=["abs_mean_change"]).reset_index(drop=True)
