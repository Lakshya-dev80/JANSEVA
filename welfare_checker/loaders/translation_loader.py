"""JSON loader for UI translation strings.

Reads data/translations.json and returns a nested dict keyed by language code.
Raises SchemeDataError for missing files or invalid JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.exceptions import SchemeDataError


def load_translations(filepath: str) -> dict[str, dict[str, str]]:
    """Load all translation label strings from a JSON file.

    The file must be a JSON object keyed by language code (e.g. ``"en"``,
    ``"hi"``, ``"ta"``), where each value is a flat dict mapping label keys
    to translated strings.

    Args:
        filepath: Path to the translations JSON file.

    Returns:
        A nested ``dict[language_code, dict[label_key, translated_string]]``.

    Raises:
        SchemeDataError: If the file is missing or contains invalid JSON.
    """
    path = Path(filepath)

    if not path.exists():
        raise SchemeDataError(f"Translations file not found: {filepath}")

    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise SchemeDataError(f"Invalid JSON in translations file '{filepath}': {exc}") from exc

    if not isinstance(data, dict):
        raise SchemeDataError(
            f"Translations file must contain a JSON object, got {type(data).__name__}"
        )

    return data  # type: ignore[return-value]


def get_labels(translations: dict[str, dict[str, str]], language_code: str) -> dict[str, str]:
    """Return the label dict for the given language code.

    Falls back to English (``"en"``) if the requested language is not found.

    Args:
        translations: The full translations dict returned by :func:`load_translations`.
        language_code: The desired language code (e.g. ``"hi"``).

    Returns:
        A flat dict mapping label keys to translated strings.
    """
    return translations.get(language_code, translations.get("en", {}))
