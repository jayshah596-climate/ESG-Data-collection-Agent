"""ESG Data Collection - Streamlit App."""

import os
import sys
import json
import tempfile

# Ensure the repo root is on sys.path so esg_agent is importable on
# Streamlit Community Cloud (where the local package isn't pip-installed).
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st

from esg_agent.pipeline import run_pipeline
from esg_agent.manual_integration import FIELD_DESCRIPTIONS, FIELD_UNITS

# On Streamlit Community Cloud the repo directory is read-only; use /tmp instead.
_REPO_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_OUTPUT = os.path.join(_REPO_DIR, "output")
try:
    os.makedirs(_DEFAULT_OUTPUT, exist_ok=True)
    # Quick write test
    _test = os.path.join(_DEFAULT_OUTPUT, ".writetest")
    open(_test, "w").close()
    os.remove(_test)
    OUTPUT_DIR = _DEFAULT_OUTPUT
except OSError:
    OUTPUT_DIR = os.path.join(tempfile.gettempdir(), "esg_output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ESG Data Collection",
    page_icon="🌿",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .stTabs [data-baseweb="tab"] { font-size: 0.95rem; font-weight: 600; }
    .metric-card {
        background: #e8f5ee; border-radius: 8px;
        padding: 1rem; text-align: center;
    }
    .badge-high   { background:#c6efce; color:#1a6b3c; padding:2px 8px; border-radius:4px; font-size:0.8rem; font-weight:600; }
    .badge-medium { background:#ffeb9c; color:#7c6a00; padding:2px 8px; border-radius:4px; font-size:0.8rem; font-weight:600; }
    .badge-low    { background:#ffc7ce; color:#c62828; padding:2px 8px; border-radius:4px; font-size:0.8rem; font-weight:600; }
    .badge-missing{ background:#eeeeee; color:#757575; padding:2px 8px; border-radius:4px; font-size:0.8rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🌿 ESG Data Collection & Intelligence")
st.caption("Collect, validate, and standardize ESG data — export to JSON, Excel, and Word")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_collect, tab_results = st.tabs(["📥 New Collection", "📂 Past Results"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — New Collection
# ═══════════════════════════════════════════════════════════════════════════════
with tab_collect:

    # ── Data Sources ─────────────────────────────────────────────────────────
    st.subheader("Data Sources")
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name *", placeholder="e.g., Apple Inc")
        url = st.text_input("Website / Sustainability Page URL",
                            placeholder="https://company.com/sustainability")
    with col2:
        pdf_file = st.file_uploader("Upload PDF Report", type=["pdf"])

    st.divider()

    # ── Manual Data Entry ────────────────────────────────────────────────────
    st.subheader("Manual Data Entry")
    st.caption("Fill in any fields you have data for. Leave blank to skip.")

    manual_values: dict[str, str] = {}

    SECTIONS = [
        ("🏢 Company Profile", [
            "company_profile.name",
            "company_profile.industry",
            "company_profile.headquarters",
            "company_profile.reporting_year",
        ]),
        ("☁️ GHG Emissions", [
            "ghg_emissions.scope_1",
            "ghg_emissions.scope_2",
            "ghg_emissions.scope_3",
            "ghg_emissions.total",
        ]),
        ("⚡ Energy", [
            "energy.total_consumption",
            "energy.renewable_energy_pct",
        ]),
        ("🎯 Climate Targets", [
            "climate_targets.net_zero_year",
            "climate_targets.interim_targets",
            "climate_targets.science_based_targets",
        ]),
        ("⚠️ Climate Risks", [
            "climate_risks.physical_risks",
            "climate_risks.transition_risks",
        ]),
        ("🏛️ Governance", [
            "governance.board_oversight",
            "governance.esg_committees",
            "governance.climate_linked_incentives",
        ]),
        ("🔗 Scope 3 Breakdown", [
            "scope3_breakdown.purchased_goods_and_services",
            "scope3_breakdown.transport_and_distribution",
            "scope3_breakdown.use_of_sold_products",
            "scope3_breakdown.end_of_life",
        ]),
    ]

    for section_title, fields in SECTIONS:
        with st.expander(section_title, expanded=(section_title == "🏢 Company Profile")):
            cols = st.columns(2)
            for i, field_path in enumerate(fields):
                unit = FIELD_UNITS.get(field_path, "")
                label = FIELD_DESCRIPTIONS[field_path]
                display_label = f"{label} ({unit})" if unit else label
                with cols[i % 2]:
                    val = st.text_input(display_label, key=f"field_{field_path}")
                    manual_values[field_path] = val

    st.divider()

    # ── Run Button ───────────────────────────────────────────────────────────
    run_clicked = st.button("🚀 Run ESG Pipeline", type="primary", use_container_width=True)

    if run_clicked:
        if not company_name.strip():
            st.error("Company name is required.")
        else:
            pdf_path = None
            manual_path = None

            try:
                # Save uploaded PDF
                if pdf_file:
                    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    tmp_pdf.write(pdf_file.read())
                    tmp_pdf.close()
                    pdf_path = tmp_pdf.name

                # Build manual input JSON
                fields_list = [
                    {
                        "field_path": fp,
                        "description": FIELD_DESCRIPTIONS[fp],
                        "expected_unit": FIELD_UNITS.get(fp, ""),
                        "value": v.strip(),
                    }
                    for fp, v in manual_values.items()
                    if v.strip()
                ]
                if fields_list:
                    tmp_manual = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".json", mode="w"
                    )
                    json.dump({"fields": fields_list}, tmp_manual, indent=2)
                    tmp_manual.close()
                    manual_path = tmp_manual.name

                # Run pipeline with progress display
                with st.spinner("Running ESG pipeline..."):
                    result = run_pipeline(
                        company_name=company_name.strip(),
                        url=url.strip() or None,
                        pdf_path=pdf_path,
                        manual_input_path=manual_path,
                        output_dir=OUTPUT_DIR,
                    )

                # ── Results ──────────────────────────────────────────────────
                st.success("Pipeline completed successfully!")

                # Quality metrics
                st.subheader("Data Quality")
                m1, m2, m3 = st.columns(3)
                m1.metric("Completeness", f"{result['completeness']:.1f}%")
                m2.metric("Fields Populated",
                          f"{22 - len(result['missing_fields'])} / 22")
                m3.metric("Missing Fields", len(result["missing_fields"]))

                st.progress(result["completeness"] / 100)

                # Downloads
                st.subheader("Download Reports")
                d1, d2, d3 = st.columns(3)
                for col, path, label, mime in [
                    (d1, result["json"],  "📄 JSON Dataset",   "application/json"),
                    (d2, result["excel"], "📊 Excel Workbook", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                    (d3, result["word"],  "📝 Word Report",    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                ]:
                    with open(path, "rb") as f:
                        col.download_button(
                            label=label,
                            data=f.read(),
                            file_name=os.path.basename(path),
                            mime=mime,
                            use_container_width=True,
                        )

                # Data preview table
                st.subheader("Extracted Data Preview")
                with open(result["json"]) as f:
                    dataset = json.load(f)

                SECTION_LABELS = {
                    "company_profile": "Company Profile",
                    "ghg_emissions": "GHG Emissions",
                    "energy": "Energy",
                    "climate_targets": "Climate Targets",
                    "climate_risks": "Climate Risks",
                    "governance": "Governance",
                    "scope3_breakdown": "Scope 3 Breakdown",
                }

                for section_key, section_label in SECTION_LABELS.items():
                    section_data = dataset.get(section_key, {})
                    rows = []
                    for field_key, field_data in section_data.items():
                        if not isinstance(field_data, dict):
                            continue
                        fp = f"{section_key}.{field_key}"
                        conf = field_data.get("confidence") or "Missing"
                        rows.append({
                            "Field": FIELD_DESCRIPTIONS.get(fp, field_key),
                            "Value": field_data.get("value", "—") if field_data.get("value") != "missing" else "—",
                            "Unit": field_data.get("unit", ""),
                            "Confidence": conf,
                            "Source": field_data.get("source", ""),
                        })
                    if rows:
                        with st.expander(f"**{section_label}**", expanded=False):
                            st.dataframe(
                                rows,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "Confidence": st.column_config.TextColumn("Confidence"),
                                },
                            )

                # Missing fields
                if result["missing_fields"]:
                    with st.expander("⚠️ Data Gaps", expanded=False):
                        st.caption("These fields could not be populated automatically. Re-run with manual data to fill them.")
                        for f in result["missing_fields"]:
                            st.write(f"• {FIELD_DESCRIPTIONS.get(f, f)}")

            except Exception as e:
                st.error(f"Pipeline error: {e}")
                raise
            finally:
                for p in [pdf_path, manual_path]:
                    if p:
                        try:
                            os.unlink(p)
                        except OSError:
                            pass


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Past Results
# ═══════════════════════════════════════════════════════════════════════════════
with tab_results:
    st.subheader("Previously Generated Reports")

    if not os.path.isdir(OUTPUT_DIR) or not os.listdir(OUTPUT_DIR):
        st.info("No results yet. Run a collection to generate reports.")
    else:
        files = sorted(
            [f for f in os.listdir(OUTPUT_DIR)
             if os.path.isfile(os.path.join(OUTPUT_DIR, f))],
            reverse=True,
        )

        MIME = {
            ".json":  "application/json",
            ".xlsx":  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".docx":  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }

        for fname in files:
            fpath = os.path.join(OUTPUT_DIR, fname)
            ext = os.path.splitext(fname)[1].lower()
            size_kb = os.path.getsize(fpath) / 1024
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(fname)
            c2.caption(f"{size_kb:.1f} KB")
            with open(fpath, "rb") as f:
                c3.download_button(
                    "Download",
                    data=f.read(),
                    file_name=fname,
                    mime=MIME.get(ext, "application/octet-stream"),
                    key=f"dl_{fname}",
                )
