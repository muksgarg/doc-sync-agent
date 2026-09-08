"""Structured diagnostics and presentation helpers."""

from __future__ import annotations

import sys
from collections.abc import Iterable
from typing import TextIO

from .model import Diagnostic, Severity


def sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> list[Diagnostic]:
    return sorted(diagnostics, key=lambda diagnostic: diagnostic.sort_key)


def format_diagnostic(diagnostic: Diagnostic) -> str:
    location = diagnostic.path or "project"
    if diagnostic.line is not None:
        location += f":{diagnostic.line}"
        if diagnostic.column is not None:
            location += f":{diagnostic.column}"
    return f"{location}: {diagnostic.severity.value} [{diagnostic.code}] {diagnostic.message}"


def write_diagnostics(
    diagnostics: Iterable[Diagnostic],
    *,
    stream: TextIO | None = None,
) -> None:
    if stream is None:
        stream = sys.stderr
    for diagnostic in sort_diagnostics(diagnostics):
        print(format_diagnostic(diagnostic), file=stream)


def warning(code: str, message: str, **location: object) -> Diagnostic:
    return Diagnostic(Severity.WARNING, code, message, **location)


def error(code: str, message: str, **location: object) -> Diagnostic:
    return Diagnostic(Severity.ERROR, code, message, **location)
