"""Pipeline Orchestrator - Runs all ESG modules in sequence."""

import os
from esg_agent.collector import collect
from esg_agent.extractor import extract_esg_data
from esg_agent.standardizer import standardize
from esg_agent.validator import validate
from esg_agent.manual_integration import merge_manual_data, load_manual_input
from esg_agent.output_json import export_json
from esg_agent.output_excel import export_excel
from esg_agent.output_word import export_word


def run_pipeline(
    company_name: str,
    url: str = None,
    pdf_path: str = None,
    manual_input_path: str = None,
    output_dir: str = "output",
) -> dict:
    """Run the full ESG data collection and reporting pipeline.

    Args:
        company_name: Name of the company to analyse
        url: Optional website URL to scrape
        pdf_path: Optional path to PDF sustainability/annual report
        manual_input_path: Optional path to completed manual input JSON
        output_dir: Directory for output files

    Returns:
        dict with paths to all generated output files
    """
    os.makedirs(output_dir, exist_ok=True)
    safe_name = company_name.replace(" ", "_").lower()

    print(f"\n{'='*60}")
    print(f" ESG Data Collection Pipeline - {company_name}")
    print(f"{'='*60}\n")

    # Module 1: Data Collection
    print("[STEP 1/6] Collecting data...")
    collected_data = collect(company_name, url=url, pdf_path=pdf_path)
    if url:
        collected_data["url"] = url
    if pdf_path:
        collected_data["pdf_path"] = pdf_path

    # Module 2: ESG Data Extraction
    print("\n[STEP 2/6] Extracting ESG data...")
    dataset = extract_esg_data(collected_data)

    # Module 3: Data Standardisation
    print("\n[STEP 3/6] Standardising data...")
    dataset = standardize(dataset)

    # Module 4: Data Validation
    print("\n[STEP 4/6] Validating data...")
    dataset = validate(dataset)

    # Module 5: Manual Data Integration
    if manual_input_path:
        print("\n[STEP 5/6] Merging manual data...")
        manual_data = load_manual_input(manual_input_path)
        dataset = merge_manual_data(dataset, manual_data)
        # Re-validate after merge
        dataset = validate(dataset)
    else:
        print("\n[STEP 5/6] No manual data provided, skipping merge...")

    # Module 6-8: Generate Outputs
    print("\n[STEP 6/6] Generating outputs...")
    json_path = os.path.join(output_dir, f"{safe_name}_esg_data.json")
    excel_path = os.path.join(output_dir, f"{safe_name}_esg_data.xlsx")
    word_path = os.path.join(output_dir, f"{safe_name}_esg_report.docx")

    export_json(dataset, json_path)
    export_excel(dataset, excel_path)
    export_word(dataset, word_path)

    print(f"\n{'='*60}")
    print(f" Pipeline Complete!")
    print(f" Data Completeness: {dataset.data_quality.completeness_pct}%")
    print(f" Missing Fields: {len(dataset.data_quality.fields_missing)}")
    print(f"{'='*60}")
    print(f"\n Output files:")
    print(f"   JSON:  {json_path}")
    print(f"   Excel: {excel_path}")
    print(f"   Word:  {word_path}")

    return {
        "json": json_path,
        "excel": excel_path,
        "word": word_path,
        "completeness": dataset.data_quality.completeness_pct,
        "missing_fields": dataset.data_quality.fields_missing,
    }
