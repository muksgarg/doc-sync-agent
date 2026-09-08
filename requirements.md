# Automated Documentation Sync

## 1. Purpose

Automated Documentation Sync is a lightweight Python command-line tool that scans a project directory, extracts the public Python API, and verifies or updates a generated API section in a Markdown document.

The tool is intended for local development and CI workflows. It must make documentation drift visible without overwriting manually maintained content outside the generated section.

## 2. Scope

### In Scope

- Scan Python source files with the `.py` extension.
- Discover public classes and functions using Python source analysis.
- Extract signatures and available docstrings.
- Detect added, removed, or signature/docstring changes in the public API.
- Validate generated API documentation against the source tree.
- Update a marker-delimited section in a Markdown file.
- Create the documentation file and markers when the target file does not exist.
- Skip hidden directories and virtual-environment directories.
- Continue processing when an individual Python file contains a syntax error.
- Report warnings and validation results through the CLI.

### Out of Scope for Version 1

- Non-Python source files.
- reStructuredText, AsciiDoc, HTML, or other documentation formats.
- Runtime imports or execution of scanned Python modules.
- Type inference beyond information available from source syntax and AST analysis.
- Automatic rewriting of Markdown outside the generated section.
- Documentation of private or internal APIs by default.
- Resolving APIs dynamically created through metaclasses, decorators, or runtime assignment.

## 3. Functional Requirements

### FR-001: Scan Python Files

The tool shall recursively scan a configured project directory for files ending in `.py`.

The scanner shall:

- Accept a user-selected root directory.
- Process files deterministically, using a stable path ordering.
- Avoid importing or executing source files.
- Preserve enough source-path information to identify each discovered API item in the generated documentation.

### FR-002: Exclude Directories

The scanner shall skip directories that are hidden or commonly used for virtual environments and generated artifacts.

At minimum, it shall skip:

- Any directory whose name begins with `.`.
- `.venv` and `venv`.
- `env` and `virtualenv`.
- `__pycache__`.

The implementation should support additional user-configured exclusions without requiring changes to the source code.

### FR-003: Parse Python Source

The tool shall parse each Python file using Python's source parser or AST facilities.

The tool shall not execute a module merely to discover its API. This prevents import-time side effects and avoids requiring project runtime dependencies during documentation generation.

### FR-004: Handle Syntax Errors

If a Python file cannot be parsed because of a syntax error, the tool shall:

- Skip that file.
- Log a clear warning to `stderr` containing the file path and error location when available.
- Continue scanning and processing other valid files.
- Avoid including incomplete API entries from the invalid file.

Syntax errors alone shall not terminate a `sync` operation. The command's final status shall follow the specified `sync` and `check` exit-code rules.

### FR-005: Identify Public APIs

The tool shall document public top-level functions, public classes, and public methods defined in scanned files.

A definition shall be considered private or internal when its name begins with `_` and is not the explicitly supported special case `__init__`.

The default behavior shall be:

- Include public functions.
- Include public classes.
- Include public methods of included classes.
- Exclude private functions, classes, and methods.
- Include `__init__` only when needed to describe the public constructor/API of a documented class.
- Exclude nested functions unless explicitly defined as a supported public API.

### FR-006: Extract API Metadata

For each included API item, the tool shall extract, where available:

- Module or source-file path.
- Definition kind: class, function, or method.
- Qualified name.
- Function or method signature.
- Class bases when available from source syntax.
- The first relevant docstring, normalized for Markdown output.
- Source location information sufficient to identify the definition during diagnostics.

The tool shall preserve meaningful parameter information, including positional-only parameters, keyword-only parameters, default values, variadic arguments, and return annotations when present.

### FR-007: Handle Missing Docstrings

Definitions without docstrings shall remain discoverable and shall be represented in the generated documentation with a consistent indication such as `No docstring provided.`

Missing docstrings shall not cause scanning, checking, or synchronization to fail.

