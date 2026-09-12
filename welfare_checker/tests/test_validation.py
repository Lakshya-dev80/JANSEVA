"""Unit tests for the validation module (core/validation.py)."""

from __future__ import annotations

import pytest

from core.validation import (
    VALID_CASTE_CATEGORIES,
    VALID_EMPLOYMENT_STATUSES,
    VALID_GENDERS,
    VALID_STATES,
    validate_inputs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _valid_data(**overrides) -> dict:
    """Return a valid form data dict, with optional field overrides."""
    base = {
        "name": "Ramesh Kumar",
        "age": 35,
        "gender": "Male",
        "state": "Maharashtra",
        "annual_income": 80000.0,
        "employment_status": "Unemployed",
        "caste_category": "General",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestValidInputs:
    def test_valid_inputs_return_no_errors(self) -> None:
        errors = validate_inputs(_valid_data())
        assert errors == []

    def test_valid_inputs_with_unicode_name(self) -> None:
        errors = validate_inputs(_valid_data(name="रमेश कुमार"))
        assert errors == []

    def test_valid_inputs_with_tamil_name(self) -> None:
        errors = validate_inputs(_valid_data(name="ரமேஷ் குமார்"))
        assert errors == []

    def test_age_boundary_zero(self) -> None:
        errors = validate_inputs(_valid_data(age=0))
        assert errors == []

    def test_age_boundary_120(self) -> None:
        errors = validate_inputs(_valid_data(age=120))
        assert errors == []

    def test_income_boundary_zero(self) -> None:
        errors = validate_inputs(_valid_data(annual_income=0.0))
        assert errors == []

    def test_all_valid_states(self) -> None:
        for state in VALID_STATES:
            errors = validate_inputs(_valid_data(state=state))
            assert errors == [], f"State '{state}' should be valid but got errors: {errors}"

    def test_all_valid_genders(self) -> None:
        for gender in VALID_GENDERS:
            errors = validate_inputs(_valid_data(gender=gender))
            assert errors == []

    def test_all_valid_employment_statuses(self) -> None:
        for status in VALID_EMPLOYMENT_STATUSES:
            errors = validate_inputs(_valid_data(employment_status=status))
            assert errors == []

    def test_all_valid_caste_categories(self) -> None:
        for caste in VALID_CASTE_CATEGORIES:
            errors = validate_inputs(_valid_data(caste_category=caste))
            assert errors == []


# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------


class TestNameValidation:
    def test_empty_name_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(name=""))
        assert len(errors) >= 1
        assert any("name" in e.lower() or "empty" in e.lower() for e in errors)

    def test_whitespace_only_name_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(name="   "))
        assert len(errors) >= 1

    def test_name_too_long_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(name="A" * 101))
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# Age validation
# ---------------------------------------------------------------------------


class TestAgeValidation:
    def test_age_above_120_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(age=121))
        assert len(errors) >= 1
        assert any("age" in e.lower() or "120" in e for e in errors)

    def test_negative_age_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(age=-1))
        assert len(errors) >= 1

    def test_age_exactly_0_is_valid(self) -> None:
        errors = validate_inputs(_valid_data(age=0))
        assert errors == []

    def test_age_exactly_120_is_valid(self) -> None:
        errors = validate_inputs(_valid_data(age=120))
        assert errors == []


# ---------------------------------------------------------------------------
# Income validation
# ---------------------------------------------------------------------------


class TestIncomeValidation:
    def test_negative_income_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(annual_income=-1.0))
        assert len(errors) >= 1
        assert any("income" in e.lower() or "negative" in e.lower() for e in errors)

    def test_zero_income_is_valid(self) -> None:
        errors = validate_inputs(_valid_data(annual_income=0.0))
        assert errors == []

    def test_large_income_is_valid(self) -> None:
        errors = validate_inputs(_valid_data(annual_income=9_999_999.0))
        assert errors == []


# ---------------------------------------------------------------------------
# Enum field validation
# ---------------------------------------------------------------------------


class TestEnumValidation:
    def test_invalid_gender_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(gender="Unknown"))
        assert len(errors) >= 1

    def test_invalid_state_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(state="Wakanda"))
        assert len(errors) >= 1

    def test_invalid_employment_status_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(employment_status="Retired"))
        assert len(errors) >= 1

    def test_invalid_caste_returns_error(self) -> None:
        errors = validate_inputs(_valid_data(caste_category="Forward"))
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# Multiple errors at once
# ---------------------------------------------------------------------------


class TestMultipleErrors:
    def test_multiple_invalid_fields_return_multiple_errors(self) -> None:
        bad_data = {
            "name": "",
            "age": -5,
            "gender": "???",
            "state": "Wakanda",
            "annual_income": -100.0,
            "employment_status": "Retired",
            "caste_category": "Other",
        }
        errors = validate_inputs(bad_data)
        assert len(errors) >= 5
