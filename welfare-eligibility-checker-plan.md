# Welfare Eligibility Checker — Project Plan

## Top-Level Overview

**Goal:** Build a beginner-friendly Python + Streamlit web app that lets citizens check their eligibility for Indian government welfare schemes.

**Scope:**
- Pure Python business logic (no Streamlit imports) in a `core/` package
- Streamlit UI layer in `app.py` that only calls `core/` functions
- All scheme data stored in `data/schemes.json`
- All UI text stored in `data/translations.json`
- Full pytest coverage for all non-UI modules (`core/` and `data/` loading)
- No database, no authentication, no external API calls

**Non-goals:**
- Real-time scheme data from government APIs
- User accounts or saved sessions
- Admin panel for editing schemes

**Approach:** Define data models as Python dataclasses with type hints, write pure functions for validation and eligibility checking, load scheme and translation data from JSON files at startup, and wire everything together in a thin Streamlit `app.py`.

---

## Architecture Overview

```
welfare_checker/
│
├── app.py                        # Streamlit entry point — UI only
│
├── core/
│   ├── __init__.py
│   ├── models.py                 # Citizen, Scheme, EligibilityResult dataclasses
│   ├── eligibility.py            # check_eligibility(), check_all_schemes()
│   ├── validation.py             # validate_inputs() and field validators
│   └── exceptions.py             # Custom exception classes
│
├── data/
│   ├── schemes.json              # All scheme definitions and rules
│   └── translations.json         # UI label strings per language code
│
├── loaders/
│   ├── __init__.py
│   ├── scheme_loader.py          # load_schemes() — parses schemes.json
│   └── translation_loader.py    # load_translations() — parses translations.json
│
└── tests/
    ├── __init__.py
    ├── test_eligibility.py
    ├── test_validation.py
    └── test_loaders.py
```

---

## Sub-Task 1 — Define Data Models

**Status:** [ ] pending

### Intent
Establish the shared data structures used across all modules. Every other sub-task depends on these. Defining them first ensures consistent type hints throughout the project.

### Expected Outcomes
- `core/models.py` contains three dataclasses: `Citizen`, `Scheme`, and `EligibilityResult`
- `core/exceptions.py` contains all custom exception classes
- All fields have type hints and docstrings
- No business logic is present in this file — pure data containers only

### Todo List
1. Create `core/__init__.py` (empty)
2. Create `core/exceptions.py` with the following exception classes:
   - `InvalidAgeError(ValueError)` — raised when age is outside 0–120
   - `InvalidIncomeError(ValueError)` — raised when income is negative
   - `InvalidInputError(ValueError)` — raised for any other field validation failure
   - `SchemeDataError(Exception)` — raised when a scheme JSON entry is malformed
3. Create `core/models.py` with the following dataclasses:
   - `Citizen` — all citizen-provided fields (see Data Models section below)
   - `EligibilityRule` — a single rule object matching JSON rule structure
   - `Scheme` — scheme metadata plus its list of `EligibilityRule` objects
   - `EligibilityResult` — result for one scheme: scheme name, status string, list of reason strings

### Relevant Context
- `EligibilityRule` must mirror the JSON rule shape: `{"field": str, "operator": str, "value": Any}`
- `EligibilityResult.status` must be one of three string literals: `"Eligible"`, `"Not Eligible"`, `"Unknown"`
- Use `@dataclass` and `field()` from the `dataclasses` standard library

---

## Sub-Task 2 — JSON Data Files

**Status:** [ ] pending

### Intent
Create the static data files that drive the app's content. Keeping data in JSON makes it easy for beginners to add or edit schemes and translations without touching Python code.

### Expected Outcomes
- `data/schemes.json` contains at least 6 well-known Indian central schemes with full rule sets
- `data/translations.json` contains UI labels in English, Hindi, and Tamil
- Both files are valid, well-formatted JSON
- Schema is consistent and matches the `Scheme` and `EligibilityRule` dataclasses

