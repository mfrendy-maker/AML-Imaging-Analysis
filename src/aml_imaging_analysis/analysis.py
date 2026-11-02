from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler


def _build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    feature_df = df.copy()
    numeric_columns = ["study_count", "series_count", "image_count"]
    for column in numeric_columns:
        feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce").fillna(0)

    if "modality" in feature_df.columns:
        modality_dummies = pd.get_dummies(feature_df["modality"].fillna("Unknown"), prefix="modality")
        feature_df = pd.concat([feature_df[numeric_columns], modality_dummies], axis=1)
    else:
        feature_df = feature_df[numeric_columns]

    return feature_df.fillna(0)


def build_patient_similarity_matrix(df: pd.DataFrame, patient_id_column: str = "patient_id") -> pd.DataFrame:
    """Create a patient-by-patient similarity matrix using cosine similarity.

    The patient table is expected to include basic modality and imaging counts per patient.
    """
    if patient_id_column not in df.columns:
        raise ValueError(f"Expected a patient identifier column named '{patient_id_column}'.")

    patient_df = df[[patient_id_column]].copy()
    patient_df = patient_df.join(_build_feature_matrix(df))

    scaled_features = StandardScaler().fit_transform(patient_df.drop(columns=[patient_id_column]))
    similarity = cosine_similarity(scaled_features)

    patient_ids = patient_df[patient_id_column].tolist()
    matrix = pd.DataFrame(similarity, index=patient_ids, columns=patient_ids)
    matrix = matrix.clip(lower=0.0, upper=1.0)
    return matrix


def summarize_patient_similarity(similarity_matrix: pd.DataFrame) -> pd.DataFrame:
    """Flatten a similarity matrix into ranked patient-pair associations."""
    if similarity_matrix.empty:
        return pd.DataFrame(columns=["patient_a", "patient_b", "similarity"])

    rows: list[dict[str, object]] = []
    for i, patient_a in enumerate(similarity_matrix.index):
        for j, patient_b in enumerate(similarity_matrix.columns):
            if i == j:
                continue
            if j <= i:
                continue
            similarity = float(similarity_matrix.iloc[i, j])
            rows.append({"patient_a": patient_a, "patient_b": patient_b, "similarity": similarity})

    summary = pd.DataFrame(rows)
    if summary.empty:
        return summary
    return summary.sort_values("similarity", ascending=False).reset_index(drop=True)
