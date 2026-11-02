from __future__ import annotations

from typing import Any

import pandas as pd


def generate_patient_report(similarity_matrix: pd.DataFrame, patient_df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Create a text-friendly, interpretable summary for AML patient similarity patterns."""
    if similarity_matrix.empty:
        return {
            "summary": "No patient comparisons available.",
            "top_pairs": [],
            "interpretable_findings": [],
        }

    if patient_df is None:
        patient_df = pd.DataFrame(index=similarity_matrix.index)

    pair_summary = []
    for i, patient_a in enumerate(similarity_matrix.index):
        for j, patient_b in enumerate(similarity_matrix.columns):
            if i >= j:
                continue
            pair_summary.append(
                {
                    "patient_a": patient_a,
                    "patient_b": patient_b,
                    "similarity": float(similarity_matrix.iloc[i, j]),
                }
            )

    pair_summary = sorted(pair_summary, key=lambda item: item["similarity"], reverse=True)
    top_pairs = pair_summary[:5]

    summary_text = (
        f"AML similarity analysis includes {len(similarity_matrix.index)} patients. "
        f"The highest similarity pair is {top_pairs[0]['patient_a']} and {top_pairs[0]['patient_b']} "
        f"with a similarity score of {top_pairs[0]['similarity']:.3f}."
        if top_pairs
        else "No high-confidence patient pairings were detected."
    )

    findings = []
    if top_pairs:
        findings.append(
            f"Patients {top_pairs[0]['patient_a']} and {top_pairs[0]['patient_b']} are the most closely aligned in the current AML cohort."
        )
        if top_pairs[0]["similarity"] > 0.9:
            findings.append("These patients exhibit near-identical imaging profile characteristics, suggesting a highly similar AML pattern.")
        elif top_pairs[0]["similarity"] > 0.7:
            findings.append("This match suggests a moderate imaging similarity pattern among AML cases.")
        else:
            findings.append("This relationship indicates a weaker but still notable resemblance between matched AML cases.")

    if patient_df is not None and not patient_df.empty:
        modality_counts = patient_df.get("modality", pd.Series([], dtype="object")).value_counts().to_dict()
        if modality_counts:
            dominant_modality = max(modality_counts.items(), key=lambda item: item[1])[0]
            findings.append(f"The dominant imaging modality in the cohort is {dominant_modality}.")

    return {
        "summary": summary_text,
        "top_pairs": top_pairs,
        "interpretable_findings": findings,
    }
