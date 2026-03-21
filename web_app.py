"""ESG Data Collection - Web UI.

A Flask-based web interface for the ESG Data Collection System.
Run with: python web_app.py
Then open http://localhost:5000 in your browser.
"""

import os
import json
import tempfile
from flask import Flask, render_template, request, redirect, url_for, send_file, flash

from esg_agent.pipeline import run_pipeline
from esg_agent.manual_integration import FIELD_DESCRIPTIONS, FIELD_UNITS
from esg_agent.output_json import dataset_to_dict

app = Flask(__name__, template_folder="web_templates", static_folder="web_static")
app.secret_key = os.urandom(24)

# Custom Jinja filter for extracting basename from file paths
app.jinja_env.filters["basename"] = os.path.basename

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


# Group field definitions for the form sections
FORM_SECTIONS = [
    {
        "id": "company_profile",
        "title": "Company Profile",
        "icon": "building",
        "fields": [
            ("company_profile.name", "text"),
            ("company_profile.industry", "text"),
            ("company_profile.headquarters", "text"),
            ("company_profile.reporting_year", "text"),
        ],
    },
    {
        "id": "ghg_emissions",
        "title": "GHG Emissions",
        "icon": "cloud",
        "fields": [
            ("ghg_emissions.scope_1", "number"),
            ("ghg_emissions.scope_2", "number"),
            ("ghg_emissions.scope_3", "number"),
            ("ghg_emissions.total", "number"),
        ],
    },
    {
        "id": "energy",
        "title": "Energy",
        "icon": "bolt",
        "fields": [
            ("energy.total_consumption", "number"),
            ("energy.renewable_energy_pct", "number"),
        ],
    },
    {
        "id": "climate_targets",
        "title": "Climate Targets",
        "icon": "bullseye",
        "fields": [
            ("climate_targets.net_zero_year", "text"),
            ("climate_targets.interim_targets", "text"),
            ("climate_targets.science_based_targets", "text"),
        ],
    },
    {
        "id": "climate_risks",
        "title": "Climate Risks",
        "icon": "exclamation-triangle",
        "fields": [
            ("climate_risks.physical_risks", "text"),
            ("climate_risks.transition_risks", "text"),
        ],
    },
    {
        "id": "governance",
        "title": "Governance",
        "icon": "users",
        "fields": [
            ("governance.board_oversight", "text"),
            ("governance.esg_committees", "text"),
            ("governance.climate_linked_incentives", "text"),
        ],
    },
    {
        "id": "scope3_breakdown",
        "title": "Scope 3 Breakdown",
        "icon": "sitemap",
        "fields": [
            ("scope3_breakdown.purchased_goods_and_services", "number"),
            ("scope3_breakdown.transport_and_distribution", "number"),
            ("scope3_breakdown.use_of_sold_products", "number"),
            ("scope3_breakdown.end_of_life", "number"),
        ],
    },
]


def _build_manual_json(form_data):
    """Convert form POST data into the manual input JSON format."""
    fields = []
    for path, desc in FIELD_DESCRIPTIONS.items():
        value = form_data.get(path, "").strip()
        fields.append({
            "field_path": path,
            "description": desc,
            "expected_unit": FIELD_UNITS.get(path, ""),
            "value": value,
        })
    return {"fields": fields}


@app.route("/")
def index():
    """Landing page."""
    return render_template("index.html")


@app.route("/collect", methods=["GET", "POST"])
def collect_data():
    """Form for data collection - URL/PDF + manual entry."""
    if request.method == "GET":
        return render_template(
            "collect.html",
            sections=FORM_SECTIONS,
            descriptions=FIELD_DESCRIPTIONS,
            units=FIELD_UNITS,
        )

    # POST: run the pipeline
    company_name = request.form.get("company_name", "").strip()
    if not company_name:
        flash("Company name is required.", "error")
        return redirect(url_for("collect_data"))

    url = request.form.get("url", "").strip() or None
    pdf_file = request.files.get("pdf")
    pdf_path = None

    # Save uploaded PDF to temp file
    if pdf_file and pdf_file.filename:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_file.save(tmp.name)
        pdf_path = tmp.name

    # Build manual input JSON from form fields
    manual_data = _build_manual_json(request.form)
    has_manual = any(f["value"] for f in manual_data["fields"])

    manual_path = None
    if has_manual:
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".json", mode="w"
        )
        json.dump(manual_data, tmp, indent=2)
        tmp.close()
        manual_path = tmp.name

    try:
        result = run_pipeline(
            company_name=company_name,
            url=url,
            pdf_path=pdf_path,
            manual_input_path=manual_path,
            output_dir=OUTPUT_DIR,
        )

        # Load the generated JSON for display
        with open(result["json"], "r") as f:
            dataset = json.load(f)

        return render_template(
            "results.html",
            company=company_name,
            result=result,
            dataset=dataset,
            sections=FORM_SECTIONS,
            descriptions=FIELD_DESCRIPTIONS,
            units=FIELD_UNITS,
        )
    except Exception as e:
        flash(f"Pipeline error: {e}", "error")
        return redirect(url_for("collect_data"))
    finally:
        # Clean up temp files
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except OSError:
                pass
        if manual_path:
            try:
                os.unlink(manual_path)
            except OSError:
                pass


@app.route("/download/<filename>")
def download(filename):
    """Download an output file."""
    # Only allow downloading from the output directory
    safe_path = os.path.join(OUTPUT_DIR, os.path.basename(filename))
    if not os.path.isfile(safe_path):
        flash("File not found.", "error")
        return redirect(url_for("index"))
    return send_file(safe_path, as_attachment=True)


@app.route("/results")
def list_results():
    """List all previously generated output files."""
    files = []
    if os.path.isdir(OUTPUT_DIR):
        for fname in sorted(os.listdir(OUTPUT_DIR)):
            fpath = os.path.join(OUTPUT_DIR, fname)
            size_kb = os.path.getsize(fpath) / 1024
            ext = os.path.splitext(fname)[1].lower()
            files.append({
                "name": fname,
                "size": f"{size_kb:.1f} KB",
                "type": ext.lstrip(".").upper(),
            })
    return render_template("results_list.html", files=files)


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\n  ESG Data Collection - Web UI")
    print("  Open http://localhost:5000 in your browser\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
