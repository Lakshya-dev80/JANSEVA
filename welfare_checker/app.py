"""Streamlit entry point for the Citizen Welfare Eligibility Checker.

This is the ONLY file that imports streamlit. All business logic is
delegated to the `core` and `loaders` packages.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import os
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


@st.cache_data
def _load_schemes_cached() -> list:
    return load_schemes(os.path.join(_DATA_DIR, "schemes.json"))


@st.cache_data
def _load_translations_cached() -> dict:
    return load_translations(os.path.join(_DATA_DIR, "translations.json"))


# ---------------------------------------------------------------------------
# Language selector (sidebar)
# ---------------------------------------------------------------------------

LANGUAGE_OPTIONS: dict[str, str] = {
    "English": "en",
    "हिन्दी (Hindi)": "hi",
    "தமிழ் (Tamil)": "ta",
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

# Retrieve the label dict for the current language (falls back to English)
L: dict[str, str] = get_labels(translations, lang_code)

# ---------------------------------------------------------------------------
# App title
# ---------------------------------------------------------------------------
st.title(f"🏛️ {L.get('app_title', 'Citizen Welfare Eligibility Checker')}")
st.caption(L.get("app_subtitle", "Check your eligibility for Indian government welfare schemes"))
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
    # Clear all input keys from session_state to reset widgets to defaults
    for key in ["input_name", "input_age", "input_gender", "input_state",
                "input_income", "input_employment", "input_caste", "results"]:
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

        # Store results in session_state so they persist after language switch
        st.session_state["results"] = results
        st.session_state["citizen_name"] = citizen.name

# ---------------------------------------------------------------------------
# Results panel
# ---------------------------------------------------------------------------
if "results" in st.session_state:
    results: list[EligibilityResult] = st.session_state["results"]
    citizen_name: str = st.session_state.get("citizen_name", "")

    st.subheader(f"📊 {L.get('results_header', 'Eligibility Results')} — {citizen_name}")

    eligible_results = [r for r in results if r.status == "Eligible"]
    ineligible_results = [r for r in results if r.status != "Eligible"]

    # --- Eligible schemes ---
    if eligible_results:
        st.success(
            f"✅ **{L.get('results_eligible_header', 'Eligible Schemes')}** "
            f"({len(eligible_results)} scheme(s) found)"
        )
        for result in eligible_results:
            with st.expander(f"✅ {result.scheme_name}", expanded=True):
                st.markdown(f"**{L.get('section_reasons', 'Eligibility Reasons')}**")
                for reason in result.reasons:
                    st.write(reason)

                # Find matching scheme for guidance and documents
                matching = next((s for s in schemes if s.name == result.scheme_name), None)
                if matching:
                    st.markdown(f"**{L.get('section_guidance', 'How to Apply')}**")
                    st.info(matching.guidance)

                    st.markdown(f"**{L.get('section_documents', 'Documents Required')}**")
                    for doc in matching.documents_required:
                        st.write(f"• {doc}")
    else:
        st.warning(
            L.get(
                "results_no_eligible",
                "No schemes matched your profile. Please verify your details.",
            )
        )

    # --- Ineligible schemes ---
    if ineligible_results:
        st.markdown(f"#### ❌ {L.get('results_ineligible_header', 'Schemes You Do Not Qualify For')}")
        for result in ineligible_results:
            with st.expander(f"❌ {result.scheme_name}", expanded=False):
                st.markdown(f"**{L.get('section_reasons', 'Eligibility Reasons')}**")
                for reason in result.reasons:
                    st.write(reason)
