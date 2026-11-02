import pandas as pd

from aml_imaging_analysis.biomarker import summarize_response_features


def test_summarize_response_features_groups_by_patient_response():
    data = pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P2", "P3", "P3"],
            "timepoint": [0, 1, 0, 1, 0, 1],
            "tumor_volume": [50, 20, 40, 35, 60, 55],
            "treatment_response": ["complete", "complete", "partial", "partial", "stable", "stable"],
        }
    )

    summary = summarize_response_features(data, feature_column="tumor_volume", response_column="treatment_response")

    assert set(summary["response_group"].tolist()) == {"complete", "partial", "stable"}
    assert summary["mean_change"].loc[summary["response_group"] == "complete"].iloc[0] == -30.0
    assert summary["mean_change"].loc[summary["response_group"] == "partial"].iloc[0] == -5.0
