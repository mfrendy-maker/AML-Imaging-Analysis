import pandas as pd

from aml_imaging_analysis.clinical import create_clinical_outcome_table, summarize_clinical_outcomes
from aml_imaging_analysis.longitudinal import compute_longitudinal_change


def test_create_clinical_outcome_table_keeps_same_patients():
    cohort = pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2"],
            "modality": ["CT", "CT", "MR"],
            "treatment_response": ["complete", "complete", "partial"],
            "outcome": ["remission", "remission", "progression"],
        }
    )

    outcome_table = create_clinical_outcome_table(cohort)

    assert sorted(outcome_table["patient_id"].tolist()) == ["P1", "P2"]
    assert outcome_table["treatment_response"].notna().all()


def test_compute_longitudinal_change_tracks_patient_delta():
    data = pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P2"],
            "timepoint": [0, 1, 0, 1],
            "tumor_volume": [20, 15, 25, 10],
        }
    )

    changed = compute_longitudinal_change(data, "tumor_volume")

    assert changed["delta_from_baseline"].tolist() == [0, -5, 0, -15]
    assert changed["percent_change_from_baseline"].tolist() == [0.0, -25.0, 0.0, -60.0]