### FR-008: Detect Documentation Drift

The tool shall compare the deterministic API content generated from the current source tree with the content inside the documentation markers.

It shall detect at least:

- Newly added public functions, classes, or methods.
- Removed public functions, classes, or methods.
- Changed signatures.
- Changed docstrings.
- Changed relevant class metadata included in the generated output.
- Missing or malformed generated markers.
- A missing target documentation file.

Comparison shall be based on normalized generated content so that equivalent source data produces stable results.

### FR-009: Generate Markdown

The tool shall generate valid, readable Markdown for the public API.

The generated section shall include enough structure to distinguish modules, classes, functions, methods, signatures, and docstrings. The exact heading levels and presentation should be deterministic and documented in the CLI help or project documentation.

The generated output shall be stable across repeated runs when the source files have not changed.

### FR-010: Use Marker-Based Updates

The tool shall manage generated documentation only between these exact HTML comment markers:

```markdown
<!-- AUTO-GENERATED:START -->
<!-- AUTO-GENERATED:END -->
```

For an existing target file, `sync` shall:

- Preserve all content before the start marker.
- Replace only the content between the markers.
- Preserve the end marker and all content after it.
- Avoid changing unrelated manually maintained Markdown.

If both markers are absent, the tool shall append a new marker-delimited generated section without destroying existing content.

If only one marker is present, or if the markers occur in an invalid order, the tool shall report the document as malformed. It shall not silently overwrite the target document.

### FR-011: Create Missing Documentation

If the configured Markdown target file does not exist, `sync` shall create it with a marker-delimited generated section.

The created file shall contain both required markers, even when no public APIs are found.

`check` shall report a missing target file or missing generated section as a documentation discrepancy.

### FR-012: Support Configurable Target

The tool shall support a configurable Markdown target path.

The default target shall be `API_DOCS.md`. A user may configure a README or another Markdown path, such as `README.md` or `docs/api.md`.

The target path shall be interpreted relative to the selected project root unless an explicit absolute path is supplied.

### FR-013: Check Mode

The `check` mode shall:

- Scan and parse the project.
- Generate the expected API section in memory.
- Compare it with the marker-delimited section in the target Markdown file.
- Print a concise result indicating whether documentation is in sync.
- Exit with code `0` when documentation is in sync.
- Exit with code `1` when discrepancies exist.
- Report operational failures separately from normal documentation drift where practical.
- Never modify source or documentation files.

### FR-014: Sync Mode

The `sync` mode shall:

- Scan and parse the project.
- Generate the expected API section.
- Create or update the configured Markdown target using the markers.
- Preserve content outside the markers.
- Exit with code `0` when the documentation is successfully written or already current.
- Report file-system, permission, or malformed-marker failures clearly and return a non-zero error code.

### FR-015: Command-Line Interface

The CLI shall expose the two required modes:

```text
 doc-sync check [OPTIONS]
 doc-sync sync [OPTIONS]
```

The CLI shall provide options equivalent to:

- `--root PATH`: project directory to scan; default is the current directory.
- `--docs PATH`: Markdown target; default is `API_DOCS.md`.
- `--exclude NAME`: additional directory name or path pattern to skip; repeatable.
- `--verbose`: enable additional diagnostic output.
- `--help`: display usage information.
- `--version`: display the tool version.

The final option names may vary with the selected Python CLI framework, but the behavior and defaults shall remain equivalent.

### FR-016: Diagnostics and Logging

The tool shall write:

- Normal results and status messages to `stdout`.
- Warnings, syntax-error notices, malformed-marker diagnostics, and operational errors to `stderr`.

Diagnostics shall include relevant paths and actionable descriptions. Verbose mode may include individual discovered definitions and detailed comparison information.

### FR-017: Deterministic Output

Given the same source files, configuration, and Python parsing rules, generated Markdown shall be byte-for-byte stable.

