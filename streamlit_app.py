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

try:
    from esg_agent.collector import collect
    from esg_agent.extractor import extract_esg_data
    from esg_agent.standardizer import standardize
    from esg_agent.validator import validate
    from esg_agent.manual_integration import (
        merge_manual_data, load_manual_input, FIELD_DESCRIPTIONS, FIELD_UNITS,
    )
    from esg_agent.output_json import export_json
    from esg_agent.output_excel import export_excel
    from esg_agent.output_word import export_word
except Exception as e:
    st.error(f"Failed to import esg_agent: {e}")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

# On Streamlit Community Cloud the repo directory is read-only; use /tmp instead.
_REPO_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_OUTPUT = os.path.join(_REPO_DIR, "output")
try:
    os.makedirs(_DEFAULT_OUTPUT, exist_ok=True)
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
    st.subheader("Manual Data Entry (optional)")
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
        with st.expander(section_title, expanded=False):
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

                safe_name = company_name.strip().replace(" ", "_").lower()

                # ── Step-by-step pipeline with visible progress ──────────
                progress = st.progress(0, text="Starting pipeline...")

                # Step 1: Collect
                progress.progress(10, text="Step 1/6: Collecting data from sources...")
                collected_data = collect(
                    company_name.strip(),
                    url=url.strip() or None,
                    pdf_path=pdf_path,
                )
                if url.strip():
                    collected_data["url"] = url.strip()
                if pdf_path:
                    collected_data["pdf_path"] = pdf_path

                web_chars = len(collected_data.get("web_text", ""))
                pdf_chars = len(collected_data.get("pdf_text", ""))
                combined_text = collected_data.get("combined_text", "")

                # Show collection results
                st.info(
                    f"**Collection complete:** "
                    f"{web_chars:,} chars from website, "
                    f"{pdf_chars:,} chars from PDF, "
                    f"{len(combined_text):,} chars total"
                )

                if not combined_text.strip():
                    st.warning(
                        "No text could be extracted from the provided sources. "
                        "This could mean the URL is unreachable, blocked, or uses "
                        "JavaScript rendering. Try providing a direct PDF report URL "
                        "or uploading a PDF file instead."
                    )

                # Show raw scraped text preview
                if combined_text.strip():
                    with st.expander("🔍 Preview: Scraped Text (first 3000 chars)", expanded=False):
                        st.text(combined_text[:3000])

                # Step 2: Extract
                progress.progress(30, text="Step 2/6: Extracting ESG data...")
                dataset = extract_esg_data(collected_data)

                # Step 3: Standardize
                progress.progress(50, text="Step 3/6: Standardizing units...")
                dataset = standardize(dataset)

                # Step 4: Validate
                progress.progress(60, text="Step 4/6: Validating data...")
                dataset = validate(dataset)

                # Step 5: Manual merge
                if manual_path:
                    progress.progress(70, text="Step 5/6: Merging manual data...")
                    manual_data = load_manual_input(manual_path)
                    dataset = merge_manual_data(dataset, manual_data)
                    dataset = validate(dataset)
                else:
                    progress.progress(70, text="Step 5/6: No manual data, skipping...")

                # Step 6: Generate outputs
                progress.progress(85, text="Step 6/6: Generating reports...")
                json_path = os.path.join(OUTPUT_DIR, f"{safe_name}_esg_data.json")
                excel_path = os.path.join(OUTPUT_DIR, f"{safe_name}_esg_data.xlsx")
                word_path = os.path.join(OUTPUT_DIR, f"{safe_name}_esg_report.docx")

                export_json(dataset, json_path)
                export_excel(dataset, excel_path)
                export_word(dataset, word_path)

                completeness = dataset.data_quality.completeness_pct
                missing_fields = dataset.data_quality.fields_missing

                progress.progress(100, text="Pipeline complete!")

                # ── Results ──────────────────────────────────────────────
                st.success(f"Pipeline completed! Data completeness: **{completeness:.1f}%**")

                # Quality metrics
                st.subheader("Data Quality")
                m1, m2, m3 = st.columns(3)
                total_fields = 22
                filled = total_fields - len(missing_fields)
                m1.metric("Completeness", f"{completeness:.1f}%")
                m2.metric("Fields Populated", f"{filled} / {total_fields}")
                m3.metric("Missing Fields", len(missing_fields))

                st.progress(completeness / 100)

                # Downloads
                st.subheader("Download Reports")
                d1, d2, d3 = st.columns(3)
                for col, path, label, mime in [
                    (d1, json_path,  "📄 JSON Dataset",   "application/json"),
                    (d2, excel_path, "📊 Excel Workbook", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                    (d3, word_path,  "📝 Word Report",    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
                ]:
                    if os.path.exists(path):
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
                with open(json_path) as f:
                    dataset_dict = json.load(f)

                SECTION_LABELS = {
                    "company_profile": "🏢 Company Profile",
                    "ghg_emissions": "☁️ GHG Emissions",
                    "energy": "⚡ Energy",
                    "climate_targets": "🎯 Climate Targets",
                    "climate_risks": "⚠️ Climate Risks",
                    "governance": "🏛️ Governance",
                    "scope3_breakdown": "🔗 Scope 3 Breakdown",
                }

                for section_key, section_label in SECTION_LABELS.items():
                    section_data = dataset_dict.get(section_key, {})
                    rows = []
                    for field_key, field_data in section_data.items():
                        if not isinstance(field_data, dict):
                            continue
                        fp = f"{section_key}.{field_key}"
                        conf = field_data.get("confidence") or "Missing"
                        raw_value = field_data.get("value", "missing")
                        if raw_value == "missing" or raw_value is None:
                            display_value = "—"
                        elif isinstance(raw_value, list):
                            display_value = ", ".join(str(v) for v in raw_value)
                        else:
                            display_value = str(raw_value)
                        rows.append({
                            "Field": FIELD_DESCRIPTIONS.get(fp, field_key),
                            "Value": display_value,
                            "Unit": field_data.get("unit", ""),
                            "Confidence": conf,
                            "Source": (field_data.get("source", "") or "")[:120],
                        })
                    if rows:
                        has_data = any(r["Value"] != "—" for r in rows)
                        with st.expander(
                            f"{section_label}  {'✅' if has_data else '❌ (no data)'}",
                            expanded=has_data,
                        ):
                            st.dataframe(
                                rows,
                                use_container_width=True,
                                hide_index=True,
                            )

                # Missing fields
                if missing_fields:
                    with st.expander(f"⚠️ Data Gaps ({len(missing_fields)} fields)", expanded=True):
                        st.caption(
                            "These fields could not be populated automatically. "
                            "Try providing a more detailed sustainability report PDF, "
                            "or fill in the Manual Data Entry section above and re-run."
                        )
                        cols = st.columns(2)
                        for i, f in enumerate(missing_fields):
                            cols[i % 2].write(f"- {FIELD_DESCRIPTIONS.get(f, f)}")

            except Exception as e:
                st.error(f"Pipeline error: {e}")
                import traceback
                st.code(traceback.format_exc())
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
