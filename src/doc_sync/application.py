"""Application workflow for check and sync operations."""

from __future__ import annotations

from pathlib import Path

from .diagnostics import sort_diagnostics, warning
from .document import append_marked_section, inspect_document, replace_marked_section, marked_document
from .exit_codes import DRIFT, OPERATIONAL_ERROR, SUCCESS
from .io import atomic_write, validate_target
from .markdown import generate_markdown
from .model import Configuration, Diagnostic, DocumentStatus, OperationResult
from .parser import parse_sources
from .scanner import discover_python_files


def _fatal_diagnostics(diagnostics: list[Diagnostic]) -> bool:
    return any(diagnostic.code != "SYNTAX_ERROR" for diagnostic in diagnostics)


def _drift_message(path: Path, current: bool) -> str:
    return f"Documentation is {'in sync' if current else 'out of sync'}: {path}"


def run(config: Configuration, mode: str) -> OperationResult:
    diagnostics: list[Diagnostic] = []
    target_error = validate_target(config)
    if target_error is not None:
        return OperationResult(OPERATIONAL_ERROR, target_error.message, [target_error])

    sources, scan_diagnostics, summary = discover_python_files(config)
    diagnostics.extend(scan_diagnostics)
    items, parse_diagnostics = parse_sources(sources, summary)
    diagnostics.extend(parse_diagnostics)
    generated = generate_markdown(items)
    if len(generated.encode("utf-8")) > config.max_output_bytes:
        diagnostic = warning(
            "OUTPUT_LIMIT",
            f"generated output exceeds maximum size of {config.max_output_bytes} bytes",
            path=str(config.docs),
        )
        diagnostics.append(diagnostic)
        return OperationResult(OPERATIONAL_ERROR, diagnostic.message, sort_diagnostics(diagnostics))

    document = inspect_document(config.docs)
    if document.diagnostic is not None:
        diagnostics.append(document.diagnostic)
    if _fatal_diagnostics(diagnostics) or document.status == DocumentStatus.MALFORMED:
        return OperationResult(OPERATIONAL_ERROR, "documentation operation failed", sort_diagnostics(diagnostics))

    if mode == "check":
        current = document.status == DocumentStatus.VALID and document.body.replace("\r\n", "\n") == generated
        if current:
            return OperationResult(SUCCESS, _drift_message(config.docs, True), sort_diagnostics(diagnostics))
        return OperationResult(DRIFT, _drift_message(config.docs, False), sort_diagnostics(diagnostics), changes=(1, 0, 0))

    if mode != "sync":
        return OperationResult(OPERATIONAL_ERROR, f"unsupported operation: {mode}", sort_diagnostics(diagnostics))
    if document.status == DocumentStatus.MISSING:
        updated = marked_document(generated)
    elif document.status == DocumentStatus.NO_MARKERS:
        updated = append_marked_section(document.text, generated)
    else:
        updated = replace_marked_section(document, generated)
    try:
        changed = not config.docs.exists() or config.docs.read_text(encoding="utf-8", newline="") != updated
        if changed:
            atomic_write(config.docs, updated, fsync=config.fsync)
    except OSError as exc:
        diagnostic = warning("DOC_WRITE", str(exc), path=str(config.docs))
        diagnostics.append(diagnostic)
        return OperationResult(OPERATIONAL_ERROR, diagnostic.message, sort_diagnostics(diagnostics))
    return OperationResult(SUCCESS, f"Documentation synchronized: {config.docs}", sort_diagnostics(diagnostics), changed=changed)
