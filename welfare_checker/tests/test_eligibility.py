"""Unit tests for the eligibility engine (core/eligibility.py)."""

from __future__ import annotations

import pytest

from core.eligibility import check_all_schemes, check_eligibility
from core.exceptions import SchemeDataError
from core.models import Citizen, EligibilityRule, EligibilityResult, Scheme


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def base_citizen() -> Citizen:
    """A baseline citizen that meets typical eligibility criteria."""
    return Citizen(
        name="Test User",
        age=30,
        gender="Male",
        state="Maharashtra",
        annual_income=80000.0,
        employment_status="Unemployed",
        caste_category="General",
    )


@pytest.fixture
def simple_scheme() -> Scheme:
    """A scheme with basic age and income rules, available in all states."""
    return Scheme(
        scheme_id="TEST_SCHEME",
        name="Test Scheme",
        description="A test scheme.",
        applicable_states=["All"],
        guidance="Apply at test office.",
        documents_required=["Aadhaar Card"],
        rules=[
            EligibilityRule(field="age", operator=">=", value=18),
            EligibilityRule(field="annual_income", operator="<=", value=100000),
        ],
    )


# ---------------------------------------------------------------------------
# check_eligibility tests
# ---------------------------------------------------------------------------


class TestCheckEligibility:
    def test_eligible_when_all_rules_pass(self, base_citizen: Citizen, simple_scheme: Scheme) -> None:
        result = check_eligibility(base_citizen, simple_scheme)
        assert result.status == "Eligible"
        assert result.scheme_name == "Test Scheme"

    def test_not_eligible_when_income_too_high(self, simple_scheme: Scheme) -> None:
        rich_citizen = Citizen(
            name="Rich User",
            age=30,
            gender="Male",
            state="Maharashtra",
            annual_income=200000.0,  # Exceeds 100000 limit
            employment_status="Employed",
            caste_category="General",
        )
        result = check_eligibility(rich_citizen, simple_scheme)
        assert result.status == "Not Eligible"

    def test_not_eligible_when_age_too_young(self, simple_scheme: Scheme) -> None:
        young_citizen = Citizen(
            name="Young User",
            age=10,  # Below 18 requirement
            gender="Female",
            state="Karnataka",
            annual_income=50000.0,
            employment_status="Student",
            caste_category="OBC",
        )
        result = check_eligibility(young_citizen, simple_scheme)
        assert result.status == "Not Eligible"

    def test_not_eligible_when_state_not_covered(self, base_citizen: Citizen) -> None:
        state_specific_scheme = Scheme(
            scheme_id="STATE_SCHEME",
            name="State Specific Scheme",
            description="Only for Gujarat.",
            applicable_states=["Gujarat"],
            guidance="Apply in Gujarat.",
            documents_required=["Aadhaar Card"],
            rules=[EligibilityRule(field="age", operator=">=", value=18)],
        )
        result = check_eligibility(base_citizen, state_specific_scheme)
        assert result.status == "Not Eligible"
        assert any("not covered" in r or "available in" in r for r in result.reasons)

    def test_eligible_when_state_is_all(self, base_citizen: Citizen) -> None:
        nationwide_scheme = Scheme(
            scheme_id="NATIONAL",
            name="National Scheme",
            description="Available everywhere.",
            applicable_states=["All"],
            guidance="Apply anywhere.",
            documents_required=["Aadhaar Card"],
            rules=[EligibilityRule(field="age", operator=">=", value=18)],
        )
        result = check_eligibility(base_citizen, nationwide_scheme)
        assert result.status == "Eligible"

    def test_income_exactly_at_threshold_is_eligible(self, simple_scheme: Scheme) -> None:
        """Income exactly at the limit must be Eligible (boundary inclusive)."""
        threshold_citizen = Citizen(
            name="Boundary User",
            age=25,
            gender="Male",
            state="Delhi",
            annual_income=100000.0,  # Exactly at the limit
            employment_status="Unemployed",
            caste_category="General",
        )
        result = check_eligibility(threshold_citizen, simple_scheme)
        assert result.status == "Eligible"

    def test_all_reasons_included_in_result(self, base_citizen: Citizen, simple_scheme: Scheme) -> None:
        """Result reasons must contain one entry per rule."""
        result = check_eligibility(base_citizen, simple_scheme)
        assert len(result.reasons) == len(simple_scheme.rules)

    def test_reasons_included_even_when_not_eligible(self, simple_scheme: Scheme) -> None:
        """Reasons are returned even when some rules fail."""
        citizen = Citizen(
            name="Fail User",
            age=10,  # Fails age rule
            gender="Male",
            state="Delhi",
            annual_income=200000.0,  # Fails income rule too
            employment_status="Unemployed",
            caste_category="General",
        )
        result = check_eligibility(citizen, simple_scheme)
        assert result.status == "Not Eligible"
        assert len(result.reasons) == 2

    def test_raises_scheme_data_error_for_unknown_operator(self, base_citizen: Citizen) -> None:
        bad_scheme = Scheme(
            scheme_id="BAD",
            name="Bad Scheme",
            description="Bad operator.",
            applicable_states=["All"],
            guidance="N/A",
            documents_required=[],
            rules=[EligibilityRule(field="age", operator=">>", value=18)],
        )
        with pytest.raises(SchemeDataError, match="Unsupported operator"):
            check_eligibility(base_citizen, bad_scheme)

    def test_raises_scheme_data_error_for_unknown_field(self, base_citizen: Citizen) -> None:
        bad_scheme = Scheme(
            scheme_id="BAD2",
            name="Bad Field Scheme",
            description="Bad field name.",
            applicable_states=["All"],
            guidance="N/A",
            documents_required=[],
            rules=[EligibilityRule(field="nonexistent_field", operator=">=", value=0)],
        )
        with pytest.raises(SchemeDataError, match="unknown citizen field"):
            check_eligibility(base_citizen, bad_scheme)

    def test_equality_operator(self, base_citizen: Citizen) -> None:
        gender_scheme = Scheme(
            scheme_id="FEMALE_SCHEME",
            name="Female Only",
            description="For women.",
            applicable_states=["All"],
            guidance="Apply.",
            documents_required=[],
            rules=[EligibilityRule(field="gender", operator="==", value="Female")],
        )
        result = check_eligibility(base_citizen, gender_scheme)
        assert result.status == "Not Eligible"

    def test_not_equal_operator(self, base_citizen: Citizen) -> None:
        non_general_scheme = Scheme(
            scheme_id="RESERVED",
            name="Reserved Category",
            description="Not for General.",
            applicable_states=["All"],
            guidance="Apply.",
            documents_required=[],
            rules=[EligibilityRule(field="caste_category", operator="!=", value="General")],
        )
        # base_citizen is General, so this should fail
        result = check_eligibility(base_citizen, non_general_scheme)
        assert result.status == "Not Eligible"


