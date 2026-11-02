# AML Imaging Analysis

This repository contains a Python package for retrieving and analyzing the public `CMB-AML` imaging collection from the Cancer Imaging Archive (TCIA) and for revealing similarity patterns across AML patients.

## Goals

- Fetch collection metadata from the TCIA API and save it to the repository.
- Build a patient-level similarity analysis for radiology and pathology metadata.
- Provide a CLI and reusable package APIs for pattern discovery.
- Keep the project ready for GitHub-based collaboration and iterative analysis.

## Quick start

```bash
python -m pip install -e .
aml-imaging --help
```

## Collection

The project currently targets the public Cancer Moonshot Biobank – Acute Myeloid Leukemia (CMB-AML) collection available on TCIA:

- https://www.cancerimagingarchive.net/collection/cmb-aml/

## Output

Downloaded metadata is stored under `data/` and can be used for patient comparison and clustering.
