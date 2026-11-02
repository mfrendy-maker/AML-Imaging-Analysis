from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .analysis import build_patient_similarity_matrix, summarize_patient_similarity
from .data_fetcher import fetch_collection_snapshot, persist_collection_snapshot


def _create_similarity_outputs(snapshot: dict, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = snapshot.get("patients", [])
    if not rows:
        raise ValueError("No patient summary rows were found in the collection snapshot.")

    feature_table = pd.DataFrame(rows)
    feature_table = feature_table.rename(columns={"patient_id": "patient_id"})

    similarity_matrix = build_patient_similarity_matrix(feature_table)
    summary = summarize_patient_similarity(similarity_matrix)

    output_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = output_dir / "patient_similarity_matrix.csv"
    summary_path = output_dir / "patient_similarity_summary.csv"

    similarity_matrix.to_csv(matrix_path)
    summary.to_csv(summary_path, index=False)
    return similarity_matrix, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieve and analyze AML imaging similarity patterns.")
    parser.add_argument("--collection", default="CMB-AML", help="TCIA collection name to query.")
    parser.add_argument("--output-dir", default="data", help="Directory used for downloaded metadata and analysis outputs.")
    parser.add_argument("--limit-patients", type=int, default=None, help="Optional cap on number of patients to fetch.")
    args = parser.parse_args()

    snapshot = fetch_collection_snapshot(collection_name=args.collection, limit_patients=args.limit_patients)
    persist_collection_snapshot(snapshot, Path(args.output_dir) / "collection_snapshot.json")
    similarity_matrix, similarity_summary = _create_similarity_outputs(snapshot, Path(args.output_dir))

    print(f"Collection: {snapshot['collection']}")
    print(f"Patients: {len(snapshot['patients'])}")
    print(f"Similarity matrix saved to: {Path(args.output_dir) / 'patient_similarity_matrix.csv'}")
    print(f"Top similarity pair: {similarity_summary.head(1).to_dict(orient='records')[0] if not similarity_summary.empty else 'none'}")


if __name__ == "__main__":
    main()
