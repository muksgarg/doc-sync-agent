"""Domain models shared across the synchronization pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ApiKind(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


class Severity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


class DocumentStatus(str, Enum):
    VALID = "valid"
    MISSING = "missing"
    NO_MARKERS = "no_markers"
    MALFORMED = "malformed"


@dataclass(frozen=True)
class SourceFile:
    path: Path
    display_path: str


@dataclass(frozen=True)
class ApiItem:
    source_path: str
    kind: ApiKind
    name: str
    qualified_name: str
    signature: str
    docstring: str
    bases: tuple[str, ...] = ()
    line: int = 0
    column: int = 0
    methods: tuple["ApiItem", ...] = ()

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return (self.source_path, self.qualified_name, self.kind.value)


@dataclass(frozen=True)
class Diagnostic:
    severity: Severity
    code: str
    message: str
    path: str | None = None
    line: int | None = None
    column: int | None = None

    @property
    def sort_key(self) -> tuple[str, int, int, str, str]:
        return (
            self.path or "",
            self.line or 0,
            self.column or 0,
            self.code,
            self.message,
        )


@dataclass
class ScanSummary:
    discovered: int = 0
    parsed: int = 0
    skipped: int = 0
    unreadable: int = 0
    limited: int = 0


@dataclass(frozen=True)
class Configuration:
    root: Path
    docs: Path
    exclusions: tuple[str, ...] = ()
    verbose: bool = False
    max_file_bytes: int = 5_000_000
    max_files: int = 100_000
    max_depth: int | None = 100
    max_output_bytes: int = 10_000_000
    follow_symlinks: bool = False
    fsync: bool = False


@dataclass(frozen=True)
class DocumentRead:
    status: DocumentStatus
    path: Path
    text: str = ""
    body: str = ""
    start_index: int | None = None
    end_index: int | None = None
    diagnostic: Diagnostic | None = None


@dataclass
class OperationResult:
    exit_code: int
    message: str
    diagnostics: list[Diagnostic] = field(default_factory=list)
    changes: tuple[int, int, int] = (0, 0, 0)
    changed: bool = False