The tool shall use stable ordering for directories, files, modules, classes, functions, and methods. It shall use a consistent line-ending policy and ensure the generated section ends with a newline.

## 4. Non-Functional Requirements

### NFR-001: Lightweight Execution

The tool should use Python's standard library for scanning, parsing, comparison, and file updates where practical. It shall not require importing the scanned project or installing the project's dependencies.

### NFR-002: Supported Python Runtime

The supported Python version shall be explicitly declared by the project. The initial implementation should target a currently supported Python 3 version and use only syntax and standard-library APIs compatible with that version.

### NFR-003: Performance

Scanning shall be approximately linear in the number and total size of eligible `.py` files. The tool should avoid repeated parsing of the same file during one command invocation.

### NFR-004: Reliability and Data Safety

`sync` shall not partially replace a documentation file after an unexpected write failure. The implementation should write through a temporary file and replace the target atomically where the operating system permits.

The tool shall never execute scanned source code as part of normal operation.

### NFR-005: Idempotency

Running `sync` multiple times without source or configuration changes shall produce the same file contents and shall not accumulate duplicate markers or generated sections.

### NFR-006: Maintainability

The implementation shall separate these responsibilities sufficiently to permit focused testing:

- File discovery and exclusion.
- Python parsing and API extraction.
- API model normalization.
- Markdown generation.
- Marker replacement and file I/O.
- CLI argument handling and exit-code mapping.

### NFR-007: Testability

The project shall include automated tests for core behavior, including discovery, extraction, deterministic generation, marker replacement, syntax-error handling, and CLI exit codes.

Tests shall use temporary directories and files rather than modifying the repository's real documentation.

### NFR-008: Usability

The CLI shall provide clear help text, useful error messages, and concise output for common workflows. A first-time user shall be able to run `check` or `sync` without understanding the internal implementation.

### NFR-009: Portability

The tool should work on Windows, macOS, and Linux. Path handling shall use platform-independent path APIs, and generated documentation should use consistent Markdown path formatting.

### NFR-010: Security

The tool shall treat source files and documentation as untrusted input for parsing purposes. It shall not execute source code, evaluate arbitrary annotations, or expand untrusted shell commands.

## 5. CLI Specifications

### 5.1 General Syntax

```text
 doc-sync <mode> [options]
```

Required modes:

- `check`: validate documentation without modifying files.
- `sync`: update the generated documentation section in place.

### 5.2 Examples

Check the current project against the default target:

```text
 doc-sync check
```

Synchronize into `API_DOCS.md`:

```text
 doc-sync sync
```

Scan a specific project and update its README section:

```text
 doc-sync sync --root ./project --docs README.md
```

Skip an additional directory:

```text
 doc-sync check --exclude examples
```

### 5.3 Exit Codes

| Code | Meaning |
|---:|---|
| `0` | Operation succeeded. For `check`, documentation is in sync. For `sync`, documentation was successfully synchronized. |
| `1` | `check` found documentation discrepancies. |
| `2` | Invalid CLI usage or configuration. |
| `3` | Operational failure, such as an unreadable source file, permission error, or unsafe/malformed marker structure that prevents the requested operation. |

A syntax error in an individual Python file shall be a warning and shall not, by itself, produce an operational failure code.

### 5.4 Check Output Contract

When current, `check` should emit a clear success message such as:

```text
Documentation is in sync: API_DOCS.md
```

When drift exists, it should identify the target and summarize the discrepancy, for example:

```text
Documentation is out of sync: API_DOCS.md
Changes detected: 2 added, 1 changed, 1 removed
```

The exact wording may vary, but scripts must be able to rely on the exit code.

### 5.5 Sync Output Contract

After a successful update, `sync` should identify the target path and whether content changed, for example:

```text
Documentation synchronized: API_DOCS.md
```

Warnings about skipped syntax-error files shall remain visible on `stderr`.

## 6. Edge Cases and Expected Behavior

