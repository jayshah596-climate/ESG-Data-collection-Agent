"""Module 5: Manual Data Integration - Template generation and data merging."""

import json
from dataclasses import fields as dc_fields
from esg_agent.models import ESGDataset, ESGField


# Field descriptions for the manual input template
FIELD_DESCRIPTIONS = {
    "company_profile.name": "Legal company name",
    "company_profile.industry": "Primary industry/sector (e.g., Technology, Energy, Manufacturing)",
    "company_profile.headquarters": "City, Country of headquarters",
    "company_profile.reporting_year": "Fiscal/reporting year (e.g., 2024)",
    "ghg_emissions.scope_1": "Direct GHG emissions",
    "ghg_emissions.scope_2": "Indirect energy-related GHG emissions",
    "ghg_emissions.scope_3": "Other indirect GHG emissions (value chain)",
    "ghg_emissions.total": "Total GHG emissions (Scope 1+2+3)",
    "energy.total_consumption": "Total energy consumed",
    "energy.renewable_energy_pct": "Percentage of energy from renewable sources",
    "climate_targets.net_zero_year": "Target year to achieve net-zero emissions",
    "climate_targets.interim_targets": "Interim emission reduction targets (e.g., 50% by 2030)",
    "climate_targets.science_based_targets": "Science-Based Target details or SBTi status",
    "climate_risks.physical_risks": "Physical climate risks identified (e.g., flooding, drought)",
    "climate_risks.transition_risks": "Transition risks identified (e.g., carbon pricing, policy)",
    "governance.board_oversight": "Board-level ESG/climate oversight details",
    "governance.esg_committees": "ESG/sustainability committee details",
    "governance.climate_linked_incentives": "Climate-linked executive incentives/compensation",
    "scope3_breakdown.purchased_goods_and_services": "Scope 3 Cat 1: Purchased goods & services emissions",
    "scope3_breakdown.transport_and_distribution": "Scope 3 Cat 4/9: Transport & distribution emissions",
    "scope3_breakdown.use_of_sold_products": "Scope 3 Cat 11: Use of sold products emissions",
    "scope3_breakdown.end_of_life": "Scope 3 Cat 12: End-of-life treatment emissions",
}

FIELD_UNITS = {
    "ghg_emissions.scope_1": "tCO2e",
    "ghg_emissions.scope_2": "tCO2e",
    "ghg_emissions.scope_3": "tCO2e",
    "ghg_emissions.total": "tCO2e",
    "energy.total_consumption": "MWh",
    "energy.renewable_energy_pct": "%",
    "scope3_breakdown.purchased_goods_and_services": "tCO2e",
    "scope3_breakdown.transport_and_distribution": "tCO2e",
    "scope3_breakdown.use_of_sold_products": "tCO2e",
    "scope3_breakdown.end_of_life": "tCO2e",
}


def generate_template(dataset: ESGDataset = None) -> dict:
    """Generate a manual input template, highlighting missing fields if dataset provided."""
    template = {"instructions": "Fill in the 'value' field for each item. Leave blank if unknown.", "fields": []}

    for path, description in FIELD_DESCRIPTIONS.items():
        is_missing = True
        current_value = ""

        if dataset:
            section_name, field_name = path.split(".")
            section_obj = getattr(dataset, section_name, None)
            if section_obj:
                field_obj = getattr(section_obj, field_name, None)
                if isinstance(field_obj, ESGField):
                    is_missing = field_obj.is_missing()
                    if not is_missing:
                        current_value = field_obj.value

        template["fields"].append({
            "field_path": path,
            "description": description,
            "expected_unit": FIELD_UNITS.get(path, ""),
            "current_value": current_value if not is_missing else "",
            "status": "missing - please fill" if is_missing else "auto-filled",
            "value": "" if is_missing else current_value,
        })

    return template


def save_template(template: dict, path: str):
    """Save template to JSON file."""
    with open(path, "w") as f:
        json.dump(template, f, indent=2, default=str)
    print(f"[INFO] Manual input template saved to {path}")


def load_manual_input(path: str) -> dict:
    """Load completed manual input from JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def merge_manual_data(dataset: ESGDataset, manual_data: dict) -> ESGDataset:
    """Merge manually provided data into the ESG dataset."""
    fields_list = manual_data.get("fields", [])
    merged_count = 0

    for item in fields_list:
        value = item.get("value", "")
        if not value or value == "":
            continue

        path = item.get("field_path", "")
        if "." not in path:
            continue

        section_name, field_name = path.split(".", 1)
        section_obj = getattr(dataset, section_name, None)
        if not section_obj:
            continue

        field_obj = getattr(section_obj, field_name, None)
        if not isinstance(field_obj, ESGField):
            continue

        # Only overwrite if currently missing or if manual data is being forced
        if field_obj.is_missing():
            field_obj.value = value
            field_obj.unit = item.get("expected_unit", field_obj.unit)
            field_obj.confidence = "High"
            field_obj.source = "Manual input"
            setattr(section_obj, field_name, field_obj)
            merged_count += 1

    print(f"[INFO] Merged {merged_count} manually provided fields")
    return dataset
