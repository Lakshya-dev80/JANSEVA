"""JSON loader for welfare scheme definitions.

Reads data/schemes.json and returns a list of typed Scheme dataclass objects.
Raises SchemeDataError for missing files, invalid JSON, or malformed entries.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.exceptions import SchemeDataError
from core.models import EligibilityRule, Scheme

# Keys required at the scheme level and at each rule level
_REQUIRED_SCHEME_KEYS: frozenset[str] = frozenset(
    {"scheme_id", "name", "description", "applicable_states", "guidance", "documents_required", "rules"}
)
_REQUIRED_RULE_KEYS: frozenset[str] = frozenset({"field", "operator", "value"})


def load_schemes(filepath: str) -> list[Scheme]:
    """Load and parse all welfare schemes from a JSON file.

    Args:
        filepath: Path to the schemes JSON file.

    Returns:
        A list of :class:`~core.models.Scheme` objects.

    Raises:
        SchemeDataError: If the file is missing, not valid JSON, or any entry
            is missing a required key.
    """
    path = Path(filepath)

    if not path.exists():
        raise SchemeDataError(f"Schemes file not found: {filepath}")

    try:
        with path.open(encoding="utf-8") as fh:
            raw_data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise SchemeDataError(f"Invalid JSON in schemes file '{filepath}': {exc}") from exc

    if not isinstance(raw_data, list):
        raise SchemeDataError(f"Schemes file must contain a JSON array, got {type(raw_data).__name__}")

    schemes: list[Scheme] = []
    for index, entry in enumerate(raw_data):
        scheme = _parse_scheme(entry, index)
        schemes.append(scheme)

    return schemes


def _parse_scheme(entry: dict, index: int) -> Scheme:
    """Parse a single scheme dict into a :class:`~core.models.Scheme`.

    Args:
        entry: Raw dictionary from the JSON array.
        index: Position in the array, used for error messages.

    Returns:
        A populated :class:`~core.models.Scheme` instance.

    Raises:
        SchemeDataError: If any required key is absent.
    """
    missing = _REQUIRED_SCHEME_KEYS - entry.keys()
    if missing:
        raise SchemeDataError(
            f"Scheme at index {index} is missing required key(s): {sorted(missing)}"
        )

    rules: list[EligibilityRule] = []
    for rule_index, rule_entry in enumerate(entry["rules"]):
        rule = _parse_rule(rule_entry, entry.get("scheme_id", f"index={index}"), rule_index)
        rules.append(rule)

    return Scheme(
        scheme_id=entry["scheme_id"],
        name=entry["name"],
        description=entry["description"],
        applicable_states=entry["applicable_states"],
        guidance=entry["guidance"],
        documents_required=entry["documents_required"],
        rules=rules,
    )


def _parse_rule(entry: dict, scheme_id: str, rule_index: int) -> EligibilityRule:
    """Parse a single rule dict into an :class:`~core.models.EligibilityRule`.

    Args:
        entry: Raw dictionary for the rule.
        scheme_id: Parent scheme ID, used for error messages.
        rule_index: Position in the rules list.

    Returns:
        A populated :class:`~core.models.EligibilityRule` instance.

    Raises:
        SchemeDataError: If any required key is absent.
    """
    missing = _REQUIRED_RULE_KEYS - entry.keys()
    if missing:
        raise SchemeDataError(
            f"Rule at index {rule_index} in scheme '{scheme_id}' is missing required key(s): {sorted(missing)}"
        )

    return EligibilityRule(
        field=entry["field"],
        operator=entry["operator"],
        value=entry["value"],
    )
