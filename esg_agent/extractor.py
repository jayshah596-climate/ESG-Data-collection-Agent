"""Module 2: ESG Data Extraction - Pattern-based extraction from text."""

import re
from esg_agent.models import (
    ESGField, CompanyProfile, GHGEmissions, Energy, ClimateTargets,
    ClimateRisks, Governance, Scope3Breakdown, ESGDataset,
)
from config import (
    PHYSICAL_RISK_KEYWORDS, TRANSITION_RISK_KEYWORDS,
    GOVERNANCE_KEYWORDS, SCOPE3_CATEGORIES,
)


def _find_number(pattern: str, text: str, flags=re.IGNORECASE) -> tuple:
    """Search for a numeric pattern. Returns (value_str, unit_str, snippet) or None."""
    match = re.search(pattern, text, flags)
    if match:
        groups = match.groups()
        # Get surrounding context as source snippet
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        snippet = text[start:end].strip()
        return groups, snippet
    return None


def _parse_number(value_str: str) -> float:
    """Parse a number string, handling commas and spaces."""
    cleaned = value_str.replace(",", "").replace(" ", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_company_profile(text: str, company_name: str) -> CompanyProfile:
    """Extract company profile information."""
    profile = CompanyProfile()

    # Company name is provided
    profile.name = ESGField(value=company_name, confidence="High", source="User input")

    # Try to find industry
    industry_patterns = [
        r"(?:industry|sector)[:\s]+([A-Za-z\s&,]+?)(?:\n|\.)",
        r"(?:operating in|leader in)\s+(?:the\s+)?([A-Za-z\s&]+?)(?:\s+(?:industry|sector))",
    ]
    for pat in industry_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            profile.industry = ESGField(
                value=groups[0].strip(), confidence="Medium", source=snippet
            )
            break

    # Try to find headquarters
    hq_patterns = [
        r"(?:headquartered|headquarters|based)\s+(?:in\s+)?([A-Za-z\s,]+?)(?:\n|\.)",
        r"(?:head\s*office|corporate\s*office)[:\s]+([A-Za-z\s,]+?)(?:\n|\.)",
    ]
    for pat in hq_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            profile.headquarters = ESGField(
                value=groups[0].strip(), confidence="Medium", source=snippet
            )
            break

    # Try to find reporting year
    year_patterns = [
        r"(?:reporting\s*(?:year|period)|fiscal\s*year|fy)\s*[:\s]*(\d{4})",
        r"(?:sustainability|annual|esg)\s*report\s*(\d{4})",
        r"\b(20[12]\d)\b",  # fallback: recent year
    ]
    for pat in year_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            confidence = "High" if "report" in pat.lower() or "year" in pat.lower() else "Low"
            profile.reporting_year = ESGField(
                value=groups[0].strip(), confidence=confidence, source=snippet
            )
            break

    return profile


def _extract_ghg_emissions(text: str) -> GHGEmissions:
    """Extract GHG emissions data (Scope 1, 2, 3, Total)."""
    emissions = GHGEmissions()
    text_lower = text.lower()

    scope_patterns = {
        "scope_1": [
            r"scope\s*1\s*(?:emissions?)?[\s:]+([0-9][0-9,.]*)\s*((?:mt?|kt?)?co2e?|tonnes?)",
            r"direct\s*(?:ghg\s*)?emissions?\s*(?:\(scope\s*1\))?\s*[:\s]+([0-9][0-9,.]*)\s*((?:mt?|kt?)?co2e?|tonnes?)",
        ],
        "scope_2": [
            r"scope\s*2\s*(?:emissions?)?[\s:]+([0-9][0-9,.]*)\s*((?:mt?|kt?)?co2e?|tonnes?)",
            r"indirect\s*(?:energy\s*)?(?:ghg\s*)?emissions?\s*(?:\(scope\s*2\))?\s*[:\s]+([0-9][0-9,.]*)\s*((?:mt?|kt?)?co2e?|tonnes?)",
        ],
        "scope_3": [
            r"scope\s*3\s*(?:emissions?)?[\s:]+([0-9][0-9,.]*)\s*((?:mt?|kt?)?co2e?|tonnes?)",
            r"other\s*indirect\s*emissions?\s*(?:\(scope\s*3\))?\s*[:\s]+([0-9][0-9,.]*)\s*((?:mt?|kt?)?co2e?|tonnes?)",
        ],
        "total": [
            r"total\s*(?:ghg\s*)?emissions?\s*[:\s]+([0-9][0-9,.]*)\s*((?:mt?|kt?)?co2e?|tonnes?)",
            r"(?:combined|aggregate)\s*(?:ghg\s*)?emissions?\s*[:\s]+([0-9][0-9,.]*)\s*((?:mt?|kt?)?co2e?|tonnes?)",
        ],
    }

    for field_name, patterns in scope_patterns.items():
        for pat in patterns:
            result = _find_number(pat, text)
            if result:
                groups, snippet = result
                value = _parse_number(groups[0])
                unit = groups[1].lower() if len(groups) > 1 else "tco2e"
                if value is not None:
                    esg_field = ESGField(
                        value=value, unit=unit, confidence="High", source=snippet
                    )
                    setattr(emissions, field_name, esg_field)
                    break

    return emissions


def _extract_energy(text: str) -> Energy:
    """Extract energy consumption and renewable energy percentage."""
    energy = Energy()

    # Energy consumption
    energy_patterns = [
        r"(?:total\s*)?energy\s*consumption\s*[:\s]+([0-9][0-9,.]*)\s*(mwh|gwh|tj|gj|kwh)",
        r"(?:total\s*)?energy\s*(?:use|usage)\s*[:\s]+([0-9][0-9,.]*)\s*(mwh|gwh|tj|gj|kwh)",
    ]
    for pat in energy_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            value = _parse_number(groups[0])
            if value is not None:
                energy.total_consumption = ESGField(
                    value=value, unit=groups[1].lower(), confidence="High", source=snippet
                )
                break

    # Renewable energy percentage
    renew_patterns = [
        r"renewable\s*energy\s*(?:share|percentage|proportion|mix)?\s*[:\s]*([0-9][0-9,.]*)\s*%",
        r"([0-9][0-9,.]*)\s*%\s*(?:of\s*(?:total\s*)?energy\s*(?:from|is)\s*)?renewable",
    ]
    for pat in renew_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            value = _parse_number(groups[0])
            if value is not None:
                energy.renewable_energy_pct = ESGField(
                    value=value, unit="%", confidence="High", source=snippet
                )
                break

    return energy


def _extract_climate_targets(text: str) -> ClimateTargets:
    """Extract climate targets (net zero, interim, science-based)."""
    targets = ClimateTargets()

    # Net zero target year
    nz_patterns = [
        r"net[\s-]*zero\s*(?:emissions?\s*)?(?:by|target[:\s]*|goal[:\s]*)\s*(\d{4})",
        r"(?:achieve|reach|attain)\s*net[\s-]*zero\s*(?:by\s*)?(\d{4})",
        r"carbon[\s-]*neutral\s*(?:by|target|goal)\s*(\d{4})",
    ]
    for pat in nz_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            targets.net_zero_year = ESGField(
                value=int(groups[0]), confidence="High", source=snippet
            )
            break

    # Interim targets
    interim_patterns = [
        r"reduce\s*(?:(?:ghg|carbon)\s*)?emissions?\s*(?:by\s*)?([0-9]+)\s*%\s*(?:by\s*)?(\d{4})",
        r"([0-9]+)\s*%\s*(?:reduction|decrease)\s*(?:in\s*emissions?\s*)?(?:by\s*)?(\d{4})",
    ]
    for pat in interim_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            targets.interim_targets = ESGField(
                value=f"{groups[0]}% reduction by {groups[1]}",
                confidence="High",
                source=snippet,
            )
            break

    # Science-based targets
    sbt_patterns = [
        r"(science[\s-]*based\s*targets?\s*(?:initiative|sbti)?[^.]*\.)",
        r"(sbti[\s-]*(?:approved|validated|committed|aligned)[^.]*\.)",
    ]
    for pat in sbt_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            targets.science_based_targets = ESGField(
                value=groups[0].strip(), confidence="Medium", source=snippet
            )
            break

    return targets


def _extract_climate_risks(text: str) -> ClimateRisks:
    """Extract physical and transition climate risks."""
    risks = ClimateRisks()
    text_lower = text.lower()

    # Physical risks
    found_physical = []
    for keyword in PHYSICAL_RISK_KEYWORDS:
        if keyword in text_lower:
            # Get context around the keyword
            idx = text_lower.index(keyword)
            start = max(0, idx - 100)
            end = min(len(text), idx + 100)
            found_physical.append(keyword)

    if found_physical:
        risks.physical_risks = ESGField(
            value=found_physical,
            confidence="Medium",
            source=f"Keywords found: {', '.join(found_physical)}",
        )

    # Transition risks
    found_transition = []
    for keyword in TRANSITION_RISK_KEYWORDS:
        if keyword in text_lower:
            found_transition.append(keyword)

    if found_transition:
        risks.transition_risks = ESGField(
            value=found_transition,
            confidence="Medium",
            source=f"Keywords found: {', '.join(found_transition)}",
        )

    return risks


def _extract_governance(text: str) -> Governance:
    """Extract governance-related ESG data."""
    gov = Governance()
    text_lower = text.lower()

    for field_name, keywords in GOVERNANCE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                idx = text_lower.index(keyword)
                start = max(0, idx - 50)
                end = min(len(text), idx + 200)
                snippet = text[start:end].strip()

                esg_field = ESGField(
                    value="Yes - disclosed",
                    confidence="Medium",
                    source=snippet,
                )
                setattr(gov, field_name, esg_field)
                break

    return gov


def _extract_scope3(text: str) -> Scope3Breakdown:
    """Extract Scope 3 emissions breakdown by category."""
    scope3 = Scope3Breakdown()
    text_lower = text.lower()

    for field_name, keywords in SCOPE3_CATEGORIES.items():
        for keyword in keywords:
            # Try to find a number near the keyword
            pattern = rf"{re.escape(keyword)}[^0-9]*?([0-9][0-9,.]*)\s*((?:mt?|kt?)?co2e?|tonnes?)"
            result = _find_number(pattern, text_lower)
            if result:
                groups, snippet = result
                value = _parse_number(groups[0])
                if value is not None:
                    esg_field = ESGField(
                        value=value,
                        unit=groups[1] if len(groups) > 1 else "tco2e",
                        confidence="Medium",
                        source=snippet,
                    )
                    setattr(scope3, field_name, esg_field)
                    break

    return scope3


def extract_esg_data(collected_data: dict) -> ESGDataset:
    """Main extraction function: extract all ESG data from collected text."""
    text = collected_data.get("combined_text", "")
    company_name = collected_data.get("company_name", "Unknown")

    dataset = ESGDataset()
    dataset.company_profile = _extract_company_profile(text, company_name)
    dataset.ghg_emissions = _extract_ghg_emissions(text)
    dataset.energy = _extract_energy(text)
    dataset.climate_targets = _extract_climate_targets(text)
    dataset.climate_risks = _extract_climate_risks(text)
    dataset.governance = _extract_governance(text)
    dataset.scope3_breakdown = _extract_scope3(text)

    # Track sources
    sources = []
    if collected_data.get("web_text"):
        sources.append(f"Website: {collected_data.get('url', 'provided URL')}")
    if collected_data.get("pdf_text"):
        sources.append(f"PDF: {collected_data.get('pdf_path', 'provided PDF')}")
    dataset.source_references = sources

    print(f"[INFO] ESG data extraction complete for {company_name}")
    return dataset
