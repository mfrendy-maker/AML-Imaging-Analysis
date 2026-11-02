import pandas as pd

from aml_imaging_analysis.analysis import build_patient_similarity_matrix
from aml_imaging_analysis.reporting import generate_patient_report


def test_generate_patient_report_returns_expected_sections():
    df = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3"],
            "modality": ["CT", "MR", "CT"],
            "study_count": [3, 2, 3],
            "series_count": [10, 8, 11],
            "image_count": [450, 520, 460],
        }
    )

    similarity = build_patient_similarity_matrix(df)
    report = generate_patient_report(similarity, df)

    assert "summary" in report
    assert "top_pairs" in report
    assert "interpretable_findings" in report
    assert isinstance(report["top_pairs"], list)
    assert len(report["top_pairs"]) >= 1
