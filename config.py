"""Configuration constants and ESG field definitions."""

# ESG keyword lists for content filtering and extraction
ESG_KEYWORDS = [
    # Emissions
    "emission", "carbon", "ghg", "greenhouse", "co2", "scope 1", "scope 2", "scope 3",
    "scope1", "scope2", "scope3", "carbon dioxide", "carbon footprint", "decarboni",
    # Climate
    "climate", "net zero", "net-zero", "carbon neutral", "carbon-neutral",
    "global warming", "paris agreement", "1.5 degree", "1.5°",
    # Energy
    "renewable", "energy consumption", "energy intensity", "energy use", "solar", "wind",
    "clean energy", "green energy", "electricity", "power purchase", "ppa",
    # General ESG
    "sustainability", "esg", "environmental", "social", "governance",
    "sustainable development", "sdg", "impact report", "csr",
    # Nature & resources
    "biodiversity", "water", "waste", "recycl", "circular economy",
    "deforestation", "land use", "natural capital",
    # Frameworks & standards
    "science-based target", "sbti", "tcfd", "csrd", "issb", "gri", "sasb",
    "cdp", "tnfd", "ifrs", "eu taxonomy",
    # Governance
    "board oversight", "committee", "incentive", "compensation",
    "executive remuneration", "sustainability officer",
    # Risks
    "physical risk", "transition risk", "carbon price", "carbon tax",
    "stranded asset", "climate risk", "climate-related",
    # Supply chain
    "supply chain", "purchased goods", "transport", "distribution",
    "value chain", "upstream", "downstream",
    # Social
    "diversity", "inclusion", "human rights", "labor", "labour",
    "health and safety", "living wage", "employee",
    # Targets & commitments
    "target", "commitment", "pledge", "ambition", "roadmap", "pathway",
    "reduction", "reduce", "achieve", "goal",
]

# Patterns for numeric extraction
EMISSION_PATTERNS = [
    r"scope\s*1[:\s]+(?:emissions?\s*(?:of|:)?\s*)?([0-9,.]+)\s*((?:mt?|kt?|t)?co2e?)",
    r"scope\s*2[:\s]+(?:emissions?\s*(?:of|:)?\s*)?([0-9,.]+)\s*((?:mt?|kt?|t)?co2e?)",
    r"scope\s*3[:\s]+(?:emissions?\s*(?:of|:)?\s*)?([0-9,.]+)\s*((?:mt?|kt?|t)?co2e?)",
    r"total\s*(?:ghg\s*)?emissions?\s*(?:of|:)?\s*([0-9,.]+)\s*((?:mt?|kt?|t)?co2e?)",
]

ENERGY_PATTERNS = [
    r"(?:total\s*)?energy\s*consumption\s*(?:of|:)?\s*([0-9,.]+)\s*(mwh|gwh|tj|gj|kwh)",
    r"renewable\s*energy\s*(?:share|percentage|%)?\s*(?:of|:)?\s*([0-9,.]+)\s*%",
]

TARGET_PATTERNS = [
    r"net[\s-]*zero\s*(?:by|target|goal)?\s*(\d{4})",
    r"carbon[\s-]*neutral\s*(?:by|target|goal)?\s*(\d{4})",
    r"reduce\s*(?:emissions?\s*)?(?:by\s*)?([0-9]+)\s*%\s*(?:by\s*)?(\d{4})",
    r"science[\s-]*based\s*target",
]

# Unit conversion factors
EMISSION_CONVERSIONS = {
    "tco2e": 1.0,
    "tco2": 1.0,
    "ktco2e": 1000.0,
    "ktco2": 1000.0,
    "mtco2e": 1_000_000.0,
    "mtco2": 1_000_000.0,
    "co2e": 1.0,  # assume tonnes if no prefix
    "tonnes": 1.0,
    "tons": 1.0,
    "metric tonnes": 1.0,
    "metric tons": 1.0,
}

ENERGY_CONVERSIONS_TO_MWH = {
    "mwh": 1.0,
    "gwh": 1000.0,
    "twh": 1_000_000.0,
    "kwh": 0.001,
    "tj": 277.778,
    "gj": 0.277778,
}

# Confidence scoring thresholds
CONFIDENCE_RULES = {
    "high": "Exact numeric value with unit found in source text",
    "medium": "Value found but unit inferred or value derived/calculated",
    "low": "Partial data, estimated, or extracted from ambiguous context",
}

# Physical and transition risk keywords
PHYSICAL_RISK_KEYWORDS = [
    "flood", "flooding", "drought", "wildfire", "bush fire",
    "hurricane", "cyclone", "typhoon",
    "sea level", "sea-level", "heat stress", "heatwave", "heat wave",
    "extreme weather", "water scarcity", "water stress",
    "storm", "precipitation", "temperature rise", "temperature increase",
    "coastal", "erosion", "landslide", "permafrost",
]

TRANSITION_RISK_KEYWORDS = [
    "carbon price", "carbon pricing", "carbon tax",
    "regulation", "regulatory", "policy", "legislation",
    "stranded asset", "technology shift", "technology risk",
    "market shift", "market risk", "reputation", "reputational",
    "litigation", "legal risk", "compliance",
    "ets", "emission trading", "cap and trade",
    "fuel efficiency", "energy efficiency standard",
]

# Governance keywords
GOVERNANCE_KEYWORDS = {
    "board_oversight": [
        "board oversight", "board of directors", "board responsibility",
        "board-level", "board level", "board supervision",
        "board committee", "board governance", "board member",
        "board chair", "chairman",
    ],
    "esg_committees": [
        "sustainability committee", "esg committee", "climate committee",
        "environmental committee", "csr committee",
        "sustainability governance", "esg governance",
        "sustainability board", "responsible business committee",
    ],
    "climate_linked_incentives": [
        "climate-linked", "esg-linked", "sustainability-linked",
        "emission reduction target", "incentive", "compensation linked",
        "executive remuneration", "performance metric",
        "sustainability metric", "esg metric", "kpi",
        "variable pay", "bonus", "long-term incentive",
    ],
}

# Scope 3 category keywords
SCOPE3_CATEGORIES = {
    "purchased_goods_and_services": [
        "purchased goods", "purchased services", "category 1",
        "procurement", "supply chain emission",
    ],
    "transport_and_distribution": [
        "upstream transport", "downstream transport", "distribution",
        "category 4", "category 9", "logistics", "freight",
        "shipping", "transportation",
    ],
    "use_of_sold_products": [
        "use of sold products", "product use phase", "category 11",
        "product lifecycle", "customer use",
    ],
    "end_of_life": [
        "end-of-life", "end of life", "disposal", "category 12",
        "waste treatment", "product disposal",
    ],
}

# Default output directory
DEFAULT_OUTPUT_DIR = "output"
