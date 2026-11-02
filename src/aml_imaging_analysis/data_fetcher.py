from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

TCIA_BASE_URL = "https://services.cancerimagingarchive.net/nbia-api/services/v1"


def _fetch_json(url: str) -> Any:
    response = requests.get(url, timeout=60, headers={"User-Agent": "AML-Imaging-Analysis/0.1"})
    response.raise_for_status()
    return response.json()


def _patient_series_summary(series_records: list[dict]) -> list[dict]:
    by_patient: dict[str, list[dict]] = {}
    for record in series_records:
        patient_id = record.get("PatientID") or record.get("patient_id")
        if patient_id is None:
            continue
        by_patient.setdefault(patient_id, []).append(record)

    summary_rows: list[dict] = []
    for patient_id, records in sorted(by_patient.items()):
        study_ids = {record.get("StudyInstanceUID") for record in records if record.get("StudyInstanceUID")}
        modality_counts: dict[str, int] = {}
        for record in records:
            modality = record.get("Modality") or "Unknown"
            modality_counts[modality] = modality_counts.get(modality, 0) + 1

        summary_rows.append(
            {
                "patient_id": patient_id,
                "study_count": len(study_ids),
                "series_count": len(records),
                "modality": sorted(modality_counts, key=modality_counts.get, reverse=True)[0] if modality_counts else "Unknown",
                "modalities": modality_counts,
                "image_count": sum(int(record.get("ImageCount") or 0) for record in records),
            }
        )
    return summary_rows


def fetch_collection_snapshot(collection_name: str = "CMB-AML", limit_patients: int | None = None) -> dict[str, Any]:
    patient_url = f"{TCIA_BASE_URL}/getPatient?Collection={collection_name}"
    patient_records = _fetch_json(patient_url)
    if limit_patients is not None:
        patient_records = patient_records[:limit_patients]

    series_url = f"{TCIA_BASE_URL}/getSeries?Collection={collection_name}"
    series_records = _fetch_json(series_url)

    patient_ids = {record.get("PatientId") or record.get("PatientID") for record in patient_records if record.get("PatientId") or record.get("PatientID")}
    filtered_series = [record for record in series_records if (record.get("PatientID") or record.get("PatientId")) in patient_ids]
    patient_summary = _patient_series_summary(filtered_series)

    snapshot = {
        "collection": collection_name,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "patient_count": len(patient_records),
        "patients": patient_summary,
        "patient_ids": sorted(patient_ids),
    }
    return snapshot


def persist_collection_snapshot(snapshot: dict[str, Any], output_path: str | Path = "data/collection_snapshot.json") -> Path:
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as outfile:
        json.dump(snapshot, outfile, indent=2)
    return target_path