### Todo List
1. Create `data/schemes.json` with the following schemes (each with `scheme_id`, `name`, `description`, `applicable_states`, `guidance`, `documents_required`, and `rules` list):
   - PM Awas Yojana (housing — income + age rules)
   - MGNREGA (employment — employment status + state rule)
   - National Scholarship Portal (education — student + income + age rules)
   - PM-KISAN (farmer income support — income + gender-neutral)
   - Sukanya Samriddhi Yojana (girl child savings — age + gender rules)
   - Ayushman Bharat PM-JAY (health insurance — income rule)
2. Create `data/translations.json` keyed by language code (`"en"`, `"hi"`, `"ta"`) with labels for:
   - All form field labels (name, age, gender, state, income, employment status, caste, is_student)
   - All button labels (submit, reset, check eligibility)
   - All status strings (eligible, not eligible)
   - All section headings (results, guidance, documents required)
   - All error/validation messages

### Relevant Context
- Each rule object shape: `{"field": "age", "operator": ">=", "value": 18}`
- Supported operators: `>=`, `<=`, `==`, `!=`
- `applicable_states` value of `["All"]` means the scheme is available nationwide
- Beginner-friendly: keep rule lists short (2–4 rules per scheme)

### JSON Structure Reference

```
schemes.json
[
  {
    "scheme_id": "PM_AWAS",
    "name": "PM Awas Yojana",
    "description": "...",
    "applicable_states": ["All"],
    "guidance": "Apply at your local municipality office with Aadhaar card.",
    "documents_required": ["Aadhaar Card", "Income Certificate"],
    "rules": [
      {"field": "age", "operator": ">=", "value": 18},
      {"field": "annual_income", "operator": "<=", "value": 300000}
    ]
  }
]

translations.json
{
  "en": {
    "form_name_label": "Full Name",
    "form_age_label": "Age",
    ...
  },
  "hi": { ... },
  "ta": { ... }
}
```

---

## Sub-Task 3 — JSON Loaders

**Status:** [ ] pending

### Intent
Provide clean loader functions that read JSON files and return typed Python objects. Keeping file I/O isolated in `loaders/` means the rest of the app never reads files directly.

### Expected Outcomes
- `loaders/scheme_loader.py` exposes `load_schemes(filepath: str) -> list[Scheme]`
- `loaders/translation_loader.py` exposes `load_translations(filepath: str) -> dict[str, dict[str, str]]`
- Both functions raise `SchemeDataError` if the file is missing or malformed
- Both functions return fully typed Python objects, not raw dicts

### Todo List
1. Create `loaders/__init__.py` (empty)
2. Create `loaders/scheme_loader.py`:
   - `load_schemes(filepath: str) -> list[Scheme]` — opens the JSON, parses each entry into a `Scheme` dataclass (and each rule into `EligibilityRule`), raises `SchemeDataError` if any required key is missing
3. Create `loaders/translation_loader.py`:
   - `load_translations(filepath: str) -> dict[str, dict[str, str]]` — opens the JSON and returns it as a nested dict; raises `SchemeDataError` if the file is missing or not valid JSON
4. Both loaders must validate that required keys are present and raise `SchemeDataError` with a descriptive message if not

### Relevant Context
- Required keys for each scheme: `scheme_id`, `name`, `description`, `applicable_states`, `guidance`, `documents_required`, `rules`
- Required keys for each rule: `field`, `operator`, `value`
- Use `json.load()` from the standard library — no third-party JSON libraries needed

---

## Sub-Task 4 — Validation Module

**Status:** [ ] pending

### Intent
Centralise all input validation in one module so the UI and tests can both call the same rules. Validation must be completely independent of Streamlit.

