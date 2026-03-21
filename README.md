# ESG Data Collection & Intelligence System

An automated ESG (Environmental, Social, Governance) data collection, extraction, validation, and reporting system. Reduces manual ESG data work by automating collection from web and PDF sources, with support for manual data input via templates.

## Features

- **Web Scraping** - Extract ESG data from company websites and sustainability pages
- **PDF Extraction** - Parse sustainability reports and annual reports
- **Pattern-Based Extraction** - Automatically identify GHG emissions, energy data, climate targets, risks, and governance disclosures
- **Data Standardisation** - Convert units to standard formats (tCO2e, MWh, %)
- **Validation & Quality Scoring** - Confidence scoring (High/Medium/Low), completeness tracking, consistency checks
- **Manual Data Integration** - Generate templates for missing data, merge manual inputs
- **Multi-Format Output** - JSON dataset, Excel workbook (7 sheets), Word report

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Collect ESG Data

```bash
# From a website
python main.py collect --company "Apple Inc" --url "https://www.apple.com/environment/"

# From a PDF report
python main.py collect --company "Shell" --pdf "./shell_sustainability_report.pdf"

# From both sources
python main.py collect --company "Microsoft" --url "https://microsoft.com/sustainability" --pdf "./msft_report.pdf"

# With manual data
python main.py collect --company "Tesla" --url "https://tesla.com" --manual filled_template.json
```

### Generate Manual Input Template

```bash
python main.py template --output my_template.json
```

### Merge Manual Data into Existing Dataset

```bash
python main.py merge --dataset output/apple_esg_data.json --manual filled_template.json
```

## Output Files

All outputs are saved to the `output/` directory (configurable with `--output-dir`):

| File | Format | Description |
|------|--------|-------------|
| `{company}_esg_data.json` | JSON | Structured ESG dataset with all fields, units, confidence scores |
| `{company}_esg_data.xlsx` | Excel | Multi-sheet workbook: Company Profile, GHG Emissions, Energy, Climate Targets, Climate Risks, Governance, Scope 3, Data Quality |
| `{company}_esg_report.docx` | Word | Professional ESG summary report with executive summary, tables, and data gap analysis |

## ESG Data Categories

1. **Company Profile** - Name, industry, headquarters, reporting year
2. **GHG Emissions** - Scope 1, 2, 3, and total (in tCO2e)
3. **Energy** - Total consumption (MWh), renewable energy share (%)
4. **Climate Targets** - Net zero year, interim targets, science-based targets
5. **Climate Risks** - Physical risks, transition risks
6. **Governance** - Board oversight, ESG committees, climate-linked incentives
7. **Scope 3 Breakdown** - Purchased goods, transport, product use, end-of-life

## Supported Frameworks

Aligned with disclosure requirements from:
- CSRD (Corporate Sustainability Reporting Directive)
- ISSB (International Sustainability Standards Board)
- TCFD (Task Force on Climate-Related Financial Disclosures)
- GHG Protocol

## Architecture

```
main.py                  → CLI entry point (argparse)
esg_agent/
  collector.py           → Web scraping + PDF extraction + text cleaning
  extractor.py           → Regex/keyword-based ESG data extraction
  standardizer.py        → Unit conversion and normalisation
  validator.py           → Missing field detection, consistency checks, confidence scoring
  manual_integration.py  → Template generation and manual data merging
  output_json.py         → JSON export
  output_excel.py        → Excel workbook generation (openpyxl)
  output_word.py         → Word report generation (python-docx)
  pipeline.py            → Orchestrator running all modules in sequence
  models.py              → Dataclass-based ESG data models
config.py                → ESG keywords, patterns, conversion factors
```

## Data Flow

```
Input (company name, URL, PDF, manual data)
  → Collector (web scrape + PDF extract + clean)
  → Extractor (pattern-based ESG data extraction)
  → Standardiser (unit conversion to tCO2e, MWh, %)
  → Validator (confidence scoring, completeness check)
  → Manual Integration (merge user-provided data)
  → Output (JSON + Excel + Word)
```
