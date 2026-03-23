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
        start = max(0, match.start() - 60)
        end = min(len(text), match.end() + 60)
        snippet = text[start:end].strip()
        return groups, snippet
    return None


def _find_all_numbers(pattern: str, text: str, flags=re.IGNORECASE) -> list:
    """Find all matches for a pattern. Returns list of (groups, snippet)."""
    results = []
    for match in re.finditer(pattern, text, flags):
        groups = match.groups()
        start = max(0, match.start() - 60)
        end = min(len(text), match.end() + 60)
        snippet = text[start:end].strip()
        results.append((groups, snippet))
    return results


def _parse_number(value_str: str) -> float:
    """Parse a number string, handling commas, spaces, and multiplier words."""
    if not value_str:
        return None
    cleaned = value_str.replace(",", "").replace(" ", "").replace("\u00a0", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_company_profile(text: str, company_name: str) -> CompanyProfile:
    """Extract company profile information."""
    profile = CompanyProfile()

    # Company name is provided
    profile.name = ESGField(value=company_name, confidence="High", source="User input")

    # Try to find industry — very flexible patterns
    industry_patterns = [
        r"(?:industry|sector|segment)[:\s]+([A-Za-z\s&,/]+?)(?:\n|\.|\|)",
        r"(?:operating\s+in|leader\s+in|provider\s+of|specializ\w+\s+in)\s+(?:the\s+)?([A-Za-z\s&,]+?)(?:\s+(?:industry|sector|market|space))",
        r"(?:is\s+(?:a|an)\s+)([A-Za-z\s&,]+?)\s+(?:company|corporation|firm|enterprise|group)",
        r"(?:leading|global|major)\s+([A-Za-z\s&]+?)\s+(?:company|corporation|firm|provider)",
    ]
    for pat in industry_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            val = groups[0].strip().rstrip(",.")
            if 2 < len(val) < 80:
                profile.industry = ESGField(
                    value=val, confidence="Medium", source=snippet
                )
                break

    # Try to find headquarters — very flexible patterns
    hq_patterns = [
        r"(?:headquartered|headquarters|head\s*quarter)\s+(?:in|at)\s+([A-Za-z\s,]+?)(?:\n|\.|\|)",
        r"(?:based\s+in|located\s+in)\s+([A-Za-z\s,]+?)(?:\n|\.|\|)",
        r"(?:head\s*office|corporate\s*office|principal\s*office)[:\s]+([A-Za-z\s,]+?)(?:\n|\.|\|)",
        r"(?:offices?\s+in)\s+([A-Za-z\s,]+?)(?:\n|\.|and\s)",
    ]
    for pat in hq_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            val = groups[0].strip().rstrip(",.")
            if 2 < len(val) < 80:
                profile.headquarters = ESGField(
                    value=val, confidence="Medium", source=snippet
                )
                break

    # Try to find reporting year — flexible patterns
    year_patterns = [
        r"(?:reporting\s*(?:year|period)|fiscal\s*year|fy)\s*[:\s]*(\d{4})",
        r"(?:sustainability|annual|esg|climate|impact)\s*report\s*(?:for\s*)?(\d{4})",
        r"(\d{4})\s*(?:sustainability|annual|esg|climate|impact)\s*report",
        r"(?:in|for|during)\s+(?:fy\s*)?(\d{4})",
        r"\b(20[12]\d)\b",  # fallback: recent year
    ]
    for pat in year_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            year_val = groups[0].strip()
            try:
                yr = int(year_val)
                if 2015 <= yr <= 2030:
                    confidence = "High" if "report" in pat.lower() or "year" in pat.lower() else "Low"
                    profile.reporting_year = ESGField(
                        value=year_val, confidence=confidence, source=snippet
                    )
                    break
            except ValueError:
                continue

    return profile


# ---------------------------------------------------------------------------
# Emissions helpers
# ---------------------------------------------------------------------------

# Flexible unit pattern that matches many real-world formats
_UNIT_PAT = (
    r"(?:million\s+)?(?:metric\s+)?(?:tonnes?|tons?|t)?\s*"
    r"(?:of\s+)?(?:co2(?:\s*-?\s*e(?:quivalent)?)?|carbon\s*dioxide)"
    r"|(?:mt?|kt?|t)\s*co2e?"
    r"|tco2e?"
    r"|co2e?"
)

# Flexible number pattern (handles commas, decimals, and "million/billion" words)
_NUM_PAT = r"([0-9][0-9,.\s]*[0-9]|[0-9])"

# Optional multiplier words after number
_MULT_PAT = r"(?:\s*(?:million|billion|thousand|mn|bn|k))?"


def _extract_emission_value(text_segment: str) -> tuple:
    """Try to extract a numeric emission value from a text segment.
    Returns (value_float, unit_str, snippet) or None.
    """
    # Pattern: number + optional multiplier + unit
    pat = rf"{_NUM_PAT}{_MULT_PAT}\s*(?:{_UNIT_PAT})"
    result = _find_number(pat, text_segment)
    if result:
        groups, snippet = result
        val = _parse_number(groups[0])
        if val is not None:
            # Handle multiplier words in snippet
            snip_lower = snippet.lower()
            if "million" in snip_lower or " mn" in snip_lower:
                val *= 1_000_000
            elif "billion" in snip_lower or " bn" in snip_lower:
                val *= 1_000_000_000
            elif "thousand" in snip_lower:
                val *= 1_000
            unit = "tCO2e"
            if "mt" in snip_lower or "million" in snip_lower:
                if val < 10_000:  # likely already in Mt, convert
                    val *= 1_000_000
            elif "kt" in snip_lower:
                if val < 1_000_000:
                    val *= 1_000
            return val, unit, snippet
    return None


def _extract_ghg_emissions(text: str) -> GHGEmissions:
    """Extract GHG emissions data (Scope 1, 2, 3, Total)."""
    emissions = GHGEmissions()

    # --- More flexible scope patterns ---
    # Each entry: (field_name, list of label patterns to search near)
    scope_labels = {
        "scope_1": [
            r"scope\s*1\b",
            r"direct\s*(?:ghg\s*)?emissions?",
            r"scope\s*1\s*(?:&|and)\s*2",  # combined mention
        ],
        "scope_2": [
            r"scope\s*2\b",
            r"indirect\s*(?:energy[- ]related\s*)?(?:ghg\s*)?emissions?",
        ],
        "scope_3": [
            r"scope\s*3\b",
            r"(?:other\s+indirect|value\s*chain)\s*(?:ghg\s*)?emissions?",
        ],
        "total": [
            r"total\s*(?:ghg\s*)?(?:greenhouse\s*gas\s*)?emissions?",
            r"(?:combined|aggregate|overall)\s*(?:ghg\s*)?emissions?",
            r"(?:ghg|greenhouse\s*gas)\s*(?:emissions?\s*)?(?:total|footprint)",
        ],
    }

    for field_name, label_patterns in scope_labels.items():
        for label_pat in label_patterns:
            # Find the label in text, then look for a number nearby (within 300 chars)
            for match in re.finditer(label_pat, text, re.IGNORECASE):
                # Search in a window after the label
                window_start = match.start()
                window_end = min(len(text), match.end() + 300)
                window = text[window_start:window_end]

                result = _extract_emission_value(window)
                if result:
                    val, unit, snippet = result
                    esg_field = ESGField(
                        value=val, unit=unit, confidence="High", source=snippet
                    )
                    setattr(emissions, field_name, esg_field)
                    break

                # Also try: label ... colon/equals ... number
                num_pat = rf"(?::\s*|=\s*|is\s+|was\s+|were\s+|of\s+|at\s+){_NUM_PAT}{_MULT_PAT}\s*(?:{_UNIT_PAT})?"
                result2 = _find_number(num_pat, window)
                if result2:
                    groups, snippet = result2
                    val = _parse_number(groups[0])
                    if val is not None and val > 0:
                        snip_lower = snippet.lower()
                        if "million" in snip_lower or " mn" in snip_lower:
                            val *= 1_000_000
                        elif "billion" in snip_lower or " bn" in snip_lower:
                            val *= 1_000_000_000
                        esg_field = ESGField(
                            value=val, unit="tCO2e", confidence="Medium", source=snippet
                        )
                        setattr(emissions, field_name, esg_field)
                        break

            # Stop trying more patterns if we found this field
            if not getattr(emissions, field_name).is_missing():
                break

    return emissions


def _extract_energy(text: str) -> Energy:
    """Extract energy consumption and renewable energy percentage."""
    energy = Energy()

    # Energy consumption — flexible patterns
    energy_labels = [
        r"(?:total\s*)?energy\s*consumption",
        r"(?:total\s*)?energy\s*(?:use|usage|demand)",
        r"electricity\s*consumption",
        r"energy\s*(?:consumed|purchased)",
    ]
    energy_units = r"(mwh|gwh|tj|gj|kwh|twh)"

    for label_pat in energy_labels:
        for match in re.finditer(label_pat, text, re.IGNORECASE):
            window = text[match.start():min(len(text), match.end() + 200)]
            pat = rf"{_NUM_PAT}\s*{energy_units}"
            result = _find_number(pat, window)
            if result:
                groups, snippet = result
                val = _parse_number(groups[0])
                if val is not None and val > 0:
                    unit = groups[1].lower() if len(groups) > 1 else "mwh"
                    energy.total_consumption = ESGField(
                        value=val, unit=unit, confidence="High", source=snippet
                    )
                    break
        if not energy.total_consumption.is_missing():
            break

    # Renewable energy percentage — flexible patterns
    renew_labels = [
        r"renewable\s*energy",
        r"clean\s*energy",
        r"renewables?",
        r"green\s*energy",
    ]
    for label_pat in renew_labels:
        for match in re.finditer(label_pat, text, re.IGNORECASE):
            window = text[match.start():min(len(text), match.end() + 200)]
            # Look for percentage
            pct_pat = r"([0-9][0-9,.]*)\s*%"
            result = _find_number(pct_pat, window)
            if result:
                groups, snippet = result
                val = _parse_number(groups[0])
                if val is not None and 0 <= val <= 100:
                    energy.renewable_energy_pct = ESGField(
                        value=val, unit="%", confidence="High", source=snippet
                    )
                    break
        if not energy.renewable_energy_pct.is_missing():
            break

    # Also try: "X% renewable" pattern (percentage before keyword)
    if energy.renewable_energy_pct.is_missing():
        pat = r"([0-9][0-9,.]*)\s*%\s*(?:of\s+(?:total\s+)?(?:energy|electricity|power)\s+(?:from\s+|is\s+)?)?(?:renewable|clean|green)"
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            val = _parse_number(groups[0])
            if val is not None and 0 <= val <= 100:
                energy.renewable_energy_pct = ESGField(
                    value=val, unit="%", confidence="High", source=snippet
                )

    return energy


def _extract_climate_targets(text: str) -> ClimateTargets:
    """Extract climate targets (net zero, interim, science-based)."""
    targets = ClimateTargets()

    # Net zero target year — very flexible
    nz_patterns = [
        r"net[\s-]*zero\s*(?:emissions?\s*)?(?:by|target[:\s]*|goal[:\s]*|in)\s*(\d{4})",
        r"(?:achieve|reach|attain|commit\w*\s+to)\s*net[\s-]*zero\s*(?:emissions?\s*)?(?:by\s*)?(\d{4})",
        r"carbon[\s-]*neutral(?:ity)?\s*(?:by|target|goal|in)\s*(\d{4})",
        r"net[\s-]*zero\s*(?:\w+\s+){0,12}(\d{4})",
        r"(\d{4})\s*net[\s-]*zero",
        r"zero\s*(?:emissions?|carbon)\s*(?:by|target|goal|in)\s*(\d{4})",
    ]
    for pat in nz_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            try:
                year = int(groups[0])
                if 2025 <= year <= 2100:
                    targets.net_zero_year = ESGField(
                        value=year, confidence="High", source=snippet
                    )
                    break
            except ValueError:
                continue

    # Interim targets — flexible
    interim_patterns = [
        r"reduce\s*(?:(?:ghg|carbon|greenhouse\s*gas)\s*)?(?:emissions?\s*)?(?:by\s*)?([0-9]+)\s*%\s*(?:by\s*|from\s*\d{4}\s*(?:to|by)\s*)?(\d{4})",
        r"([0-9]+)\s*%\s*(?:reduction|decrease|cut)\s*(?:in\s*(?:emissions?\s*)?)?(?:by\s*)?(\d{4})",
        r"(?:target|goal|aim|commit\w*)\s*(?:to\s+)?(?:reduce|cut|lower)\s*(?:\w+\s+){0,5}([0-9]+)\s*%\s*(?:\w+\s+){0,5}(\d{4})",
        r"([0-9]+)\s*%\s*(?:\w+\s+){0,5}(?:by|before|until)\s*(\d{4})",
    ]
    for pat in interim_patterns:
        result = _find_number(pat, text)
        if result:
            groups, snippet = result
            try:
                pct = int(groups[0])
                year = int(groups[1])
                if 0 < pct <= 100 and 2025 <= year <= 2100:
                    targets.interim_targets = ESGField(
                        value=f"{pct}% reduction by {year}",
                        confidence="High",
                        source=snippet,
                    )
                    break
            except (ValueError, IndexError):
                continue

    # Science-based targets — flexible
    sbt_patterns = [
        r"(science[\s-]*based\s*targets?\s*(?:initiative|sbti)?[^.\n]{0,150}[.\n])",
        r"(sbti[\s-]*(?:approved|validated|committed|aligned|verified)[^.\n]{0,150}[.\n])",
        r"((?:approved|validated|committed)\s+(?:by|to|with)\s*(?:the\s*)?(?:science[\s-]*based|sbti)[^.\n]{0,150}[.\n])",
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
            found_physical.append(keyword)

    if found_physical:
        # Get context around the first keyword found
        idx = text_lower.index(found_physical[0])
        start = max(0, idx - 100)
        end = min(len(text), idx + 200)
        snippet = text[start:end].strip()
        risks.physical_risks = ESGField(
            value=found_physical,
            confidence="Medium",
            source=snippet,
        )

    # Transition risks
    found_transition = []
    for keyword in TRANSITION_RISK_KEYWORDS:
        if keyword in text_lower:
            found_transition.append(keyword)

    if found_transition:
        idx = text_lower.index(found_transition[0])
        start = max(0, idx - 100)
        end = min(len(text), idx + 200)
        snippet = text[start:end].strip()
        risks.transition_risks = ESGField(
            value=found_transition,
            confidence="Medium",
            source=snippet,
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
                end = min(len(text), idx + 250)
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

    for field_name, keywords in SCOPE3_CATEGORIES.items():
        for keyword in keywords:
            # Find the keyword, then look for a number nearby
            for match in re.finditer(re.escape(keyword), text, re.IGNORECASE):
                window = text[match.start():min(len(text), match.end() + 300)]
                result = _extract_emission_value(window)
                if result:
                    val, unit, snippet = result
                    esg_field = ESGField(
                        value=val,
                        unit=unit,
                        confidence="Medium",
                        source=snippet,
                    )
                    setattr(scope3, field_name, esg_field)
                    break
            if not getattr(scope3, field_name).is_missing():
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