### Expected Outcomes
- `core/validation.py` exports `validate_inputs(data: dict) -> list[str]` which returns a list of error message strings (empty list means all inputs are valid)
- Individual field validators are internal helper functions
- Raises typed exceptions (`InvalidAgeError`, `InvalidIncomeError`, `InvalidInputError`) for programmatic error handling

### Todo List
1. Create `core/validation.py` with the following internal helper functions (all return `bool`):
   - `_validate_name(name: str) -> bool` — non-empty, letters/spaces/unicode only, max 100 chars
   - `_validate_age(age: int) -> bool` — integer in range 0–120
   - `_validate_income(income: float) -> bool` — non-negative float
   - `_validate_state(state: str, valid_states: list[str]) -> bool` — must be in the provided list
   - `_validate_enum_field(value: str, valid_values: list[str]) -> bool` — generic enum checker used for gender, employment status, caste
2. Create the public function:
   - `validate_inputs(data: dict) -> list[str]` — calls all helpers, collects error messages, returns the list. Returns empty list if all fields are valid.

### Validation Rules Summary

| Field | Rule |
|---|---|
| name | Non-empty, letters + spaces + unicode, max 100 chars |
| age | Integer, 0–120 inclusive |
| annual_income | Float, >= 0 |
| gender | One of: Male, Female, Other |
| state | One of the fixed state list |
| employment_status | One of: Employed, Unemployed, Self-Employed, Student |
| caste_category | One of: General, OBC, SC, ST |

### Relevant Context
- `validate_inputs` receives a plain `dict` (not a `Citizen` object) — this allows it to be called before constructing the `Citizen` dataclass
- Error messages should be human-readable strings matching the translation system keys, OR plain English for the initial version

---

## Sub-Task 5 — Eligibility Engine

**Status:** [ ] pending

### Intent
Implement the core business logic that evaluates a `Citizen` against a `Scheme`'s rules and returns an `EligibilityResult`. This is the most important module in the project and must be fully testable in isolation from the UI.

### Expected Outcomes
- `core/eligibility.py` exports two public functions with full type hints
- `check_eligibility()` evaluates one citizen against one scheme and returns one `EligibilityResult`
- `check_all_schemes()` runs `check_eligibility()` for all schemes and returns sorted results (eligible first)
- All rule operators (`>=`, `<=`, `==`, `!=`) are handled
- State filtering is applied: schemes with `applicable_states != ["All"]` are skipped if the citizen's state is not in the list
- Each result includes per-rule reason strings explaining the outcome

### Todo List
1. Create `core/eligibility.py`
2. Implement `_apply_rule(citizen: Citizen, rule: EligibilityRule) -> tuple[bool, str]`:
   - Uses `getattr(citizen, rule.field)` to read the citizen's field value
   - Applies the operator using a dispatch dict or if/elif chain
   - Returns `(passed: bool, reason_message: str)`
   - Raises `SchemeDataError` if `rule.operator` is not one of the four supported operators
   - Raises `SchemeDataError` if `rule.field` is not a valid field on `Citizen`
3. Implement `check_eligibility(citizen: Citizen, scheme: Scheme) -> EligibilityResult`:
   - First checks if `scheme.applicable_states == ["All"]` or `citizen.state in scheme.applicable_states`; if not, returns `EligibilityResult` with status `"Not Eligible"` and reason "Scheme not available in your state"
   - Calls `_apply_rule()` for each rule in `scheme.rules`
   - If ALL rules pass → status is `"Eligible"`
   - If ANY rule fails → status is `"Not Eligible"`
   - Always includes all rule reasons in the result (not just the failing ones)
4. Implement `check_all_schemes(citizen: Citizen, schemes: list[Scheme]) -> list[EligibilityResult]`:
   - Calls `check_eligibility()` for each scheme
   - Returns results sorted: `"Eligible"` results first, `"Not Eligible"` results last

