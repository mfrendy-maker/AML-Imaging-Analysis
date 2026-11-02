from __future__ import annotations

from typing import Any

import pandas as pd


def summarize_biologic_patterns(
    df: pd.DataFrame,
    feature_column: str,
    response_column: str = "treatment_response",
    patient_id_column: str = "patient_id",
    time_column: str = "timepoint",
    cluster_column: str = "cluster",
) -> pd.DataFrame:
    """Summarize longitudinal AML feature shifts by patient cluster and response pattern."""
    required = {patient_id_column, response_column, time_column, feature_column}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    working = df.copy()
    working = working.sort_values([patient_id_column, time_column]).reset_index(drop=True)
    working[feature_column] = pd.to_numeric(working[feature_column], errors="coerce").fillna(0.0)

    patient_level = (
        working.groupby([patient_id_column, cluster_column] if cluster_column in working.columns else patient_id_column, as_index=False)
        .agg(
            baseline_value=(feature_column, "first"),
            followup_value=(feature_column, "last"),
            response_group=(response_column, "first"),
        )
    )
    patient_level["feature_change"] = patient_level["followup_value"] - patient_level["baseline_value"]

    if cluster_column not in patient_level.columns:
        grouped = patient_level.groupby("response_group", as_index=False)
        summary = grouped.agg(
            patient_count=(patient_id_column, "count"),
            mean_feature_change=("feature_change", "mean"),
            response_distribution=("response_group", lambda values: dict(values.value_counts().to_dict())),
        )
        summary = summary.rename(columns={"response_group": cluster_column})
    else:
        grouped = patient_level.groupby(cluster_column, as_index=False)
        summary = grouped.agg(
            patient_count=(patient_id_column, "count"),
            mean_feature_change=("feature_change", "mean"),
            response_distribution=("response_group", lambda values: dict(values.value_counts().to_dict())),
        )

    return summary.sort_values(cluster_column, kind="mergesort").reset_index(drop=True)


def generate_biology_report(summary_df: pd.DataFrame, group_column: str = "cluster") -> dict[str, Any]:
    """Produce a human-readable AML biological discovery summary from cluster-level consequences."""
    if summary_df.empty:
        return {"summary": "No AML biological patterns were discovered.", "findings": []}

    top_group = summary_df.assign(abs_change=summary_df["mean_feature_change"].abs()).sort_values("abs_change", ascending=False).iloc[0]
    summary = (
        f"AML biological discovery identifies Cluster {int(top_group[group_column])} as the strongest response-associated pattern, "
        f"with a mean feature change of {top_group['mean_feature_change']:.2f} across {int(top_group['patient_count'])} patients."
    )

    findings = []
    for _, row in summary_df.sort_values(group_column).iterrows():
        cluster_label = int(row[group_column])
        response_summary = row.get("response_distribution", {})
        response_text = ", ".join(f"{key}={value}" for key, value in response_summary.items()) if isinstance(response_summary, dict) else str(response_summary)
        findings.append(
            f"Cluster {cluster_label} includes {int(row['patient_count'])} patients; mean feature change {row['mean_feature_change']:.2f}; response mix: {response_text}."
        )

    return {"summary": summary, "findings": findings}
