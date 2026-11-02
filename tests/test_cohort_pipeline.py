import pandas as pd

from aml_imaging_analysis.cohort import build_patient_cohort, merge_same_patient_records


def test_merge_same_patient_records_restricts_to_common_patients():
    imaging = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3", "P4"],
            "modality": ["CT", "MR", "CT", "CT"],
            "study_count": [2, 1, 3, 2],
        }
    )
    pathology = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P3"],
            "slide_count": [5, 4, 6],
            "pathology_label": ["AML-A", "AML-B", "AML-A"],
        }
    )
    clinical = pd.DataFrame(
        {
            "patient_id": ["P1", "P2", "P4"],
            "treatment_response": ["complete", "partial", "stable"],
        }
    )

    merged = merge_same_patient_records(imaging, pathology, clinical)

    assert list(merged["patient_id"]) == ["P1", "P2"]
    assert merged.shape[1] >= 6


def test_build_patient_cohort_creates_summary_counts():
    imaging = pd.DataFrame(
        {
            "patient_id": ["P1", "P2"],
            "modality": ["CT", "MR"],
            "study_count": [2, 1],
        }
    )
    pathology = pd.DataFrame(
        {
            "patient_id": ["P1", "P2"],
            "slide_count": [5, 3],
        }
    )

    cohort = build_patient_cohort(imaging, pathology)

    assert cohort["patient_count"] == 2
    assert cohort["modality_counts"]["CT"] == 1
    assert cohort["modality_counts"]["MR"] == 1
