"""Data model dataclasses for the Welfare Eligibility Checker.

These are pure data containers — no business logic lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Citizen:
    """Represents a citizen submitting a welfare eligibility check.

    Attributes:
        name: Full name of the citizen.
        age: Age in years (0–120).
        gender: One of 'Male', 'Female', 'Other'.
        state: Indian state or union territory.
        annual_income: Annual household income in INR (>= 0).
        employment_status: One of 'Employed', 'Unemployed', 'Self-Employed', 'Student'.
        caste_category: One of 'General', 'OBC', 'SC', 'ST'.
    """

    name: str
    age: int
    gender: str
    state: str
    annual_income: float
    employment_status: str
    caste_category: str


@dataclass
class EligibilityRule:
    """A single eligibility rule that checks one field on a Citizen.

    Attributes:
        field: Name of the Citizen attribute to evaluate (e.g. 'age').
        operator: Comparison operator — one of '>=', '<=', '==', '!='.
        value: The threshold or target value to compare against.
    """

    field: str
    operator: str
    value: Any


@dataclass
class Scheme:
    """Represents a government welfare scheme and its eligibility criteria.

    Attributes:
        scheme_id: Unique identifier string (e.g. 'PM_AWAS').
        name: Human-readable display name.
        description: Plain-language description of the scheme.
        applicable_states: List of state names; use ['All'] for nationwide schemes.
        guidance: Instructions on how and where to apply.
        documents_required: List of documents needed to apply.
        rules: Ordered list of EligibilityRule objects that must ALL pass.
    """

    scheme_id: str
    name: str
    description: str
    applicable_states: list[str]
    guidance: str
    documents_required: list[str]
    rules: list[EligibilityRule] = field(default_factory=list)


@dataclass
class EligibilityResult:
    """The eligibility outcome for one citizen against one scheme.

    Attributes:
        scheme_name: Display name of the scheme.
        status: 'Eligible' or 'Not Eligible'.
        reasons: One human-readable reason string per rule evaluated.
    """

    scheme_name: str
    status: str
    reasons: list[str] = field(default_factory=list)
