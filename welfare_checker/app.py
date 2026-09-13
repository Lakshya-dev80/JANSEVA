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

    pdf = FPDF(format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    # usable width = 210 - 20 - 20 = 170mm
    W = 170

    def row(text: str, h: int = 6) -> None:
        """Write a safe text row, truncating if needed."""
        safe = str(text).encode("latin-1", errors="replace").decode("latin-1")
        pdf.cell(W, h, safe, ln=True)

    def section(title: str, r: int, g: int, b: int) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(r, g, b)
        pdf.cell(W, 8, title, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 0, 0)
    row("JanSeva Welfare Eligibility Report", 10)
    pdf.set_font("Helvetica", "", 10)
    row(f"Citizen: {citizen_name}", 7)
    pdf.ln(3)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    # Summary
    pdf.set_font("Helvetica", "B", 11)
    row(f"Summary:  {len(eligible)} Eligible    {len(ineligible)} Not Eligible", 8)
    pdf.ln(3)

    # Eligible schemes
    if eligible:
        section("ELIGIBLE SCHEMES", 0, 130, 0)
        for result in eligible:
            matching = next((s for s in schemes if s.name == result.scheme_name), None)
            pdf.set_font("Helvetica", "B", 10)
            row(f"  {result.scheme_name[:80]}")
            if matching:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(80, 80, 80)
                row(f"  Category: {matching.category}")
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 8)
                for reason in result.reasons:
                    clean = (reason
                             .replace("\u2713", "OK")
                             .replace("\u2717", "X")
                             .replace("\u2714", "OK")
                             .replace("\u274c", "X"))
                    row(f"  - {clean[:100]}")
                guidance = _re.sub(r'\s+', ' ', matching.guidance)[:200]
                row(f"  Apply: {guidance}")
                docs = ", ".join(matching.documents_required)[:150]
                row(f"  Docs: {docs}")
                if matching.portal_url:
                    row(f"  Portal: {matching.portal_url}")
            pdf.ln(2)

    # Not eligible
    if ineligible:
        pdf.ln(2)
        section("NOT ELIGIBLE SCHEMES", 180, 0, 0)
        for result in ineligible:
            pdf.set_font("Helvetica", "B", 10)
            row(f"  {result.scheme_name[:80]}")
            pdf.set_font("Helvetica", "", 8)
            for reason in result.reasons:
                clean = (reason
                         .replace("\u2713", "OK")
                         .replace("\u2717", "X")
                         .replace("\u2714", "OK")
                         .replace("\u274c", "X"))
                row(f"  - {clean[:100]}")
            pdf.ln(2)

    # Footer
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    row("Generated by JanSeva | Team CLAVIX", 6)

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

    # PDF download button — generated only when clicked
    if st.button("📄 Download PDF Summary", use_container_width=True):
        pdf_bytes = _generate_pdf(citizen_name, eligible_results, ineligible_results, schemes)
        st.download_button(
            label="⬇️ Click here to download",
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
        # Total estimated benefit summary
        total_benefits = [s.benefit_amount for s in schemes
                         if any(r.scheme_name == s.name for r in filtered_eligible) and s.benefit_amount]
        st.success(
            f"✅ **{L.get('results_eligible_header', 'Eligible Schemes')}** "
            f"({len(filtered_eligible)} scheme(s) found)"
        )

        # Scam warning banner — global
        st.markdown(
            '<div style="background:#fff3cd;border-left:5px solid #ff9800;padding:12px 16px;border-radius:6px;margin-bottom:12px;">'
            '<b>⚠️ IMPORTANT — Beware of Scams!</b><br>'
            'All these government schemes are <b>100% FREE</b> to apply. '
            '<b>Never pay anyone</b> — no agent, middleman, or website — to apply on your behalf. '
            'Always apply directly through the official government portal.'
            '</div>',
            unsafe_allow_html=True,
        )

        for result in filtered_eligible:
            matching = next((s for s in schemes if s.name == result.scheme_name), None)
            category_tag = f" • 🗂️ {matching.category}" if matching else ""
            benefit_tag = f" • 💰 {matching.benefit_amount}" if matching and matching.benefit_amount else ""
            with st.expander(f"✅ {result.scheme_name}{category_tag}", expanded=True):
                if matching:
                    st.caption(matching.description)

                # Financial benefit highlight
                if matching and matching.benefit_amount:
                    st.markdown(
                        f'<div style="background:#e8f8e8;border-left:5px solid #1d6f42;padding:10px 16px;border-radius:6px;margin-bottom:8px;">'
                        f'<span style="font-size:13px;color:#555;">💰 <b>Estimated Benefit ({matching.benefit_type})</b></span><br>'
                        f'<span style="font-size:18px;font-weight:bold;color:#1d6f42;">{matching.benefit_amount}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                st.markdown(f"**{L.get('section_reasons', 'Eligibility Reasons')}**")
                for reason in result.reasons:
                    st.write(reason)
                if matching:
                    st.markdown(f"**{L.get('section_guidance', 'How to Apply')}**")
                    st.markdown(
                        f'<div style="background:#e8f4fd;border-left:4px solid #3b82d4;padding:10px 14px;border-radius:4px;font-size:14px;">{_linkify(matching.guidance)}</div>',
                        unsafe_allow_html=True,
                    )
                    if matching.portal_url:
                        st.markdown(
                            f'<a href="{matching.portal_url}" target="_blank" style="display:inline-block;margin-top:8px;padding:8px 20px;background:#1d6f42;color:white;border-radius:6px;text-decoration:none;font-weight:bold;font-size:14px;">🌐 Apply Now on Official Portal</a>',
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
