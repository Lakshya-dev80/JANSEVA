"""Unit tests for JSON loaders (loaders/scheme_loader.py, loaders/translation_loader.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.exceptions import SchemeDataError
from core.models import EligibilityRule, Scheme
from loaders.scheme_loader import load_schemes
from loaders.translation_loader import get_labels, load_translations


# ---------------------------------------------------------------------------
# Helpers — build valid JSON payloads
# ---------------------------------------------------------------------------


def _make_scheme_entry(**overrides) -> dict:
    """Return a valid scheme dict, optionally overriding fields."""
    base = {
        "scheme_id": "TEST",
        "name": "Test Scheme",
        "description": "A scheme for testing.",
        "applicable_states": ["All"],
        "guidance": "Apply here.",
        "documents_required": ["Aadhaar Card"],
        "rules": [
            {"field": "age", "operator": ">=", "value": 18},
            {"field": "annual_income", "operator": "<=", "value": 100000},
        ],
    }
    base.update(overrides)
    return base


def _write_json(path: Path, data) -> str:
    """Write data as JSON to path and return the file path as a string."""
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# load_schemes — happy path
# ---------------------------------------------------------------------------


class TestLoadSchemes:
    def test_loads_valid_schemes_file(self, tmp_path: Path) -> None:
        filepath = _write_json(tmp_path / "schemes.json", [_make_scheme_entry()])
        schemes = load_schemes(filepath)
        assert len(schemes) == 1
        assert isinstance(schemes[0], Scheme)
        assert schemes[0].scheme_id == "TEST"
        assert schemes[0].name == "Test Scheme"

    def test_rules_are_parsed_to_eligibility_rule(self, tmp_path: Path) -> None:
        filepath = _write_json(tmp_path / "schemes.json", [_make_scheme_entry()])
        schemes = load_schemes(filepath)
        assert len(schemes[0].rules) == 2
        assert isinstance(schemes[0].rules[0], EligibilityRule)
        assert schemes[0].rules[0].field == "age"
        assert schemes[0].rules[0].operator == ">="
        assert schemes[0].rules[0].value == 18

    def test_applicable_states_all(self, tmp_path: Path) -> None:
        filepath = _write_json(tmp_path / "schemes.json", [_make_scheme_entry()])
        schemes = load_schemes(filepath)
        assert schemes[0].applicable_states == ["All"]

    def test_loads_multiple_schemes(self, tmp_path: Path) -> None:
        entries = [
            _make_scheme_entry(scheme_id="S1", name="Scheme 1"),
            _make_scheme_entry(scheme_id="S2", name="Scheme 2"),
            _make_scheme_entry(scheme_id="S3", name="Scheme 3"),
        ]
        filepath = _write_json(tmp_path / "schemes.json", entries)
        schemes = load_schemes(filepath)
        assert len(schemes) == 3
        assert [s.scheme_id for s in schemes] == ["S1", "S2", "S3"]

    def test_empty_rules_list_is_valid(self, tmp_path: Path) -> None:
        filepath = _write_json(tmp_path / "schemes.json", [_make_scheme_entry(rules=[])])
        schemes = load_schemes(filepath)
        assert schemes[0].rules == []


# ---------------------------------------------------------------------------
# load_schemes — error paths
# ---------------------------------------------------------------------------


class TestLoadSchemesErrors:
    def test_raises_when_file_not_found(self) -> None:
        with pytest.raises(SchemeDataError, match="not found"):
            load_schemes("/nonexistent/path/schemes.json")

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "schemes.json"
        bad_file.write_text("{ this is not valid json }", encoding="utf-8")
        with pytest.raises(SchemeDataError, match="Invalid JSON"):
            load_schemes(str(bad_file))

    def test_raises_when_root_is_not_list(self, tmp_path: Path) -> None:
        filepath = _write_json(tmp_path / "schemes.json", {"key": "value"})
        with pytest.raises(SchemeDataError):
            load_schemes(filepath)

    def test_raises_when_scheme_missing_name(self, tmp_path: Path) -> None:
        entry = _make_scheme_entry()
        del entry["name"]
        filepath = _write_json(tmp_path / "schemes.json", [entry])
        with pytest.raises(SchemeDataError, match="missing required key"):
            load_schemes(filepath)

    def test_raises_when_scheme_missing_scheme_id(self, tmp_path: Path) -> None:
        entry = _make_scheme_entry()
        del entry["scheme_id"]
        filepath = _write_json(tmp_path / "schemes.json", [entry])
        with pytest.raises(SchemeDataError, match="missing required key"):
            load_schemes(filepath)

    def test_raises_when_scheme_missing_rules(self, tmp_path: Path) -> None:
        entry = _make_scheme_entry()
        del entry["rules"]
        filepath = _write_json(tmp_path / "schemes.json", [entry])
        with pytest.raises(SchemeDataError, match="missing required key"):
            load_schemes(filepath)

    def test_raises_when_rule_missing_field(self, tmp_path: Path) -> None:
        bad_rule = {"operator": ">=", "value": 18}  # missing "field"
        entry = _make_scheme_entry(rules=[bad_rule])
        filepath = _write_json(tmp_path / "schemes.json", [entry])
        with pytest.raises(SchemeDataError, match="missing required key"):
            load_schemes(filepath)

    def test_raises_when_rule_missing_operator(self, tmp_path: Path) -> None:
        bad_rule = {"field": "age", "value": 18}  # missing "operator"
        entry = _make_scheme_entry(rules=[bad_rule])
        filepath = _write_json(tmp_path / "schemes.json", [entry])
        with pytest.raises(SchemeDataError, match="missing required key"):
            load_schemes(filepath)

    def test_raises_when_rule_missing_value(self, tmp_path: Path) -> None:
        bad_rule = {"field": "age", "operator": ">="}  # missing "value"
        entry = _make_scheme_entry(rules=[bad_rule])
        filepath = _write_json(tmp_path / "schemes.json", [entry])
        with pytest.raises(SchemeDataError, match="missing required key"):
            load_schemes(filepath)


# ---------------------------------------------------------------------------
# load_translations — happy path
# ---------------------------------------------------------------------------


class TestLoadTranslations:
    def test_loads_valid_translations(self, tmp_path: Path) -> None:
        data = {
            "en": {"app_title": "Test App", "btn_check": "Check"},
            "hi": {"app_title": "टेस्ट ऐप", "btn_check": "जाँचें"},
        }
        filepath = _write_json(tmp_path / "translations.json", data)
        translations = load_translations(filepath)
        assert "en" in translations
        assert "hi" in translations
        assert translations["en"]["app_title"] == "Test App"

    def test_all_keys_preserved(self, tmp_path: Path) -> None:
        data = {"en": {"key1": "val1", "key2": "val2"}}
        filepath = _write_json(tmp_path / "translations.json", data)
        translations = load_translations(filepath)
        assert translations["en"]["key1"] == "val1"
        assert translations["en"]["key2"] == "val2"


# ---------------------------------------------------------------------------
# load_translations — error paths
# ---------------------------------------------------------------------------


class TestLoadTranslationsErrors:
    def test_raises_when_file_not_found(self) -> None:
        with pytest.raises(SchemeDataError, match="not found"):
            load_translations("/nonexistent/translations.json")

    def test_raises_on_malformed_json(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "translations.json"
        bad_file.write_text("not json at all", encoding="utf-8")
        with pytest.raises(SchemeDataError, match="Invalid JSON"):
            load_translations(str(bad_file))

    def test_raises_when_root_is_not_dict(self, tmp_path: Path) -> None:
        filepath = _write_json(tmp_path / "translations.json", ["en", "hi"])
        with pytest.raises(SchemeDataError):
            load_translations(filepath)


# ---------------------------------------------------------------------------
# get_labels — helper tests
# ---------------------------------------------------------------------------


class TestGetLabels:
    def test_returns_correct_language(self) -> None:
        translations = {
            "en": {"title": "English Title"},
            "hi": {"title": "हिन्दी शीर्षक"},
        }
        labels = get_labels(translations, "hi")
        assert labels["title"] == "हिन्दी शीर्षक"

    def test_falls_back_to_english_for_unknown_language(self) -> None:
        translations = {
            "en": {"title": "English Title"},
        }
        labels = get_labels(translations, "fr")
        assert labels["title"] == "English Title"

    def test_returns_empty_dict_when_no_fallback(self) -> None:
        translations: dict = {}
        labels = get_labels(translations, "fr")
        assert labels == {}
