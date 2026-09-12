"""Custom exception classes for the Welfare Eligibility Checker."""


class InvalidAgeError(ValueError):
    """Raised when the citizen's age is outside the valid range of 0–120."""

    def __init__(self, age: int) -> None:
        super().__init__(f"Age must be between 0 and 120, got: {age}")
        self.age = age


class InvalidIncomeError(ValueError):
    """Raised when the citizen's annual income is negative."""

    def __init__(self, income: float) -> None:
        super().__init__(f"Annual income cannot be negative, got: {income}")
        self.income = income


class InvalidInputError(ValueError):
    """Raised for any other field that fails validation."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"Invalid value for '{field}': {message}")
        self.field = field


class SchemeDataError(Exception):
    """Raised when a scheme JSON entry is malformed or the file cannot be loaded."""
