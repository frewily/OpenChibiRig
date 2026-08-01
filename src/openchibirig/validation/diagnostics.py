from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: Severity
    message: str
    location: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationReport:
    diagnostics: tuple[Diagnostic, ...]

    @property
    def errors(self) -> tuple[Diagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.severity is Severity.ERROR)

    @property
    def is_valid(self) -> bool:
        return not self.errors
