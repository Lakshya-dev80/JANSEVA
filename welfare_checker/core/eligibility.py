"""Eligibility engine — pure business logic, zero Streamlit imports.

Public API
----------
check_eligibility(citizen, scheme) -> EligibilityResult
check_all_schemes(citizen, schemes) -> list[EligibilityResult]
"""

from __future__ import annotations

import operator as _op
from typing import Any, Callable

from core.exceptions import SchemeDataError
from core.models import Citizen, EligibilityResult, EligibilityRule, Scheme

# ---------------------------------------------------------------------------
# Operator dispatch table
# ---------------------------------------------------------------------------

_OPERATOR_MAP: dict[str, Callable[[Any, Any], bool]] = {
    ">=": _op.ge,
    "<=": _op.le,
    "==": _op.eq,
    "!=": _op.ne,
}

_OPERATOR_DESCRIPTIONS: dict[str, str] = {
    ">=": "at least",
    "<=": "at most",
    "==": "equal to",
    "!=": "not equal to",
}

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _apply_rule(citizen: Citizen, rule: EligibilityRule) -> tuple[bool, str]:
    """Evaluate a single eligibility rule against a citizen's data.

    Args:
        citizen: The :class:`~core.models.Citizen` being evaluated.
        rule: The :class:`~core.models.EligibilityRule` to apply.

    Returns:
        A ``(passed, reason_message)`` tuple where *passed* is ``True`` when
        the citizen satisfies the rule and *reason_message* is a human-readable
        explanation either way.

    Raises:
        SchemeDataError: If ``rule.operator`` is unsupported or ``rule.field``
            does not exist on :class:`~core.models.Citizen`.
    """
    # Validate operator
    if rule.operator not in _OPERATOR_MAP:
        raise SchemeDataError(
            f"Unsupported operator '{rule.operator}'. "
            f"Allowed operators: {sorted(_OPERATOR_MAP.keys())}"
        )

    # Validate field exists on Citizen
    try:
        citizen_value = getattr(citizen, rule.field)
    except AttributeError as exc:
        raise SchemeDataError(
            f"Rule references unknown citizen field '{rule.field}'. "
            f"Check your schemes.json for typos."
        ) from exc

    compare_fn = _OPERATOR_MAP[rule.operator]
    passed: bool = compare_fn(citizen_value, rule.value)

    op_desc = _OPERATOR_DESCRIPTIONS[rule.operator]
    field_label = rule.field.replace("_", " ").title()

    if passed:
        reason = f"✅ {field_label} ({citizen_value}) is {op_desc} {rule.value} — requirement met."
    else:
        reason = f"❌ {field_label} ({citizen_value}) must be {op_desc} {rule.value} — requirement not met."

    return passed, reason


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_eligibility(citizen: Citizen, scheme: Scheme) -> EligibilityResult:
    """Check whether a citizen is eligible for a single welfare scheme.

    State filtering is applied first: if the scheme is not available in the
    citizen's state the result is immediately ``"Not Eligible"``.

    Then each rule in ``scheme.rules`` is evaluated. If **all** rules pass,
    the status is ``"Eligible"``; if any rule fails, it is ``"Not Eligible"``.
    All per-rule reasons (pass and fail) are included in the result.

    Args:
        citizen: The citizen to evaluate.
        scheme: The scheme to check against.

    Returns:
        An :class:`~core.models.EligibilityResult` with ``status`` and
        ``reasons``.

    Raises:
        SchemeDataError: Propagated from :func:`_apply_rule` if the scheme
            JSON contains an unknown operator or field name.
    """
    reasons: list[str] = []

    # --- State filter ---
    if scheme.applicable_states != ["All"] and citizen.state not in scheme.applicable_states:
        reasons.append(
            f"❌ This scheme is only available in: {', '.join(scheme.applicable_states)}. "
            f"Your state ({citizen.state}) is not covered."
        )
        return EligibilityResult(
            scheme_name=scheme.name,
            status="Not Eligible",
            reasons=reasons,
        )

    # --- Rule evaluation ---
    all_passed = True
    for rule in scheme.rules:
        passed, reason = _apply_rule(citizen, rule)
        reasons.append(reason)
        if not passed:
            all_passed = False

    status = "Eligible" if all_passed else "Not Eligible"
    return EligibilityResult(scheme_name=scheme.name, status=status, reasons=reasons)


def check_all_schemes(citizen: Citizen, schemes: list[Scheme]) -> list[EligibilityResult]:
    """Run eligibility check for every scheme and return sorted results.

    Eligible schemes are listed first, followed by ineligible ones.

    Args:
        citizen: The citizen to evaluate.
        schemes: All available welfare schemes.

    Returns:
        A list of :class:`~core.models.EligibilityResult` objects sorted so
        that ``"Eligible"`` results appear before ``"Not Eligible"`` results.
    """
    results: list[EligibilityResult] = [check_eligibility(citizen, scheme) for scheme in schemes]
    # Sort: "Eligible" first (sort key: 0), "Not Eligible" second (sort key: 1)
    results.sort(key=lambda r: 0 if r.status == "Eligible" else 1)
    return results
