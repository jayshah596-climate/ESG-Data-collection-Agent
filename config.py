"""Configuration constants and ESG field definitions."""

# ESG keyword lists for content filtering and extraction
ESG_KEYWORDS = [
    "emission", "carbon", "ghg", "greenhouse", "co2", "scope 1", "scope 2", "scope 3",
    "climate", "net zero", "net-zero", "carbon neutral", "decarboni",
    "renewable", "energy consumption", "energy intensity", "solar", "wind",
    "sustainability", "esg", "environmental", "social", "governance",
    "biodiversity", "water", "waste", "recycl", "circular economy",
    "science-based target", "sbti", "paris agreement", "tcfd", "csrd", "issb",
    "board oversight", "committee", "incentive", "compensation",
    "physical risk", "transition risk", "carbon price", "carbon tax",
    "supply chain", "purchased goods", "transport", "distribution",
    "diversity", "inclusion", "human rights", "labor", "health and safety",
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
}

ENERGY_CONVERSIONS_TO_MWH = {
    "mwh": 1.0,
    "gwh": 1000.0,
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
    "flood", "drought", "wildfire", "hurricane", "cyclone", "typhoon",
    "sea level", "heat stress", "extreme weather", "water scarcity",
    "storm", "precipitation", "temperature rise",
]

TRANSITION_RISK_KEYWORDS = [
    "carbon price", "carbon tax", "regulation", "policy", "legislation",
    "stranded asset", "technology shift", "market shift", "reputation",
    "litigation", "compliance", "ets", "emission trading",
]

# Governance keywords
GOVERNANCE_KEYWORDS = {
    "board_oversight": [
        "board oversight", "board of directors", "board responsibility",
        "board-level", "board level", "board supervision",
    ],
    "esg_committees": [
        "sustainability committee", "esg committee", "climate committee",
        "environmental committee", "csr committee",
    ],
    "climate_incentives": [
        "climate-linked", "esg-linked", "sustainability-linked",
        "emission reduction target", "incentive", "compensation linked",
        "executive remuneration", "performance metric",
    ],
}

# Scope 3 category keywords
SCOPE3_CATEGORIES = {
    "purchased_goods_and_services": [
        "purchased goods", "purchased services", "category 1",
    ],
    "transport_and_distribution": [
        "upstream transport", "downstream transport", "distribution",
        "category 4", "category 9",
    ],
    "use_of_sold_products": [
        "use of sold products", "product use phase", "category 11",
    ],
    "end_of_life": [
        "end-of-life", "end of life", "disposal", "category 12",
    ],
}

# Default output directory
DEFAULT_OUTPUT_DIR = "output"
