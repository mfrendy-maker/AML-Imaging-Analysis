import pandas as pd

from aml_imaging_analysis.discovery import generate_biology_report, summarize_biologic_patterns


def test_summarize_biologic_patterns_groups_by_cluster_and_response():
    df = pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P2", "P3", "P3", "P4", "P4"],
            "timepoint": [0, 1, 0, 1, 0, 1, 0, 1],
            "cluster": [0, 0, 0, 0, 1, 1, 1, 1],
            "tumor_volume": [50, 20, 40, 35, 60, 55, 30, 20],
            "treatment_response": ["complete", "complete", "complete", "complete", "partial", "partial", "partial", "partial"],
        }
    )

    summary = summarize_biologic_patterns(df, feature_column="tumor_volume", response_column="treatment_response")

    assert set(summary["cluster"].tolist()) == {0, 1}
    assert summary[summary["cluster"] == 0]["mean_feature_change"].iloc[0] == -17.5
    assert summary[summary["cluster"] == 1]["mean_feature_change"].iloc[0] == -7.5


def test_generate_biology_report_returns_interpretable_findings():
    summary = pd.DataFrame(
        {
            "cluster": [0, 1],
            "patient_count": [2, 2],
            "mean_feature_change": [-15.0, -5.0],
            "response_distribution": [{"complete": 2}, {"partial": 2}],
        }
    )

    report = generate_biology_report(summary)

    assert "Cluster 0" in report["summary"]
    assert report["findings"][0].startswith("Cluster 0")
