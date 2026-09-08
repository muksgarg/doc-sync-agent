from __future__ import annotations

from pathlib import Path

from doc_sync.config import build_configuration
from doc_sync.parser import MISSING_DOCSTRING, parse_sources
from doc_sync.scanner import discover_python_files


def test_scanner_excludes_hidden_virtualenv_and_custom_directories(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("def public(): pass\n", encoding="utf-8")
    for directory in (".hidden", ".venv", "venv", "env", "virtualenv", "__pycache__", "generated"):
        folder = tmp_path / directory
        folder.mkdir()
        (folder / "ignored.py").write_text("def ignored(): pass\n", encoding="utf-8")

    config = build_configuration(tmp_path, Path("API_DOCS.md"), ("generated",))
    files, diagnostics, _ = discover_python_files(config)

    assert [source.display_path for source in files] == ["main.py"]
    assert diagnostics == []


def test_parser_extracts_public_api_and_excludes_private_definitions(tmp_path: Path) -> None:
    source_path = tmp_path / "api.py"
    source_path.write_text(
        """
class Public:
    \"\"\"A public class.\"\"\"
    def __init__(self, value: int = 1):
        self.value = value

    def run(self, *, enabled: bool = True) -> str:
        \"\"\"Run the operation.\"\"\"
        return "ok"

    def _private_method(self):
        pass

class _PrivateClass:
    pass

def public_function(value: int = 1, /, *args, option=None, **kwargs) -> int:
    return value

def _private_function():
    pass


def outer():
    def nested_public():
        pass
    return nested_public
""".lstrip(),
        encoding="utf-8",
    )
    config = build_configuration(tmp_path, Path("API_DOCS.md"))
    files, _, summary = discover_python_files(config)
    items, diagnostics = parse_sources(files, summary)

    assert diagnostics == []
    assert [item.qualified_name for item in items] == ["Public", "outer", "public_function"]
    public_class = items[0]
    assert public_class.signature == "Public(value: int = 1)"
    assert public_class.docstring == "A public class."
    assert [method.name for method in public_class.methods] == ["run"]
    assert public_class.methods[0].signature.startswith("(self, *, enabled: bool = True)")
    assert items[2].signature.startswith("(value: int = 1, /, *args")
    assert all(method.name != "nested_public" for method in public_class.methods)


def test_syntax_error_is_skipped_and_valid_files_continue(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
    (tmp_path / "good.py").write_text("def valid():\n    pass\n", encoding="utf-8")
    config = build_configuration(tmp_path, Path("API_DOCS.md"))
    files, _, summary = discover_python_files(config)

    items, diagnostics = parse_sources(files, summary)

    assert [item.qualified_name for item in items] == ["valid"]
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "SYNTAX_ERROR"
    assert diagnostics[0].path == "bad.py"
    assert summary.parsed == 1
    assert summary.skipped == 1


def test_missing_docstrings_are_explicit(tmp_path: Path) -> None:
    (tmp_path / "api.py").write_text("class Public:\n    pass\n", encoding="utf-8")
    config = build_configuration(tmp_path, Path("API_DOCS.md"))
    files, _, summary = discover_python_files(config)
    items, _ = parse_sources(files, summary)

    assert items[0].docstring == MISSING_DOCSTRING
