from __future__ import annotations

from typing import Iterable

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def _prepare_cluster_features(
    df: pd.DataFrame,
    patient_id_column: str = "patient_id",
    feature_columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Prepare a patient feature table for clustering while keeping same-patient AML data aligned."""
    if patient_id_column not in df.columns:
        raise ValueError(f"Expected a patient identifier column named '{patient_id_column}'.")

    feature_df = df.copy()
    if feature_columns is not None:
        selected = [patient_id_column, *feature_columns]
        missing = [col for col in selected if col not in feature_df.columns]
        if missing:
            raise ValueError(f"Requested feature columns are missing: {missing}")
        feature_df = feature_df[selected].copy()
    else:
        non_id = [col for col in feature_df.columns if col != patient_id_column]
        numeric = [col for col in non_id if pd.api.types.is_numeric_dtype(feature_df[col])]
        if "modality" in feature_df.columns:
            modality_dummies = pd.get_dummies(feature_df["modality"].fillna("Unknown"), prefix="modality")
            feature_df = pd.concat([feature_df[numeric], modality_dummies], axis=1)
        else:
            feature_df = feature_df[numeric]

    feature_df = feature_df.fillna(0.0)
    return feature_df


def cluster_patients(
    df: pd.DataFrame,
    patient_id_column: str = "patient_id",
    feature_columns: Iterable[str] | None = None,
    n_clusters: int = 3,
    random_state: int = 42,
) -> pd.DataFrame:
    """Cluster AML patients using standardized imaging and clinical features."""
    if df.empty:
        return pd.DataFrame(columns=[patient_id_column, "cluster"])

    patient_ids = df[patient_id_column].astype(str).tolist()
    features = _prepare_cluster_features(df, patient_id_column=patient_id_column, feature_columns=feature_columns)

    if len(features) <= 1:
        return pd.DataFrame({patient_id_column: patient_ids, "cluster": [0]})

    n_clusters = max(1, min(int(n_clusters), len(features)))
    scaled = StandardScaler().fit_transform(features)
    labels = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10).fit_predict(scaled)

    result = pd.DataFrame({patient_id_column: patient_ids, "cluster": labels.astype(int)})
    return result.sort_values(patient_id_column).reset_index(drop=True)


def summarize_cluster_outcomes(
    clustered_df: pd.DataFrame,
    outcome_df: pd.DataFrame,
    patient_id_column: str = "patient_id",
    cluster_column: str = "cluster",
    response_column: str = "treatment_response",
    outcome_column: str = "outcome",
) -> pd.DataFrame:
    """Summarize treatment-response and outcome distributions by AML patient cluster."""
    required_cluster_cols = {patient_id_column, cluster_column}
    missing_cluster_cols = required_cluster_cols - set(clustered_df.columns)
    if missing_cluster_cols:
        raise ValueError(f"Clustered dataframe is missing required columns: {sorted(missing_cluster_cols)}")

    if patient_id_column not in outcome_df.columns:
        raise ValueError(f"Outcome dataframe must include '{patient_id_column}'.")

    merged = clustered_df[[patient_id_column, cluster_column]].merge(
        outcome_df[[patient_id_column] + ([response_column] if response_column in outcome_df.columns else []) + ([outcome_column] if outcome_column in outcome_df.columns else [])],
        on=patient_id_column,
        how="inner",
    )

    if merged.empty:
        return pd.DataFrame(columns=[cluster_column, "patient_count", "response_distribution", "outcome_distribution"])

    summary_rows = []
    for cluster_id, group in merged.groupby(cluster_column, sort=True):
        response_distribution = {}
        if response_column in group.columns:
            response_distribution = group[response_column].fillna("Unknown").value_counts().to_dict()

        outcome_distribution = {}
        if outcome_column in group.columns:
            outcome_distribution = group[outcome_column].fillna("Unknown").value_counts().to_dict()

        summary_rows.append(
            {
                cluster_column: int(cluster_id),
                "patient_count": int(group[patient_id_column].nunique()),
                "response_distribution": response_distribution,
                "outcome_distribution": outcome_distribution,
            }
        )

    return pd.DataFrame(summary_rows).sort_values(cluster_column).reset_index(drop=True)
