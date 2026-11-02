import pandas as pd

from aml_imaging_analysis.ct_imaging import summarize_ct_biomarker


def test_summarize_ct_biomarker_tracks_patient_volume_change():
    df = pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P2"],
            "timepoint": [0, 1, 0, 1],
            "lesion_volume_mm3": [80.0, 45.0, 70.0, 78.0],
            "mean_intensity": [120.0, 90.0, 100.0, 110.0],
            "treatment_response": ["complete", "complete", "partial", "partial"],
        }
    )

    summary = summarize_ct_biomarker(df)

    assert set(summary["response_group"].tolist()) == {"complete", "partial"}
    assert summary["volume_change_mm3"].loc[summary["response_group"] == "complete"].iloc[0] == -35.0
    assert summary["intensity_change"].loc[summary["response_group"] == "partial"].iloc[0] == 10.0
