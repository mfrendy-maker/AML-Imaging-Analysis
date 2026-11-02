import pandas as pd

from aml_imaging_analysis.clustering import cluster_patients, summarize_cluster_outcomes


def test_cluster_patients_assigns_patient_groups():
    df = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4", "P5", "P6"],
            "modality": ["CT", "MR", "CT", "MR", "CT", "MR"],
            "study_count": [2, 8, 2, 8, 2, 8],
            "series_count": [5, 40, 5, 40, 5, 40],
            "image_count": [200, 900, 220, 950, 210, 920],
        }
    )

    clusters = cluster_patients(df, n_clusters=2)

    assert sorted(clusters["patient_id"].tolist()) == sorted(df["patient_id"].tolist())
    assert set(clusters["cluster"].unique()) == {0, 1}


def test_summarize_cluster_outcomes_reports_response_by_group():
    clustered = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4"],
            "cluster": [0, 0, 1, 1],
        }
    )
    outcomes = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4"],
            "treatment_response": ["complete", "complete", "partial", "partial"],
            "outcome": ["remission", "remission", "progression", "progression"],
        }
    )

    summary = summarize_cluster_outcomes(clustered, outcomes)

    assert summary["cluster"].tolist() == [0, 1]
    assert summary["patient_count"].sum() == 4
    assert summary["response_distribution"].iloc[0]["complete"] == 2
