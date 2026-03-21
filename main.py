#!/usr/bin/env python3
"""ESG Data Collection and Intelligence System - CLI Entry Point."""

import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_collect(args):
    """Run the full ESG data collection pipeline."""
    from esg_agent.pipeline import run_pipeline

    result = run_pipeline(
        company_name=args.company,
        url=args.url,
        pdf_path=args.pdf,
        manual_input_path=args.manual,
        output_dir=args.output_dir,
    )
    return 0


def cmd_template(args):
    """Generate a manual input template."""
    from esg_agent.manual_integration import generate_template, save_template

    template = generate_template()
    output_path = args.output or "manual_input_template.json"
    save_template(template, output_path)
    print(f"\nTemplate generated: {output_path}")
    print("Fill in the 'value' fields and use with: esg-agent collect --manual <path>")
    return 0


def cmd_merge(args):
    """Merge manual data into an existing dataset and re-export."""
    import json
    from esg_agent.models import ESGDataset
    from esg_agent.manual_integration import load_manual_input, merge_manual_data
    from esg_agent.validator import validate
    from esg_agent.output_json import export_json
    from esg_agent.output_excel import export_excel
    from esg_agent.output_word import export_word

    # Load existing dataset
    with open(args.dataset, "r") as f:
        data = json.load(f)

    # Reconstruct ESGDataset from JSON
    dataset = _dict_to_dataset(data)

    # Load and merge manual data
    manual_data = load_manual_input(args.manual)
    dataset = merge_manual_data(dataset, manual_data)
    dataset = validate(dataset)

    # Re-export
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(args.dataset))[0]
    export_json(dataset, os.path.join(output_dir, f"{base}_merged.json"))
    export_excel(dataset, os.path.join(output_dir, f"{base}_merged.xlsx"))
    export_word(dataset, os.path.join(output_dir, f"{base}_merged.docx"))

    return 0


def _dict_to_dataset(data: dict):
    """Reconstruct an ESGDataset from a dictionary (loaded from JSON)."""
    from esg_agent.models import (
        ESGDataset, ESGField, CompanyProfile, GHGEmissions, Energy,
        ClimateTargets, ClimateRisks, Governance, Scope3Breakdown, DataQuality,
    )

    def _to_field(d: dict) -> ESGField:
        if not isinstance(d, dict):
            return ESGField(value=d)
        return ESGField(
            value=d.get("value", "missing"),
            unit=d.get("unit", ""),
            confidence=d.get("confidence"),
            source=d.get("source", ""),
        )

    def _to_section(cls, section_data: dict):
        obj = cls()
        if not isinstance(section_data, dict):
            return obj
        for key, val in section_data.items():
            if hasattr(obj, key) and isinstance(val, dict) and "value" in val:
                setattr(obj, key, _to_field(val))
        return obj

    dataset = ESGDataset()
    dataset.company_profile = _to_section(CompanyProfile, data.get("company_profile", {}))
    dataset.ghg_emissions = _to_section(GHGEmissions, data.get("ghg_emissions", {}))
    dataset.energy = _to_section(Energy, data.get("energy", {}))
    dataset.climate_targets = _to_section(ClimateTargets, data.get("climate_targets", {}))
    dataset.climate_risks = _to_section(ClimateRisks, data.get("climate_risks", {}))
    dataset.governance = _to_section(Governance, data.get("governance", {}))
    dataset.scope3_breakdown = _to_section(Scope3Breakdown, data.get("scope3_breakdown", {}))

    dq = data.get("data_quality", {})
    dataset.data_quality = DataQuality(
        completeness_pct=dq.get("completeness_pct", 0),
        fields_missing=dq.get("fields_missing", []),
        confidence_scores=dq.get("confidence_scores", {}),
    )
    dataset.source_references = data.get("source_references", [])

    return dataset


def main():
    parser = argparse.ArgumentParser(
        description="ESG Data Collection and Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s collect --company "Apple Inc" --url "https://www.apple.com/environment/"
  %(prog)s collect --company "Shell" --pdf "./shell_report.pdf" --output-dir ./results
  %(prog)s template --output my_template.json
  %(prog)s merge --dataset output/apple_esg_data.json --manual filled_template.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Run ESG data collection pipeline")
    collect_parser.add_argument("--company", required=True, help="Company name")
    collect_parser.add_argument("--url", help="Company website or sustainability page URL")
    collect_parser.add_argument("--pdf", help="Path to PDF sustainability/annual report")
    collect_parser.add_argument("--manual", help="Path to completed manual input JSON")
    collect_parser.add_argument("--output-dir", default="output", help="Output directory (default: output)")

    # Template command
    template_parser = subparsers.add_parser("template", help="Generate manual input template")
    template_parser.add_argument("--output", help="Output path for template (default: manual_input_template.json)")

    # Merge command
    merge_parser = subparsers.add_parser("merge", help="Merge manual data into existing dataset")
    merge_parser.add_argument("--dataset", required=True, help="Path to existing ESG JSON dataset")
    merge_parser.add_argument("--manual", required=True, help="Path to completed manual input JSON")
    merge_parser.add_argument("--output-dir", default="output", help="Output directory (default: output)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "collect": cmd_collect,
        "template": cmd_template,
        "merge": cmd_merge,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