# ---------------------------------------------------------------------------
# check_all_schemes tests
# ---------------------------------------------------------------------------


class TestCheckAllSchemes:
    def test_eligible_results_appear_first(self, base_citizen: Citizen) -> None:
        eligible_scheme = Scheme(
            scheme_id="EASY",
            name="Easy Scheme",
            description="Very easy to qualify.",
            applicable_states=["All"],
            guidance="Apply.",
            documents_required=[],
            rules=[EligibilityRule(field="age", operator=">=", value=0)],  # Everyone passes
        )
        hard_scheme = Scheme(
            scheme_id="HARD",
            name="Hard Scheme",
            description="Very hard to qualify.",
            applicable_states=["All"],
            guidance="Apply.",
            documents_required=[],
            rules=[EligibilityRule(field="annual_income", operator="<=", value=1)],  # No one passes
        )
        results = check_all_schemes(base_citizen, [hard_scheme, eligible_scheme])
        assert results[0].status == "Eligible"
        assert results[1].status == "Not Eligible"

    def test_returns_one_result_per_scheme(self, base_citizen: Citizen) -> None:
        schemes = [
            Scheme(
                scheme_id=f"S{i}",
                name=f"Scheme {i}",
                description="",
                applicable_states=["All"],
                guidance="",
                documents_required=[],
                rules=[],
            )
            for i in range(3)
        ]
        results = check_all_schemes(base_citizen, schemes)
        assert len(results) == 3

    def test_empty_schemes_list_returns_empty(self, base_citizen: Citizen) -> None:
        results = check_all_schemes(base_citizen, [])
        assert results == []
