from __future__ import annotations

from typing import Any

import pandas as pd


def create_clinical_outcome_table(
    cohort_df: pd.DataFrame,
    response_column: str = "treatment_response",
    outcome_column: str = "outcome",
    patient_id_column: str = "patient_id",
) -> pd.DataFrame:
    """Create a patient-level outcome table for same-patient AML analyses."""
    if patient_id_column not in cohort_df.columns:
        raise ValueError(f"Expected a '{patient_id_column}' column for patient matching.")

    table = cohort_df[[patient_id_column]].drop_duplicates().copy()

    if response_column in cohort_df.columns:
        response_map = cohort_df[[patient_id_column, response_column]].drop_duplicates()
        table = table.merge(response_map, on=patient_id_column, how="left")

    if outcome_column in cohort_df.columns:
        outcome_map = cohort_df[[patient_id_column, outcome_column]].drop_duplicates()
        table = table.merge(outcome_map, on=patient_id_column, how="left")

    return table.reset_index(drop=True)


def summarize_clinical_outcomes(clinical_df: pd.DataFrame, response_column: str = "treatment_response") -> dict[str, Any]:
    """Summarize patient treatment response categories and their frequencies."""
    if clinical_df.empty:
        return {"response_counts": {}, "summary": "No clinical outcomes recorded."}

    response_counts = clinical_df[response_column].fillna("Unknown").value_counts().to_dict() if response_column in clinical_df.columns else {}
    return {
        "response_counts": response_counts,
        "summary": (
            f"Clinical outcome summary: {response_counts}"
        ),
    }
