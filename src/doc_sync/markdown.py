"""Deterministic Markdown generation for extracted APIs."""

from __future__ import annotations

from collections.abc import Iterable

from .model import ApiItem, ApiKind


def _docstring_lines(docstring: str) -> list[str]:
    return [f"    {line}" if line else "    " for line in docstring.splitlines()]


def _display_signature(name: str, signature: str) -> str:
    return f"{name}{signature.removeprefix('async ')}"


def generate_markdown(items: Iterable[ApiItem]) -> str:
    lines: list[str] = []
    current_source: str | None = None
    for item in sorted(items, key=lambda value: value.sort_key):
        if item.source_path != current_source:
            if lines:
                lines.append("")
            lines.append(f"### Module `{item.source_path}`")
            current_source = item.source_path
        if item.kind == ApiKind.CLASS:
            lines.append("")
            lines.append(f"#### Class `{item.signature}`")
            if item.bases:
                lines.append(f"Bases: {', '.join(f'`{base}`' for base in item.bases)}")
            lines.extend(_docstring_lines(item.docstring))
            for method in item.methods:
                lines.append("")
                lines.append(f"##### Method `{_display_signature(method.name, method.signature)}`")
                lines.extend(_docstring_lines(method.docstring))
        elif item.kind == ApiKind.FUNCTION:
            lines.append("")
            prefix = "async " if item.signature.startswith("async ") else ""
            lines.append(f"#### Function `{prefix}{_display_signature(item.name, item.signature)}`")
            lines.extend(_docstring_lines(item.docstring))
    return "\n".join(lines).rstrip() + "\n" if lines else ""