### Relevant Context
- `citizen.employment_status == "Student"` is the proxy for `is_student` — do not add a separate `is_student` field; use the employment_status value
- Income threshold comparisons use `<=` (at-threshold is eligible)
- `getattr(citizen, rule.field)` will raise `AttributeError` if the field name in JSON is misspelled — catch this and re-raise as `SchemeDataError`

---

## Sub-Task 6 — Streamlit UI

**Status:** [ ] pending

### Intent
Build a thin Streamlit UI layer that collects user input, calls the `core/` functions, and displays results. The UI must contain NO business logic — it only handles layout, user input, and display.

### Expected Outcomes
- `app.py` is the only file that imports `streamlit`
- The UI has three logical sections: language selector, citizen input form, results panel
- Validation errors are shown inline before results are computed
- Results are shown as expandable cards, one per scheme
- Language selection re-renders all UI labels without clearing form data
- A Reset button clears all form fields

### Todo List
1. Create `app.py` with the following structure:
   - **Startup:** Load schemes via `load_schemes()` and translations via `load_translations()` using `@st.cache_data` to avoid reloading on every interaction
   - **Language selector:** `st.selectbox` at the top of the sidebar; stores chosen language code in `st.session_state`
   - **Input form section:** All fields as Streamlit widgets (`st.text_input`, `st.number_input`, `st.selectbox`, `st.radio`); values read from widgets, not session state
   - **Submit button:** Calls `validate_inputs()` first; if errors exist, show them with `st.error()`; if valid, construct `Citizen`, call `check_all_schemes()`, and display results
   - **Results section:** Use `st.expander` for each scheme result; show a green ✅ or red ❌ header; list reasons; show guidance and documents required only for eligible schemes
   - **Reset button:** Calls `st.rerun()` after clearing relevant session state keys

### UI Flow

```
Sidebar: [Language Selector]
  |
  v
Main Area:
  [Citizen Information Form]
    Full Name | Age | Gender | State
    Annual Income | Employment Status | Caste Category
  [Check Eligibility Button]
    |
    v (validation fails)
  [Inline Error Messages]
    |
    v (validation passes)
  [Results Panel]
    Scheme 1 expander: Eligible ✅
      - Reasons
      - Guidance
      - Documents Required
    Scheme 2 expander: Not Eligible ❌
      - Reasons
  [Reset Button]
```

### Relevant Context
- Use `st.cache_data` on both loader functions to cache JSON file reads
- All display strings (labels, headings, button text) must come from the `translations` dict using the selected language code
- Do not import anything from `core/` inside a widget callback — keep all logic in the main script flow

---

## Sub-Task 7 — Unit Tests

**Status:** [ ] pending

### Intent
Write pytest tests that verify all non-UI modules work correctly in isolation. Tests must run without Streamlit and without any file system side effects.

### Expected Outcomes
- `tests/test_eligibility.py` has tests for all eligibility scenarios
- `tests/test_validation.py` has tests for all validation rules including edge cases
- `tests/test_loaders.py` has tests for both loader functions including error paths
- All tests pass with `pytest tests/`
- No test imports `streamlit`

### Todo List
1. Create `tests/__init__.py` (empty)
2. Create `tests/test_validation.py`:
   - Test valid inputs return empty error list
   - Test each invalid field returns the correct error message
   - Test boundary values: age 0, age 120, age 121, income 0, income -1
   - Test name with unicode characters is accepted
   - Test empty name is rejected
3. Create `tests/test_eligibility.py`:
   - Use fixture functions (not JSON files) to create `Citizen` and `Scheme` objects inline
   - Test: citizen meets all rules → status is `"Eligible"`
   - Test: citizen fails one rule → status is `"Not Eligible"`
   - Test: citizen's state not in scheme's applicable_states → `"Not Eligible"` with state reason
   - Test: scheme with `applicable_states: ["All"]` → state check always passes
   - Test: income exactly at threshold → `"Eligible"` (boundary test)
   - Test: unknown operator in rule → raises `SchemeDataError`
   - Test: unknown field in rule → raises `SchemeDataError`
   - Test: `check_all_schemes` returns eligible results before not-eligible results
