"""Module 3: Data Standardisation - Unit conversion, normalization."""

import re
from esg_agent.models import ESGDataset, ESGField
from config import EMISSION_CONVERSIONS, ENERGY_CONVERSIONS_TO_MWH


def _convert_emissions(value, unit: str) -> tuple:
    """Convert emissions to tCO2e. Returns (converted_value, 'tCO2e')."""
    if value == "missing" or value is None:
        return value, "tCO2e"

    try:
        numeric = float(value)
    except (ValueError, TypeError):
        return value, unit

    unit_clean = unit.lower().replace(" ", "").replace("tonnes", "tco2e")
    factor = EMISSION_CONVERSIONS.get(unit_clean, 1.0)
    return round(numeric * factor, 2), "tCO2e"


def _convert_energy(value, unit: str) -> tuple:
    """Convert energy to MWh. Returns (converted_value, 'MWh')."""
    if value == "missing" or value is None:
        return value, "MWh"

    try:
        numeric = float(value)
    except (ValueError, TypeError):
        return value, unit

    unit_clean = unit.lower().replace(" ", "")
    factor = ENERGY_CONVERSIONS_TO_MWH.get(unit_clean, 1.0)
    return round(numeric * factor, 2), "MWh"


def _normalize_percentage(value) -> float:
    """Normalize percentage values: '50%' -> 50.0, '0.5' -> 50.0."""
    if value == "missing" or value is None:
        return value

    if isinstance(value, str):
        value = value.replace("%", "").replace("percent", "").strip()
        try:
            numeric = float(value)
        except ValueError:
            return value
    else:
        try:
            numeric = float(value)
        except (ValueError, TypeError):
            return value

    # If value is between 0 and 1, assume it's a decimal representation
    if 0 < numeric < 1:
        return round(numeric * 100, 2)
    return round(numeric, 2)


def _resolve_range(value) -> float:
    """Convert a range like '100-200' to its midpoint 150.0."""
    if value == "missing" or value is None:
        return value

    if isinstance(value, str):
        range_match = re.match(r"([0-9,.]+)\s*[-–—to]+\s*([0-9,.]+)", value)
        if range_match:
            low = float(range_match.group(1).replace(",", ""))
            high = float(range_match.group(2).replace(",", ""))
            return round((low + high) / 2, 2)

    return value


def _standardize_field(esg_field: ESGField, converter) -> ESGField:
    """Apply a converter function to an ESGField's value."""
    if esg_field.is_missing():
        return esg_field

    # Resolve ranges first
    resolved_value = _resolve_range(esg_field.value)

    converted_value, new_unit = converter(resolved_value, esg_field.unit)
    esg_field.value = converted_value
    esg_field.unit = new_unit
    return esg_field


def standardize(dataset: ESGDataset) -> ESGDataset:
    """Standardize all units in the ESG dataset."""

    # GHG Emissions → tCO2e
    ghg = dataset.ghg_emissions
    ghg.scope_1 = _standardize_field(ghg.scope_1, _convert_emissions)
    ghg.scope_2 = _standardize_field(ghg.scope_2, _convert_emissions)
    ghg.scope_3 = _standardize_field(ghg.scope_3, _convert_emissions)
    ghg.total = _standardize_field(ghg.total, _convert_emissions)

    # Energy → MWh
    energy = dataset.energy
    energy.total_consumption = _standardize_field(energy.total_consumption, _convert_energy)

    # Renewable % normalization
    if not energy.renewable_energy_pct.is_missing():
        energy.renewable_energy_pct.value = _normalize_percentage(
            energy.renewable_energy_pct.value
        )
        energy.renewable_energy_pct.unit = "%"

    # Scope 3 breakdown → tCO2e
    s3 = dataset.scope3_breakdown
    s3.purchased_goods_and_services = _standardize_field(
        s3.purchased_goods_and_services, _convert_emissions
    )
    s3.transport_and_distribution = _standardize_field(
        s3.transport_and_distribution, _convert_emissions
    )
    s3.use_of_sold_products = _standardize_field(
        s3.use_of_sold_products, _convert_emissions
    )
    s3.end_of_life = _standardize_field(s3.end_of_life, _convert_emissions)

    print("[INFO] Data standardisation complete")
    return dataset
