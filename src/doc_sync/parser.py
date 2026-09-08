"""Static AST parsing and public API extraction."""

from __future__ import annotations

import ast
import tokenize
from pathlib import Path

from .diagnostics import warning
from .model import ApiItem, ApiKind, Diagnostic, ScanSummary, SourceFile
from .signature import class_signature, expression, function_signature

MISSING_DOCSTRING = "No docstring provided."


def _docstring(node: ast.AST) -> str:
    return ast.get_docstring(node, clean=True) or MISSING_DOCSTRING


def _public(name: str) -> bool:
    return not name.startswith("_")


def _function_item(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    source: SourceFile,
    qualified_name: str,
    kind: ApiKind,
) -> ApiItem:
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return ApiItem(
        source_path=source.display_path,
        kind=kind,
        name=node.name,
        qualified_name=qualified_name,
        signature=f"{prefix}{function_signature(node)}",
        docstring=_docstring(node),
        line=node.lineno,
        column=node.col_offset,
    )


def _class_item(node: ast.ClassDef, source: SourceFile) -> ApiItem:
    bases = tuple(expression(base) for base in node.bases)
    methods: list[ApiItem] = []
    constructor: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for child in node.body:
        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if child.name == "__init__":
            constructor = child
        elif _public(child.name):
            methods.append(
                _function_item(
                    child,
                    source,
                    f"{node.name}.{child.name}",
                    ApiKind.METHOD,
                )
            )
    methods.sort(key=lambda item: item.qualified_name)
    return ApiItem(
        source_path=source.display_path,
        kind=ApiKind.CLASS,
        name=node.name,
        qualified_name=node.name,
        signature=class_signature(node.name, bases, constructor),
        docstring=_docstring(node),
        bases=bases,
        line=node.lineno,
        column=node.col_offset,
        methods=tuple(methods),
    )


def parse_source_file(
    source: SourceFile,
) -> tuple[list[ApiItem], list[Diagnostic], bool]:
    try:
        with tokenize.open(source.path) as handle:
            text = handle.read()
    except (OSError, UnicodeError) as exc:
        return [], [warning("SOURCE_READ", str(exc), path=source.display_path)], False

    try:
        tree = ast.parse(text, filename=str(source.path))
    except SyntaxError as exc:
        return [], [
            warning(
                "SYNTAX_ERROR",
                exc.msg,
                path=source.display_path,
                line=exc.lineno,
                column=exc.offset,
            )
        ], False

    items: list[ApiItem] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _public(node.name):
            items.append(_function_item(node, source, node.name, ApiKind.FUNCTION))
        elif isinstance(node, ast.ClassDef) and _public(node.name):
            items.append(_class_item(node, source))
    items.sort(key=lambda item: item.sort_key)
    return items, [], True


def parse_sources(
    sources: list[SourceFile],
    summary: ScanSummary,
) -> tuple[list[ApiItem], list[Diagnostic]]:
    items: list[ApiItem] = []
    diagnostics: list[Diagnostic] = []
    for source in sources:
        parsed_items, file_diagnostics, parsed = parse_source_file(source)
        diagnostics.extend(file_diagnostics)
        if parsed:
            summary.parsed += 1
        else:
            summary.skipped += 1
            if any(diagnostic.code == "SOURCE_READ" for diagnostic in file_diagnostics):
                summary.unreadable += 1
        items.extend(parsed_items)
    return items, diagnostics