| Scenario | Expected behavior |
|---|---|
| Project contains no `.py` files | Generate a valid empty API section; `check` compares it normally. |
| File has no module, class, or function docstring | Include the public definition and show the standard missing-docstring text. |
| File contains a syntax error | Warn to `stderr`, skip that file, and continue processing other files. |
| File contains only private definitions | Produce no entries for those definitions. |
| Definition name begins with `_` | Exclude it, except supported `__init__` handling. |
| Public class contains private methods | Include the class and public methods only. |
| Public class has no public methods | Include the class with its class docstring or missing-docstring text. |
| Nested public-looking function | Exclude by default unless explicitly supported as a public API in a future version. |
| Decorated function or class | Document the statically discoverable definition and source signature; do not execute decorators. |
| Async public function or method | Treat it as a public function or method and preserve its async nature in the signature. |
| Type annotations contain complex expressions | Preserve source-level signature information without evaluating annotations. |
| Default value has side effects if evaluated | Do not evaluate it; represent it using safe source/AST-derived text where possible. |
| Hidden directory contains valid Python files | Skip the directory and its descendants. |
| Virtualenv directory contains valid Python files | Skip the directory and its descendants. |
| Target Markdown file is missing | `sync` creates it with both markers; `check` reports drift and exits `1`. |
| Target has neither marker | `sync` appends a new marked section; `check` reports drift. |
| Target has only one marker | Report malformed markers; do not silently overwrite the file. |
| Start marker appears after end marker | Report malformed markers; do not update the file. |
| Markers occur more than once | Report an ambiguous/malformed document unless a future specification defines multiple generated sections. |
| Generated section is empty | Treat it as valid when the source contains no included public APIs. |
| Documentation contains manual text outside markers | Preserve it exactly during `sync`. |
| Documentation has different line endings | Normalize only the generated replacement according to the implementation policy; avoid changing unrelated content. |
| Target directory does not exist | Report an operational error; do not silently create an unexpected directory tree unless explicitly configured. |
| Target is not writable | Report an operational error and leave the original file unchanged. |
| Source file cannot be read | Warn or report according to the failure policy, continue where possible, and make the result visible to the user. |
| Same source is run through `sync` repeatedly | Do not create duplicate content or markers; output remains idempotent. |
| API is removed from source | Remove its generated entry on the next successful `sync`; `check` reports the discrepancy beforehand. |
| Signature changes but docstring does not | Treat the API entry as changed. |
| Docstring changes but signature does not | Treat the API entry as changed. |

## 7. Acceptance Criteria

1. Running `doc-sync check` on an up-to-date project returns exit code `0` and does not modify files.
2. Running `doc-sync check` when a public API is added, removed, or changed returns exit code `1`.
3. Running `doc-sync sync` creates a missing `API_DOCS.md` with exactly one valid marker pair.
4. Running `doc-sync sync` updates only the content between the required markers.
5. Content outside the markers remains unchanged after synchronization.
6. Public functions and classes are documented; private definitions are excluded except for supported `__init__` behavior.
7. Missing docstrings are represented without stopping the operation.
8. Syntax-error files generate clear `stderr` warnings and do not prevent valid files from being processed.
9. Hidden and virtual-environment directories are not scanned.
10. Repeating `sync` without source changes is idempotent.
11. Generated output has stable ordering and formatting across repeated runs.
12. File-system failures and malformed marker structures produce clear diagnostics and non-zero error codes.
13. The project includes automated tests covering the principal functional requirements and edge cases listed above.

## 8. Open Implementation Decisions

The following details may be finalized during technical design without changing the user-facing requirements:

- The exact CLI framework, such as `argparse`, `click`, or `typer`.
- The precise Markdown heading layout.
- Whether module-level docstrings are rendered as separate entries or only used as module descriptions.
- The precise representation of complex default values and annotations.
- Whether skipped unreadable files are warnings or operational errors, provided the behavior is documented and consistent.
- The exact Python versions supported by the implementation.
