"""Input validation for citizen welfare eligibility form data.

All validation logic lives here — completely independent of Streamlit.
The public function ``validate_inputs`` accepts a plain dict and returns
a list of human-readable error strings (empty list means all inputs are valid).
"""

from __future__ import annotations

import re

from core.exceptions import InvalidAgeError, InvalidIncomeError, InvalidInputError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_GENDERS: list[str] = ["Male", "Female", "Other"]

VALID_EMPLOYMENT_STATUSES: list[str] = [
    "Employed",
    "Unemployed",
    "Self-Employed",
    "Student",
]

VALID_CASTE_CATEGORIES: list[str] = ["General", "OBC", "SC", "ST"]

VALID_STATES: list[str] = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    # Union Territories
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
]

# Allows any Unicode letter (including combining marks/diacritics used in
# Devanagari, Tamil, etc.), spaces, hyphens, and apostrophes.
# \w alone misses Unicode combining characters (category Mc/Mn) so we
# use a broad "not a digit-or-ASCII-punctuation" approach instead.
_NAME_PATTERN: re.Pattern[str] = re.compile(
    r"^[^\d!@#$%^&*()\[\]{};:\"\\|<>?,/~`+=]+$",
    re.UNICODE,
)

_MAX_NAME_LENGTH: int = 100
_MIN_AGE: int = 0
_MAX_AGE: int = 120


# ---------------------------------------------------------------------------
# Private field validators
# ---------------------------------------------------------------------------


def _validate_name(name: str) -> bool:
    """Return True if name is non-empty, within length, and contains valid characters."""
    if not name or not name.strip():
        return False
    if len(name.strip()) > _MAX_NAME_LENGTH:
        return False
    # Strip leading/trailing whitespace before pattern check
    return bool(_NAME_PATTERN.match(name.strip()))


def _validate_age(age: int) -> bool:
    """Return True if age is an integer within 0–120 inclusive.

    Raises:
        InvalidAgeError: If age is outside the valid range.
    """
    if not isinstance(age, int) or isinstance(age, bool):
        raise InvalidAgeError(age)
    if age < _MIN_AGE or age > _MAX_AGE:
        raise InvalidAgeError(age)
    return True


def _validate_income(income: float) -> bool:
    """Return True if income is a non-negative number.

    Raises:
        InvalidIncomeError: If income is negative.
    """
    if income < 0:
        raise InvalidIncomeError(income)
    return True


def _validate_state(state: str) -> bool:
    """Return True if state is in the recognised list of Indian states/UTs."""
    return state in VALID_STATES


def _validate_enum_field(value: str, valid_values: list[str]) -> bool:
    """Return True if value is one of the allowed options."""
    return value in valid_values


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_inputs(data: dict) -> list[str]:
    """Validate all citizen form fields and return a list of error messages.

    Calls each individual field validator, collects any errors, and returns
    them as human-readable English strings. An empty list means all inputs
    are valid.

    Args:
        data: A dict with the following expected keys:
            ``name``, ``age``, ``gender``, ``state``, ``annual_income``,
            ``employment_status``, ``caste_category``.

    Returns:
        A (possibly empty) list of validation error message strings.
    """
    errors: list[str] = []

    # --- name ---
    name = data.get("name", "")
    if not _validate_name(str(name)):
        if not str(name).strip():
            errors.append("Full name cannot be empty.")
        else:
            errors.append(
                "Name must contain only letters, spaces, or valid unicode characters (max 100 characters)."
            )

    # --- age ---
    age = data.get("age")
    try:
        _validate_age(int(age))  # type: ignore[arg-type]
    except (InvalidAgeError, TypeError, ValueError):
        errors.append(f"Age must be between {_MIN_AGE} and {_MAX_AGE}.")

    # --- annual_income ---
    income = data.get("annual_income")
    try:
        _validate_income(float(income))  # type: ignore[arg-type]
    except (InvalidIncomeError, TypeError, ValueError):
        errors.append("Annual income cannot be negative.")

    # --- gender ---
    gender = data.get("gender", "")
    if not _validate_enum_field(str(gender), VALID_GENDERS):
        errors.append(f"Please select a valid gender option. Valid options: {VALID_GENDERS}.")

    # --- state ---
    state = data.get("state", "")
    if not _validate_state(str(state)):
        errors.append("Please select a valid state or union territory.")

    # --- employment_status ---
    employment = data.get("employment_status", "")
    if not _validate_enum_field(str(employment), VALID_EMPLOYMENT_STATUSES):
        errors.append(
            f"Please select a valid employment status. Valid options: {VALID_EMPLOYMENT_STATUSES}."
        )

    # --- caste_category ---
    caste = data.get("caste_category", "")
    if not _validate_enum_field(str(caste), VALID_CASTE_CATEGORIES):
        errors.append(
            f"Please select a valid caste category. Valid options: {VALID_CASTE_CATEGORIES}."
        )

    return errors
