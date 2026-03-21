"""Module 6: Structured JSON Output."""

import json
from esg_agent.models import ESGDataset


def dataset_to_dict(dataset: ESGDataset) -> dict:
    """Convert ESGDataset to a clean nested dictionary."""
    return dataset.to_dict()


def export_json(dataset: ESGDataset, output_path: str) -> str:
    """Export ESG dataset to JSON file."""
    data = dataset_to_dict(dataset)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"[INFO] JSON output saved to {output_path}")
    return output_path
