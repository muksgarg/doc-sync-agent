from __future__ import annotations

from pathlib import Path

from doc_sync.document import (
    END_MARKER,
    START_MARKER,
    append_marked_section,
    inspect_document,
    replace_marked_section,
)
from doc_sync.markdown import generate_markdown
from doc_sync.model import ApiItem, ApiKind, DocumentStatus


def test_markdown_generation_is_deterministic_and_readable() -> None:
    item = ApiItem(
        source_path="pkg/api.py",
        kind=ApiKind.FUNCTION,
        name="public",
        qualified_name="public",
        signature="(value: int = 1) -> int",
        docstring="Returns a value.",
    )

    first = generate_markdown([item])
    second = generate_markdown([item])

    assert first == second
    assert first.endswith("\n")
    assert "### Module `pkg/api.py`" in first
    assert "#### Function `public(value: int = 1) -> int`" in first


def test_missing_markers_are_distinguished_from_malformed_markers(tmp_path: Path) -> None:
    path = tmp_path / "README.md"
    path.write_text("# Manual\n", encoding="utf-8")
    assert inspect_document(path).status == DocumentStatus.NO_MARKERS

    path.write_text(f"{START_MARKER}\ncontent\n", encoding="utf-8")
    malformed = inspect_document(path)
    assert malformed.status == DocumentStatus.MALFORMED
    assert malformed.diagnostic is not None


def test_marker_replacement_preserves_manual_content(tmp_path: Path) -> None:
    path = tmp_path / "README.md"
    original = f"# Before\n{START_MARKER}\nold\n{END_MARKER}\n# After\n"
    path.write_bytes(original.encode("utf-8"))
    document = inspect_document(path)

    updated = replace_marked_section(document, "new content\n")

    assert updated == f"# Before\n{START_MARKER}\nnew content\n{END_MARKER}\n# After\n"
    assert "old" not in updated


def test_append_marked_section_adds_one_pair_and_is_idempotent() -> None:
    text = "# Manual"
    updated = append_marked_section(text, "generated\n")

    assert updated.count(START_MARKER) == 1
    assert updated.count(END_MARKER) == 1
    assert updated.startswith("# Manual\n")


def test_duplicate_or_reversed_markers_are_malformed(tmp_path: Path) -> None:
    path = tmp_path / "README.md"
    path.write_text(
        f"{END_MARKER}\n{START_MARKER}\nbody\n{END_MARKER}\n",
        encoding="utf-8",
    )
    assert inspect_document(path).status == DocumentStatus.MALFORMED
