"""Module 4: Data Validation & Quality Check."""

from dataclasses import fields as dc_fields
from esg_agent.models import ESGDataset, ESGField, DataQuality


def _get_all_esg_fields(dataset: ESGDataset) -> dict:
    """Get all ESGField instances from the dataset with their paths."""
    result = {}
    sections = [
        ("company_profile", dataset.company_profile),
        ("ghg_emissions", dataset.ghg_emissions),
        ("energy", dataset.energy),
        ("climate_targets", dataset.climate_targets),
        ("climate_risks", dataset.climate_risks),
        ("governance", dataset.governance),
        ("scope3_breakdown", dataset.scope3_breakdown),
    ]
    for section_name, section_obj in sections:
        for f in dc_fields(section_obj):
            field_val = getattr(section_obj, f.name)
            if isinstance(field_val, ESGField):
                path = f"{section_name}.{f.name}"
                result[path] = field_val
    return result


def _check_missing_fields(all_fields: dict) -> list:
    """Return list of field paths with missing values."""
    return [path for path, field in all_fields.items() if field.is_missing()]


def _check_consistency(dataset: ESGDataset) -> list:
    """Check for data inconsistencies. Returns list of warning strings."""
    warnings = []
    ghg = dataset.ghg_emissions

    # Check if scope 1+2+3 ≈ total
    scopes_available = (
        not ghg.scope_1.is_missing()
        and not ghg.scope_2.is_missing()
        and not ghg.scope_3.is_missing()
        and not ghg.total.is_missing()
    )
    if scopes_available:
        try:
            s1 = float(ghg.scope_1.value)
            s2 = float(ghg.scope_2.value)
            s3 = float(ghg.scope_3.value)
            total = float(ghg.total.value)
            calculated = s1 + s2 + s3
            if total > 0 and abs(calculated - total) / total > 0.1:
                warnings.append(
                    f"GHG total ({total}) differs from sum of scopes ({calculated}) by >10%"
                )
        except (ValueError, TypeError):
            pass

    # Check renewable percentage bounds
    renew = dataset.energy.renewable_energy_pct
    if not renew.is_missing():
        try:
            pct = float(renew.value)
            if pct < 0 or pct > 100:
                warnings.append(f"Renewable energy % ({pct}) is outside 0-100 range")
        except (ValueError, TypeError):
            pass

    # Check net zero year is in the future
    nz = dataset.climate_targets.net_zero_year
    if not nz.is_missing():
        try:
            year = int(nz.value)
            if year < 2025:
                warnings.append(f"Net zero target year ({year}) is in the past")
            if year > 2100:
                warnings.append(f"Net zero target year ({year}) seems unrealistic")
        except (ValueError, TypeError):
            pass

    return warnings


def _compute_confidence_scores(all_fields: dict) -> dict:
    """Aggregate confidence scores by section."""
    section_scores = {}
    for path, field in all_fields.items():
        section = path.split(".")[0]
        if section not in section_scores:
            section_scores[section] = {"high": 0, "medium": 0, "low": 0, "missing": 0}

        if field.is_missing():
            section_scores[section]["missing"] += 1
        elif field.confidence:
            section_scores[section][field.confidence.lower()] += 1

    return section_scores


def _compute_completeness(all_fields: dict) -> float:
    """Calculate percentage of fields with actual values."""
    total = len(all_fields)
    if total == 0:
        return 0.0
    filled = sum(1 for f in all_fields.values() if not f.is_missing())
    return round(filled / total * 100, 1)


def validate(dataset: ESGDataset) -> ESGDataset:
    """Run all validation checks and populate data_quality."""
    all_fields = _get_all_esg_fields(dataset)

    missing = _check_missing_fields(all_fields)
    warnings = _check_consistency(dataset)
    confidence_scores = _compute_confidence_scores(all_fields)
    completeness = _compute_completeness(all_fields)

    dataset.data_quality = DataQuality(
        completeness_pct=completeness,
        fields_missing=missing,
        confidence_scores=confidence_scores,
    )

    if warnings:
        print("[WARNING] Data consistency issues found:")
        for w in warnings:
            print(f"  - {w}")

    print(f"[INFO] Validation complete: {completeness}% data completeness, {len(missing)} missing fields")
    return dataset
