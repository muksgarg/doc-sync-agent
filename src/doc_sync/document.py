"""Pure marker parsing and generated-section replacement."""

from __future__ import annotations

from pathlib import Path

from .diagnostics import error
from .model import Diagnostic, DocumentRead, DocumentStatus

START_MARKER = "<!-- AUTO-GENERATED:START -->"
END_MARKER = "<!-- AUTO-GENERATED:END -->"


def _line_value(line: str) -> str:
    return line.removesuffix("\n").removesuffix("\r")


def inspect_document(path: Path) -> DocumentRead:
    if not path.exists():
        return DocumentRead(DocumentStatus.MISSING, path)
    try:
        text = path.read_text(encoding="utf-8", newline="")
    except (OSError, UnicodeError) as exc:
        return DocumentRead(
            DocumentStatus.MALFORMED,
            path,
            diagnostic=error("DOC_READ", str(exc), path=str(path)),
        )

    lines = text.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if _line_value(line) == START_MARKER]
    ends = [index for index, line in enumerate(lines) if _line_value(line) == END_MARKER]
    if not starts and not ends:
        return DocumentRead(DocumentStatus.NO_MARKERS, path, text=text)
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        return DocumentRead(
            DocumentStatus.MALFORMED,
            path,
            text=text,
            diagnostic=error(
                "DOC_MARKERS",
                "document must contain exactly one ordered marker pair",
                path=str(path),
            ),
        )

    start_line, end_line = starts[0], ends[0]
    start_index = sum(len(line) for line in lines[: start_line + 1])
    end_index = sum(len(line) for line in lines[:end_line])
    return DocumentRead(
        DocumentStatus.VALID,
        path,
        text=text,
        body=text[start_index:end_index],
        start_index=start_index,
        end_index=end_index,
    )


def marked_document(body: str) -> str:
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    if body and not body.endswith("\n"):
        body += "\n"
    return f"{START_MARKER}\n{body}{END_MARKER}\n"


def append_marked_section(text: str, body: str) -> str:
    prefix = text
    if prefix and not prefix.endswith(("\n", "\r")):
        prefix += "\n"
    return prefix + marked_document(body)


def replace_marked_section(document: DocumentRead, body: str) -> str:
    if document.status != DocumentStatus.VALID:
        raise ValueError("cannot replace a document without a valid marker pair")
    assert document.start_index is not None and document.end_index is not None
    generated = body.replace("\r\n", "\n").replace("\r", "\n")
    if generated and not generated.endswith("\n"):
        generated += "\n"
    return document.text[: document.start_index] + generated + document.text[document.end_index:]
