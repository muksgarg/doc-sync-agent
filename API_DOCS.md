<!-- AUTO-GENERATED:START -->
### Module `demo.py`

#### Function `run(cmd, title)`
    No docstring provided.

### Module `src/doc_sync/application.py`

#### Function `run(config: Configuration, mode: str) -> OperationResult`
    No docstring provided.

### Module `src/doc_sync/cli.py`

#### Function `main(argv: list[str] | None = None) -> int`
    No docstring provided.

### Module `src/doc_sync/config.py`

#### Function `build_configuration(root: Path, docs: Path, exclusions: tuple[str, ...] = (), *, verbose: bool = False, max_file_bytes: int = 5000000, max_files: int = 100000, max_depth: int | None = 100, max_output_bytes: int = 10000000, follow_symlinks: bool = False, fsync: bool = False) -> Configuration`
    No docstring provided.

### Module `src/doc_sync/diagnostics.py`

#### Function `error(code: str, message: str, **location: object) -> Diagnostic`
    No docstring provided.

#### Function `format_diagnostic(diagnostic: Diagnostic) -> str`
    No docstring provided.

#### Function `sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> list[Diagnostic]`
    No docstring provided.

#### Function `warning(code: str, message: str, **location: object) -> Diagnostic`
    No docstring provided.

#### Function `write_diagnostics(diagnostics: Iterable[Diagnostic], *, stream: TextIO | None = None) -> None`
    No docstring provided.

### Module `src/doc_sync/document.py`

#### Function `append_marked_section(text: str, body: str) -> str`
    No docstring provided.

#### Function `inspect_document(path: Path) -> DocumentRead`
    No docstring provided.

#### Function `marked_document(body: str) -> str`
    No docstring provided.

#### Function `replace_marked_section(document: DocumentRead, body: str) -> str`
    No docstring provided.

### Module `src/doc_sync/io.py`

#### Function `atomic_write(path: Path, text: str, *, fsync: bool = False) -> None`
    No docstring provided.

#### Function `validate_target(config: Configuration) -> Diagnostic | None`
    No docstring provided.

### Module `src/doc_sync/markdown.py`

#### Function `generate_markdown(items: Iterable[ApiItem]) -> str`
    No docstring provided.

### Module `src/doc_sync/model.py`

#### Class `ApiItem`
    No docstring provided.

##### Method `sort_key(self) -> tuple[str, str, str]`
    No docstring provided.

#### Class `ApiKind(str, Enum)`
Bases: `str`, `Enum`
    No docstring provided.

#### Class `Configuration`
    No docstring provided.

#### Class `Diagnostic`
    No docstring provided.

##### Method `sort_key(self) -> tuple[str, int, int, str, str]`
    No docstring provided.

#### Class `DocumentRead`
    No docstring provided.

#### Class `DocumentStatus(str, Enum)`
Bases: `str`, `Enum`
    No docstring provided.

#### Class `OperationResult`
    No docstring provided.

#### Class `ScanSummary`
    No docstring provided.

#### Class `Severity(str, Enum)`
Bases: `str`, `Enum`
    No docstring provided.

#### Class `SourceFile`
    No docstring provided.

### Module `src/doc_sync/parser.py`

#### Function `parse_source_file(source: SourceFile) -> tuple[list[ApiItem], list[Diagnostic], bool]`
    No docstring provided.

#### Function `parse_sources(sources: list[SourceFile], summary: ScanSummary) -> tuple[list[ApiItem], list[Diagnostic]]`
    No docstring provided.

### Module `src/doc_sync/scanner.py`

#### Function `discover_python_files(config: Configuration) -> tuple[list[SourceFile], list[Diagnostic], ScanSummary]`
    No docstring provided.

### Module `src/doc_sync/signature.py`

#### Function `class_signature(name: str, bases: tuple[str, ...], constructor: ast.FunctionDef | ast.AsyncFunctionDef | None) -> str`
    No docstring provided.

#### Function `expression(node: ast.AST | None) -> str`
    No docstring provided.

#### Function `function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef, *, omit_first_parameter: bool = False) -> str`
    No docstring provided.

### Module `tests/test_application_cli.py`

#### Function `test_check_and_sync_create_and_validate_documentation(tmp_path: Path, capsys) -> None`
    No docstring provided.

#### Function `test_check_detects_api_drift_and_sync_preserves_manual_text(tmp_path: Path) -> None`
    No docstring provided.

#### Function `test_malformed_markers_return_operational_error_without_overwrite(tmp_path: Path) -> None`
    No docstring provided.

#### Function `test_syntax_error_warning_does_not_block_sync(tmp_path: Path, capsys) -> None`
    No docstring provided.

### Module `tests/test_document_and_markdown.py`

#### Function `test_append_marked_section_adds_one_pair_and_is_idempotent() -> None`
    No docstring provided.

#### Function `test_duplicate_or_reversed_markers_are_malformed(tmp_path: Path) -> None`
    No docstring provided.

#### Function `test_markdown_generation_is_deterministic_and_readable() -> None`
    No docstring provided.

#### Function `test_marker_replacement_preserves_manual_content(tmp_path: Path) -> None`
    No docstring provided.

#### Function `test_missing_markers_are_distinguished_from_malformed_markers(tmp_path: Path) -> None`
    No docstring provided.

### Module `tests/test_safety.py`

#### Function `test_generated_marker_constant_is_exact() -> None`
    No docstring provided.

#### Function `test_scanner_skips_directory_symlink_by_default(tmp_path: Path) -> None`
    No docstring provided.

### Module `tests/test_scanner_parser.py`

#### Function `test_missing_docstrings_are_explicit(tmp_path: Path) -> None`
    No docstring provided.

#### Function `test_parser_extracts_public_api_and_excludes_private_definitions(tmp_path: Path) -> None`
    No docstring provided.

#### Function `test_scanner_excludes_hidden_virtualenv_and_custom_directories(tmp_path: Path) -> None`
    No docstring provided.

#### Function `test_syntax_error_is_skipped_and_valid_files_continue(tmp_path: Path) -> None`
    No docstring provided.
<!-- AUTO-GENERATED:END -->
