"""Streamlit entry point for the Citizen Welfare Eligibility Checker.

This is the ONLY file that imports streamlit. All business logic is
delegated to the `core` and `loaders` packages.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import io
import os
import re as _re
import sys

# ---------------------------------------------------------------------------
# Path fix: allow imports from the welfare_checker/ package root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

from core.eligibility import check_all_schemes
from core.models import Citizen, EligibilityResult
from core.validation import (
    VALID_CASTE_CATEGORIES,
    VALID_EMPLOYMENT_STATUSES,
    VALID_GENDERS,
    VALID_STATES,
    validate_inputs,
)
from loaders.scheme_loader import load_schemes
from loaders.translation_loader import get_labels, load_translations

# ---------------------------------------------------------------------------
# Page configuration (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Welfare Eligibility Checker",
    page_icon="🏛️",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Cached data loaders — run once and cache across reruns
# ---------------------------------------------------------------------------

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@st.cache_data(show_spinner=False)
def _load_schemes_cached(_version: int = 3) -> list:
    return load_schemes(os.path.join(_DATA_DIR, "schemes.json"))


@st.cache_data(show_spinner=False)
def _load_translations_cached(_version: int = 2) -> dict:
    return load_translations(os.path.join(_DATA_DIR, "translations.json"))


# ---------------------------------------------------------------------------
# Language selector (sidebar)
# ---------------------------------------------------------------------------

LANGUAGE_OPTIONS: dict[str, str] = {
    "English": "en",
    "हिन्दी (Hindi)": "hi",
    "தமிழ் (Tamil)": "ta",
    "বাংলা (Bengali)": "bn",
    "తెలుగు (Telugu)": "te",
    "मराठी (Marathi)": "mr",
    "ગુજરાતી (Gujarati)": "gu",
    "ಕನ್ನಡ (Kannada)": "kn",
    "മലയാളം (Malayalam)": "ml",
    "ਪੰਜਾਬੀ (Punjabi)": "pa",
    "ଓଡ଼ିଆ (Odia)": "or",
}

translations = _load_translations_cached()
schemes = _load_schemes_cached()

with st.sidebar:
    st.header("🌐 Language / भाषा / மொழி")
    selected_lang_name = st.selectbox(
        "Select Language",
        options=list(LANGUAGE_OPTIONS.keys()),
        key="language_selector",
    )
    lang_code: str = LANGUAGE_OPTIONS[selected_lang_name]

    st.divider()

    # -----------------------------------------------------------------------
    # Stats badge in sidebar
    # -----------------------------------------------------------------------
    st.metric("📋 Total Schemes", "50+")
    categories = sorted(set(s.category for s in schemes))
    st.metric("🗂️ Categories", len(categories))

# Retrieve the label dict for the current language (falls back to English)
L: dict[str, str] = get_labels(translations, lang_code)

# ---------------------------------------------------------------------------
# App title
# ---------------------------------------------------------------------------
st.title(f"🏛️ {L.get('app_title', 'Citizen Welfare Eligibility Checker')}")
st.caption(L.get("app_subtitle", "Check your eligibility for 50+ Indian government welfare schemes instantly"))
st.divider()

# ---------------------------------------------------------------------------
# Citizen input form
# ---------------------------------------------------------------------------
st.subheader(f"📋 {L.get('form_header', 'Enter Your Information')}")

col1, col2 = st.columns(2)

with col1:
    name_input: str = st.text_input(
        L.get("form_name_label", "Full Name"),
        placeholder=L.get("form_name_placeholder", "e.g. Ramesh Kumar"),
        key="input_name",
    )
    age_input: int = st.number_input(
        L.get("form_age_label", "Age (years)"),
        min_value=0,
        max_value=120,
        value=25,
        step=1,
        key="input_age",
    )
    gender_input: str = st.selectbox(
        L.get("form_gender_label", "Gender"),
        options=VALID_GENDERS,
        key="input_gender",
    )
    state_input: str = st.selectbox(
        L.get("form_state_label", "State / Union Territory"),
        options=VALID_STATES,
        key="input_state",
    )

with col2:
    income_input: float = st.number_input(
        L.get("form_income_label", "Annual Household Income (INR)"),
        min_value=0.0,
        max_value=10_000_000.0,
        value=80000.0,
        step=1000.0,
        format="%.0f",
        key="input_income",
    )
    employment_input: str = st.selectbox(
        L.get("form_employment_label", "Employment Status"),
        options=VALID_EMPLOYMENT_STATUSES,
        key="input_employment",
    )
    caste_input: str = st.selectbox(
        L.get("form_caste_label", "Caste Category"),
        options=VALID_CASTE_CATEGORIES,
        key="input_caste",
    )

st.divider()

# ---------------------------------------------------------------------------
# Action buttons
# ---------------------------------------------------------------------------
btn_col1, btn_col2 = st.columns([3, 1])

with btn_col1:
    check_clicked: bool = st.button(
        f"🔍 {L.get('btn_check', 'Check Eligibility')}",
        type="primary",
        use_container_width=True,
    )

with btn_col2:
    reset_clicked: bool = st.button(
        L.get("btn_reset", "Reset Form"),
        type="secondary",
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Reset handler
# ---------------------------------------------------------------------------
if reset_clicked:
    for key in ["input_name", "input_age", "input_gender", "input_state",
                "input_income", "input_employment", "input_caste", "results",
                "citizen_name"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ---------------------------------------------------------------------------
# Eligibility check handler
# ---------------------------------------------------------------------------
if check_clicked:
    form_data: dict = {
        "name": name_input,
        "age": int(age_input),
        "gender": gender_input,
        "state": state_input,
        "annual_income": float(income_input),
        "employment_status": employment_input,
        "caste_category": caste_input,
    }

    errors: list[str] = validate_inputs(form_data)

    if errors:
        st.error(f"**{L.get('validation_header', 'Please fix the following errors:')}**")
        for error in errors:
            st.write(f"• {error}")
    else:
        citizen = Citizen(
            name=str(name_input),
            age=int(age_input),
            gender=gender_input,
            state=state_input,
            annual_income=float(income_input),
            employment_status=employment_input,
            caste_category=caste_input,
        )

        results: list[EligibilityResult] = check_all_schemes(citizen, schemes)
        st.session_state["results"] = results
        st.session_state["citizen_name"] = citizen.name

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_URL_RE = _re.compile(
    r'(https?://[^\s)]+|[a-zA-Z0-9.-]+\.gov\.in[^\s)]*|[a-zA-Z0-9.-]+\.nic\.in[^\s)]*|[a-zA-Z0-9.-]+\.co\.in[^\s)]*)'
)


def _linkify(text: str) -> str:
    """Wrap any URL or .gov.in / .nic.in / .co.in domain into a markdown link."""
    def _replace(m: _re.Match) -> str:
        url = m.group(0).rstrip(".,;)")
        href = url if url.startswith("http") else f"https://{url}"
        return f"[{url}]({href})"
    return _URL_RE.sub(_replace, text)


def _generate_pdf(
    citizen_name: str,
    eligible: list,
    ineligible: list,
    schemes: list,
) -> bytes:
    """Generate a PDF summary of eligibility results."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "JanSeva Welfare Eligibility Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Citizen: {citizen_name}", ln=True, align="C")
    pdf.ln(4)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    # Summary
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Summary: {len(eligible)} Eligible  |  {len(ineligible)} Not Eligible", ln=True)
    pdf.ln(4)

    # Eligible schemes
    if eligible:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(0, 128, 0)
        pdf.cell(0, 9, "ELIGIBLE SCHEMES", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        for result in eligible:
            matching = next((s for s in schemes if s.name == result.scheme_name), None)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 7, result.scheme_name)
            if matching:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(0, 6, f"Category: {matching.category}")
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 9)
                for reason in result.reasons:
                    clean = reason.replace("\u2713", "OK").replace("\u2717", "X")
                    pdf.multi_cell(0, 6, f"- {clean}")
                guidance_clean = _re.sub(r'\s+', ' ', matching.guidance)
                pdf.multi_cell(0, 6, f"How to Apply: {guidance_clean}")
                pdf.set_font("Helvetica", "I", 9)
                pdf.multi_cell(0, 6, f"Docs: {', '.join(matching.documents_required)}")
            pdf.ln(3)

    # Not eligible schemes
    if ineligible:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(180, 0, 0)
        pdf.cell(0, 9, "NOT ELIGIBLE SCHEMES", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        for result in ineligible:
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 7, result.scheme_name)
            pdf.set_font("Helvetica", "", 9)
            for reason in result.reasons:
                clean = reason.replace("\u2713", "OK").replace("\u2717", "X")
                pdf.multi_cell(0, 6, f"- {clean}")
            pdf.ln(2)

    # Footer
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "Generated by JanSeva | Team CLAVIX | janseva.streamlit.app", ln=True, align="C")

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Results panel
# ---------------------------------------------------------------------------
if "results" in st.session_state:
    results: list[EligibilityResult] = st.session_state["results"]
    citizen_name: str = st.session_state.get("citizen_name", "")

    eligible_results = [r for r in results if r.status == "Eligible"]
    ineligible_results = [r for r in results if r.status != "Eligible"]

    # Summary metrics
    st.subheader(f"📊 {L.get('results_header', 'Eligibility Results')} — {citizen_name}")
    m1, m2, m3 = st.columns(3)
    m1.metric(f"📋 {L.get('total_schemes_label', 'schemes checked')}", len(results))
    m2.metric(f"✅ {L.get('eligible_count_label', 'eligible')}", len(eligible_results))
    m3.metric("❌ Not eligible", len(ineligible_results))

    # PDF download button
    pdf_bytes = _generate_pdf(citizen_name, eligible_results, ineligible_results, schemes)
    st.download_button(
        label="📄 Download PDF Summary",
        data=pdf_bytes,
        file_name=f"janseva_{citizen_name.replace(' ', '_')}_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.divider()

    # -----------------------------------------------------------------------
    # Filter & Search bar
    # -----------------------------------------------------------------------
    st.markdown(f"#### 🔎 {L.get('filter_header', 'Filter & Search')}")
    f_col1, f_col2 = st.columns([1, 2])

    with f_col1:
        all_result_categories = sorted(set(
            s.category for s in schemes
            if any(r.scheme_name == s.name for r in results)
        ))
        category_options = [L.get("filter_all", "All Categories")] + all_result_categories
        selected_category = st.selectbox(
            L.get("filter_category_label", "Filter by Category"),
            options=category_options,
            key="filter_category",
        )

    with f_col2:
        search_query = st.text_input(
            L.get("filter_search_label", "Search Schemes"),
            placeholder=L.get("filter_search_placeholder", "Type scheme name..."),
            key="filter_search",
        ).lower()

    def _scheme_matches_filters(result: EligibilityResult) -> bool:
        matching = next((s for s in schemes if s.name == result.scheme_name), None)
        cat_ok = (
            selected_category == L.get("filter_all", "All Categories")
            or (matching and matching.category == selected_category)
        )
        search_ok = search_query == "" or search_query in result.scheme_name.lower()
        return cat_ok and search_ok

    filtered_eligible = [r for r in eligible_results if _scheme_matches_filters(r)]
    filtered_ineligible = [r for r in ineligible_results if _scheme_matches_filters(r)]

    st.divider()

    # --- Eligible schemes ---
    if filtered_eligible:
        st.success(
            f"✅ **{L.get('results_eligible_header', 'Eligible Schemes')}** "
            f"({len(filtered_eligible)} scheme(s) found)"
        )
        for result in filtered_eligible:
            matching = next((s for s in schemes if s.name == result.scheme_name), None)
            category_tag = f" • 🗂️ {matching.category}" if matching else ""
            with st.expander(f"✅ {result.scheme_name}{category_tag}", expanded=True):
                if matching:
                    st.caption(matching.description)
                st.markdown(f"**{L.get('section_reasons', 'Eligibility Reasons')}**")
                for reason in result.reasons:
                    st.write(reason)
                if matching:
                    st.markdown(f"**{L.get('section_guidance', 'How to Apply')}**")
                    st.markdown(
                        f'<div style="background:#e8f4fd;border-left:4px solid #3b82d4;padding:10px 14px;border-radius:4px;font-size:14px;">{_linkify(matching.guidance)}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{L.get('section_documents', 'Documents Required')}**")
                    for doc in matching.documents_required:
                        st.write(f"• {doc}")
    elif eligible_results:
        st.info("No eligible schemes match your current filter/search. Try clearing filters.")
    else:
        st.warning(L.get("results_no_eligible", "No schemes matched your profile. Please verify your details."))

    # --- Ineligible schemes ---
    if filtered_ineligible:
        st.markdown(f"#### ❌ {L.get('results_ineligible_header', 'Schemes You Do Not Qualify For')}")
        for result in filtered_ineligible:
            matching = next((s for s in schemes if s.name == result.scheme_name), None)
            category_tag = f" • 🗂️ {matching.category}" if matching else ""
            with st.expander(f"❌ {result.scheme_name}{category_tag}", expanded=False):
                st.markdown(f"**{L.get('section_reasons', 'Eligibility Reasons')}**")
                for reason in result.reasons:
                    st.write(reason)
