from __future__ import annotations

import pandas as pd


def summarize_ct_biomarker(
    df: pd.DataFrame,
    patient_id_column: str = "patient_id",
    time_column: str = "timepoint",
    volume_column: str = "lesion_volume_mm3",
    intensity_column: str = "mean_intensity",
    response_column: str = "treatment_response",
) -> pd.DataFrame:
    """Summarize CT-derived AML biomarker changes by treatment-response group.

    This is an additive extension to the earlier package and preserves the original
    imaging similarity workflow. It is designed for same-patient CT data where each
    patient has baseline and follow-up measurements.
    """
    required_columns = {patient_id_column, time_column, volume_column, intensity_column, response_column}
    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    patient_table = df.sort_values([patient_id_column, time_column]).copy()
    patient_table[response_column] = patient_table.groupby(patient_id_column)[response_column].transform("first")

    patient_table[volume_column] = pd.to_numeric(patient_table[volume_column], errors="coerce").fillna(0.0)
    patient_table[intensity_column] = pd.to_numeric(patient_table[intensity_column], errors="coerce").fillna(0.0)

    baseline_volume = (
        patient_table.groupby(patient_id_column, as_index=False)
        .agg({volume_column: "first"})
        .rename(columns={volume_column: "baseline_volume_mm3"})
    )
    followup_volume = (
        patient_table.groupby(patient_id_column, as_index=False)
        .agg({volume_column: "last"})
        .rename(columns={volume_column: "followup_volume_mm3"})
    )
    baseline_intensity = (
        patient_table.groupby(patient_id_column, as_index=False)
        .agg({intensity_column: "first"})
        .rename(columns={intensity_column: "baseline_intensity"})
    )
    followup_intensity = (
        patient_table.groupby(patient_id_column, as_index=False)
        .agg({intensity_column: "last"})
        .rename(columns={intensity_column: "followup_intensity"})
    )
    response_map = (
        patient_table[[patient_id_column, response_column]]
        .drop_duplicates()
        .rename(columns={response_column: "response_group"})
    )

    summary = baseline_volume.merge(followup_volume, on=patient_id_column, how="inner")
    summary = summary.merge(baseline_intensity, on=patient_id_column, how="inner")
    summary = summary.merge(followup_intensity, on=patient_id_column, how="inner")
    summary = summary.merge(response_map, on=patient_id_column, how="inner")
    summary["volume_change_mm3"] = summary["followup_volume_mm3"] - summary["baseline_volume_mm3"]
    summary["intensity_change"] = summary["followup_intensity"] - summary["baseline_intensity"]

    grouped = (
        summary.groupby("response_group", as_index=False)
        .agg(
            mean_volume_change_mm3=("volume_change_mm3", "mean"),
            mean_intensity_change=("intensity_change", "mean"),
            patient_count=(patient_id_column, "count"),
        )
        .sort_values("response_group")
        .reset_index(drop=True)
    )
    return grouped


def build_ct_biomarker_signature(
    df: pd.DataFrame,
    patient_id_column: str = "patient_id",
    time_column: str = "timepoint",
    volume_column: str = "lesion_volume_mm3",
    intensity_column: str = "mean_intensity",
    response_column: str = "treatment_response",
) -> pd.DataFrame:
    """Return ranked CT biomarker signatures by treatment-response group."""
    summary = summarize_ct_biomarker(
        df=df,
        patient_id_column=patient_id_column,
        time_column=time_column,
        volume_column=volume_column,
        intensity_column=intensity_column,
        response_column=response_column,
    )
    summary["absolute_volume_change"] = summary["mean_volume_change_mm3"].abs()
    return summary.sort_values("absolute_volume_change", ascending=False).drop(columns=["absolute_volume_change"]).reset_index(drop=True)