4. Create `tests/test_loaders.py`:
   - Test: valid `schemes.json` content loads correctly into `list[Scheme]`
   - Test: missing required key in a scheme entry raises `SchemeDataError`
   - Test: missing required key in a rule raises `SchemeDataError`
   - Test: file not found raises `SchemeDataError`
   - Test: valid `translations.json` loads correctly
   - Test: malformed JSON raises `SchemeDataError`
   - Use `tmp_path` pytest fixture to write temporary JSON files — do not depend on the real `data/` files

### Relevant Context
- Use `pytest.raises(SchemeDataError)` for all error path tests
- Use `pytest.fixture` for reusable `Citizen` and `Scheme` test objects
- Test file isolation: all loader tests must write their own JSON to `tmp_path` and not rely on `data/schemes.json`

---

## Data Models Detail

### `Citizen` fields

| Field | Type | Allowed Values |
|---|---|---|
| name | str | Non-empty string |
| age | int | 0–120 |
| gender | str | "Male", "Female", "Other" |
| state | str | One of the 28 states + 8 UTs |
| annual_income | float | >= 0 |
| employment_status | str | "Employed", "Unemployed", "Self-Employed", "Student" |
| caste_category | str | "General", "OBC", "SC", "ST" |

### `EligibilityRule` fields

| Field | Type | Description |
|---|---|---|
| field | str | Name of the `Citizen` attribute to check |
| operator | str | One of: ">=", "<=", "==", "!=" |
| value | Any | The threshold or target value to compare against |

### `Scheme` fields

| Field | Type | Description |
|---|---|---|
| scheme_id | str | Unique identifier |
| name | str | Display name |
| description | str | Plain-language description |
| applicable_states | list[str] | ["All"] or list of state names |
| guidance | str | How to apply |
| documents_required | list[str] | Required documents |
| rules | list[EligibilityRule] | Ordered list of eligibility rules |

### `EligibilityResult` fields

| Field | Type | Description |
|---|---|---|
| scheme_name | str | Name of the scheme |
| status | str | "Eligible" or "Not Eligible" |
| reasons | list[str] | One reason string per rule evaluated |

---

## Edge Cases to Handle

| Case | Where Handled |
|---|---|
| Age = 0 (newborn) | validation.py — valid, passes 0–120 check |
| Income exactly at threshold | eligibility.py — use <= operator, so threshold is inclusive |
| No schemes match citizen | app.py — show "No eligible schemes found" message |
| All schemes match citizen | app.py — render all expanders scrollably |
| Unknown operator in scheme JSON | eligibility.py — raises SchemeDataError |
| Misspelled field name in rule | eligibility.py — catches AttributeError, re-raises as SchemeDataError |
| Name in Hindi or Tamil script | validation.py — unicode regex allows non-ASCII letters |
| Language switch mid-session | app.py — language code in session_state, labels re-fetched on each render |
| schemes.json file missing at startup | scheme_loader.py — raises SchemeDataError with clear message |

---

## Future Improvements

These are explicitly out of scope for this beginner project but worth noting:

1. **Disability field** — add `has_disability: bool` to `Citizen` and support `"=="` rules against it
2. **Marital status** — needed for widow/widower-specific schemes
3. **BPL card field** — some schemes check card possession, not income
4. **Per-capita income** — divide by household size for more accurate checks
5. **PDF/print export** — `st.download_button` with a simple text summary
6. **Official links** — add a `url` field to `Scheme` and render as a hyperlink
7. **More languages** — `translations.json` is designed to accept any language code
8. **Scheme search/filter** — `st.text_input` filter box in the results panel
9. **Database backend** — replace `schemes.json` with SQLite using the same loader interface
10. **CI pipeline** — add a `pytest` GitHub Actions workflow on push
