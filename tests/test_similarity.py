import pandas as pd

from aml_imaging_analysis.analysis import build_patient_similarity_matrix
from aml_imaging_analysis.data_fetcher import fetch_collection_snapshot


def test_build_patient_similarity_matrix():
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

    assert similarity.shape == (3, 3)
    assert similarity.iloc[0, 0] == 1.0
    assert similarity.iloc[0, 1] >= 0.0
    assert similarity.iloc[0, 1] <= 1.0


def test_fetch_collection_snapshot_returns_expected_fields():
    snapshot = fetch_collection_snapshot(collection_name="CMB-AML")

    assert "collection" in snapshot
    assert "patients" in snapshot
    assert snapshot["collection"] == "CMB-AML"
