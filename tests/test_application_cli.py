from __future__ import annotations

from pathlib import Path

from doc_sync.application import run
from doc_sync.cli import main
from doc_sync.config import build_configuration
from doc_sync.exit_codes import DRIFT, SUCCESS


def test_check_and_sync_create_and_validate_documentation(tmp_path: Path, capsys) -> None:
    (tmp_path / "api.py").write_text("def public():\n    pass\n", encoding="utf-8")
    config = build_configuration(tmp_path, Path("API_DOCS.md"))

    check_before = run(config, "check")
    assert check_before.exit_code == DRIFT
    assert not (tmp_path / "API_DOCS.md").exists()

    sync_result = run(config, "sync")
    assert sync_result.exit_code == SUCCESS
    assert (tmp_path / "API_DOCS.md").exists()

    check_after = run(config, "check")
    assert check_after.exit_code == SUCCESS
    assert check_after.message.startswith("Documentation is in sync:")


def test_check_detects_api_drift_and_sync_preserves_manual_text(tmp_path: Path) -> None:
    (tmp_path / "api.py").write_text("def public():\n    pass\n", encoding="utf-8")
    assert main(["sync", "--root", str(tmp_path)]) == SUCCESS
    docs = tmp_path / "API_DOCS.md"
    docs.write_text(docs.read_text(encoding="utf-8") + "\nManual notes.\n", encoding="utf-8")
    (tmp_path / "api.py").write_text("def changed():\n    pass\n", encoding="utf-8")

    assert main(["check", "--root", str(tmp_path)]) == DRIFT
    assert main(["sync", "--root", str(tmp_path)]) == SUCCESS
    updated = docs.read_text(encoding="utf-8")
    assert "Manual notes." in updated
    assert "Function `changed()" in updated
    assert "Function `public()" not in updated


def test_malformed_markers_return_operational_error_without_overwrite(tmp_path: Path) -> None:
    (tmp_path / "api.py").write_text("def public():\n    pass\n", encoding="utf-8")
    docs = tmp_path / "API_DOCS.md"
    original = "# Notes\n<!-- AUTO-GENERATED:START -->\nno end\n"
    docs.write_text(original, encoding="utf-8")

    result = main(["sync", "--root", str(tmp_path)])

    assert result == 3
    assert docs.read_text(encoding="utf-8") == original


def test_syntax_error_warning_does_not_block_sync(tmp_path: Path, capsys) -> None:
    (tmp_path / "bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
    (tmp_path / "good.py").write_text("def valid():\n    pass\n", encoding="utf-8")

    result = main(["sync", "--root", str(tmp_path)])
    captured = capsys.readouterr()

    assert result == SUCCESS
    assert "SYNTAX_ERROR" in captured.err
    assert "Function `valid()" in (tmp_path / "API_DOCS.md").read_text(encoding="utf-8")
