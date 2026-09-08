from __future__ import annotations

from pathlib import Path

from doc_sync.config import build_configuration
from doc_sync.document import START_MARKER
from doc_sync.scanner import discover_python_files


def test_scanner_skips_directory_symlink_by_default(tmp_path: Path) -> None:
    target = tmp_path / "outside"
    target.mkdir()
    (target / "external.py").write_text("def external(): pass\n", encoding="utf-8")
    link = tmp_path / "linked"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    config = build_configuration(tmp_path, Path("API_DOCS.md"))
    files, _, _ = discover_python_files(config)

    assert all(source.display_path != "linked/external.py" for source in files)


def test_generated_marker_constant_is_exact() -> None:
    assert START_MARKER == "<!-- AUTO-GENERATED:START -->"
