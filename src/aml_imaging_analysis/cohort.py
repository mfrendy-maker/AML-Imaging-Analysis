from __future__ import annotations

from typing import Iterable

import pandas as pd


def merge_same_patient_records(*tables: pd.DataFrame, patient_id_column: str = "patient_id") -> pd.DataFrame:
    """Intersect multiple patient-level tables on the same patient IDs.

    Each table is expected to contain at least a `patient_id` column, and optional
    `timepoint` or `visit` data can be used to align longitudinal records.
    """
    if not tables:
        raise ValueError("At least one patient-level dataframe must be provided.")

    cleaned_tables: list[pd.DataFrame] = []
    for table in tables:
        if table.empty:
            continue
        if patient_id_column not in table.columns:
            raise ValueError(f"Expected a '{patient_id_column}' column in every provided dataframe.")
        frame = table.copy()
        frame[patient_id_column] = frame[patient_id_column].astype(str)
        cleaned_tables.append(frame)

    if not cleaned_tables:
        return pd.DataFrame(columns=[patient_id_column])

    common_ids = set(cleaned_tables[0][patient_id_column].tolist())
    for frame in cleaned_tables[1:]:
        common_ids &= set(frame[patient_id_column].tolist())

    merged = cleaned_tables[0][cleaned_tables[0][patient_id_column].isin(common_ids)].copy()
    for idx, frame in enumerate(cleaned_tables[1:], start=1):
        candidate = frame[frame[patient_id_column].isin(common_ids)].copy()
        join_columns = [patient_id_column]
        if "timepoint" in merged.columns and "timepoint" in candidate.columns:
            join_columns.append("timepoint")
        elif "visit" in merged.columns and "visit" in candidate.columns:
            join_columns.append("visit")

        merged = merged.merge(candidate, on=join_columns, how="inner", suffixes=("", f"_{idx}"))

    return merged.sort_values(patient_id_column).reset_index(drop=True)


def build_patient_cohort(*tables: pd.DataFrame, patient_id_column: str = "patient_id") -> dict:
    """Build a same-patient AML cohort summary used for patient-matched imaging analyses."""
    merged = merge_same_patient_records(*tables, patient_id_column=patient_id_column)
    if merged.empty:
        return {
            "patient_count": 0,
            "patient_ids": [],
            "modality_counts": {},
            "summary": "No same-patient AML cohort was found.",
            "cohort": merged,
        }

    modality_counts: dict[str, int] = {}
    if "modality" in merged.columns:
        modality_counts = merged["modality"].astype(str).value_counts().to_dict()

    return {
        "patient_count": len(merged[patient_id_column].unique()),
        "patient_ids": sorted(merged[patient_id_column].unique().tolist()),
        "modality_counts": modality_counts,
        "summary": (
            f"Same-patient AML cohort contains {len(merged[patient_id_column].unique())} patients "
            f"with an imaging modality distribution of {modality_counts}."
        ),
        "cohort": merged,
    }
