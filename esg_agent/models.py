"""Data models for ESG dataset using dataclasses."""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ESGField:
    """A single ESG data field with value, unit, confidence, and source."""
    value: object = "missing"
    unit: str = ""
    confidence: Optional[str] = None  # "High", "Medium", "Low", or None
    source: str = ""

    def is_missing(self) -> bool:
        return self.value == "missing" or self.value is None


@dataclass
class CompanyProfile:
    name: ESGField = field(default_factory=ESGField)
    industry: ESGField = field(default_factory=ESGField)
    headquarters: ESGField = field(default_factory=ESGField)
    reporting_year: ESGField = field(default_factory=ESGField)


@dataclass
class GHGEmissions:
    scope_1: ESGField = field(default_factory=lambda: ESGField(unit="tCO2e"))
    scope_2: ESGField = field(default_factory=lambda: ESGField(unit="tCO2e"))
    scope_3: ESGField = field(default_factory=lambda: ESGField(unit="tCO2e"))
    total: ESGField = field(default_factory=lambda: ESGField(unit="tCO2e"))


@dataclass
class Energy:
    total_consumption: ESGField = field(default_factory=lambda: ESGField(unit="MWh"))
    renewable_energy_pct: ESGField = field(default_factory=lambda: ESGField(unit="%"))


@dataclass
class ClimateTargets:
    net_zero_year: ESGField = field(default_factory=ESGField)
    interim_targets: ESGField = field(default_factory=ESGField)
    science_based_targets: ESGField = field(default_factory=ESGField)


@dataclass
class ClimateRisks:
    physical_risks: ESGField = field(default_factory=ESGField)
    transition_risks: ESGField = field(default_factory=ESGField)


@dataclass
class Governance:
    board_oversight: ESGField = field(default_factory=ESGField)
    esg_committees: ESGField = field(default_factory=ESGField)
    climate_linked_incentives: ESGField = field(default_factory=ESGField)


@dataclass
class Scope3Breakdown:
    purchased_goods_and_services: ESGField = field(default_factory=lambda: ESGField(unit="tCO2e"))
    transport_and_distribution: ESGField = field(default_factory=lambda: ESGField(unit="tCO2e"))
    use_of_sold_products: ESGField = field(default_factory=lambda: ESGField(unit="tCO2e"))
    end_of_life: ESGField = field(default_factory=lambda: ESGField(unit="tCO2e"))


@dataclass
class DataQuality:
    completeness_pct: float = 0.0
    fields_missing: list = field(default_factory=list)
    confidence_scores: dict = field(default_factory=dict)


@dataclass
class ESGDataset:
    company_profile: CompanyProfile = field(default_factory=CompanyProfile)
    ghg_emissions: GHGEmissions = field(default_factory=GHGEmissions)
    energy: Energy = field(default_factory=Energy)
    climate_targets: ClimateTargets = field(default_factory=ClimateTargets)
    climate_risks: ClimateRisks = field(default_factory=ClimateRisks)
    governance: Governance = field(default_factory=Governance)
    scope3_breakdown: Scope3Breakdown = field(default_factory=Scope3Breakdown)
    data_quality: DataQuality = field(default_factory=DataQuality)
    source_references: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
