# Automated Documentation Sync Implementation Plan

## 1. Goal and Delivery Strategy

Implement `doc-sync` as a lightweight Python CLI that statically scans Python source, generates deterministic public API Markdown, and checks or updates one marker-delimited section without executing project code or changing manual content.

The implementation should proceed in dependency order:

1. Resolve design decisions and establish project contracts.
2. Build pure domain, diagnostics, discovery, parsing, rendering, and document primitives.
3. Add safe filesystem writes and application orchestration.
4. Expose and validate the CLI.
5. Complete cross-platform, failure-mode, and acceptance testing.

A task is considered complete only when its focused tests pass and its stated acceptance evidence exists.

## 2. Priority and Status Conventions

- **P0:** Required foundation or correctness gate; blocks downstream work.
- **P1:** Required Version 1 behavior.
- **P2:** Hardening, portability, or usability improvement required before release.
- **Blocked:** Cannot start safely until the listed predecessor task is complete.
- **Milestone:** A validation gate; no dependent implementation should proceed after a failed gate.

## 3. Dependency-Ordered Task List

### Phase 0: Resolve Contracts and Project Foundations

#### T01 - Finalize Version 1 design decisions

**Priority:** P0  
**Blocked until:** None  
**Deliverables:** A short decision record, reflected in `architecture.md` and CLI help as appropriate.

Decide and document:

- Python version range and AST grammar compatibility.
- Source encoding: use coding-cookie-aware reads such as `tokenize.open`; define invalid-byte behavior.
- Generated Markdown encoding and newline policy.
- Directory and file symlink policy; default to not following directory symlinks.
- Maximum source file size for huge files, file count, generated output size, and optional traversal depth.
- Incomplete-scan reporting and exact exit-code behavior.
- Canonical source-safe signature formatting.
- Exact marker line grammar and handling of marker-like text in code fences.
- Target path safety and whether absolute targets outside `--root` are allowed.
- Constructor representation, nested definitions, overloads, duplicates, and conditional definitions.
- Concurrent target-change behavior and write durability expectations.

**Why first:** Parser, scanner, document, and writer behavior otherwise remains ambiguous and would cause rework.

#### T02 - Scaffold packaging and test infrastructure

**Priority:** P0  
**Blocked until:** T01

Create the `src/` package and `tests/` structure from `architecture.md`, plus:

- `pyproject.toml` with the supported Python version and console entry point.
- `doc_sync/__init__.py` and `__main__.py`.
- Pytest configuration and reusable temporary-project fixtures.
- Basic test command documented in `README.md`.

Add a smoke test that imports the package without importing any scanned project code.

#### M01 - Foundation gate

**Blocked until:** T02  
**Verification:** Packaging metadata is valid, the package imports, the test runner starts, and the smoke test passes on the development Python version.

No feature implementation should proceed if the supported-runtime or entry-point contract is still unresolved.

### Phase 1: Contracts, Models, and Diagnostics

#### T03 - Implement configuration and exit-code contracts

**Priority:** P0  
**Blocked until:** M01

Implement `config.py` and `exit_codes.py`:

- Immutable configuration for root, docs target, exclusions, verbosity, and resource limits.
- Defaults: current directory, `API_DOCS.md`, and required directory exclusions.
- Root and target path resolution using `pathlib`.
- Validation for nonexistent/non-directory roots, unsafe target types, invalid limits, and invalid exclusions.
- Exit codes `0`, `1`, `2`, and `3`.

Test invalid configuration and path cases without invoking the full CLI.

#### T04 - Implement structured domain models

**Priority:** P0  
**Blocked until:** T03

Implement `model.py` dataclasses/enums for:

- Source file records.
- API items and kinds.
- Configuration.
- Diagnostics.
- Scan summary.
- Document status.
- Operation result.

Include normalized root-relative POSIX display paths and stable sort keys. Preserve source locations for diagnostics.

#### T05 - Implement deterministic diagnostics

**Priority:** P1  
**Blocked until:** T04

Implement `diagnostics.py` to:

- Collect warnings and errors as structured records.
- Sort diagnostics deterministically by path, line, and code.
- Route warnings/errors to `stderr` and status to `stdout` at the presentation boundary.
- Support concise and verbose output with a bounded warning summary.

#### M02 - Domain contract gate

**Blocked until:** T03, T04, T05  
**Verification:** Unit tests cover defaults, invalid configuration, stable model ordering, diagnostic ordering, and all exit-code constants.

### Phase 2: Safe Discovery and Static Parsing

#### T06 - Implement safe iterative project scanning

**Priority:** P0  
**Blocked until:** M02 and T01

Implement `scanner.py` using an iterative directory traversal:

- Discover only `.py` files.
- Sort directory and file processing deterministically.
- Prune hidden directories, `.venv`, `venv`, `env`, `virtualenv`, `__pycache__`, and user exclusions.
- Do not follow directory symlinks by default; define file-symlink behavior from T01.
- Enforce root containment and configured file/count/depth limits.
- Continue after inaccessible entries with structured diagnostics.

Tests must cover exclusions, custom exclusions, stable ordering, symlink cycles/escape attempts, deep trees, inaccessible paths where supported, and limits.

#### T07 - Implement coding-cookie-aware source reader

**Priority:** P0  
**Blocked until:** T06 and T01

Add the source read boundary in `parser.py` or a small internal reader:

- Read Python using `tokenize.open()` or equivalent.
- Preserve the actual text used for parsing.
- Handle UTF-8, BOMs, declared encodings, invalid bytes, and read races.
- Produce path-specific diagnostics and a scan summary for skipped files.

Do not evaluate source text or annotations.

#### T08 - Implement AST API extraction

**Priority:** P0  
**Blocked until:** T04, T05, and T07

Implement module-level and direct class-body extraction:

- Public top-level functions and classes.
- Public methods of included classes.
- Explicit constructor policy for `__init__`.
- Exclusion of private definitions and nested functions/classes per T01.
- Async function recognition.
- Class bases, qualified names, source locations, and normalized docstrings.
- Missing-docstring representation.
- Syntax-error warning with location; skip only the invalid file.
- No imports, execution, evaluation, or runtime dependency resolution.

Test public/private filtering, methods, constructors, async definitions, decorators, nested definitions, missing docstrings, syntax errors, invalid encodings, and complex annotations/defaults.

#### T09 - Implement source-safe signature renderer

**Priority:** P0  
**Blocked until:** T08 and T01

Create a dedicated deterministic renderer for AST signature data:

- Positional-only, positional-or-keyword, keyword-only, `*args`, `**kwargs`.
- Defaults and return annotations.
- Async marker.
- Class bases.
- Complex AST expressions without evaluation.
- Stable formatting across all supported Python versions.

Use `ast.unparse` only if its supported-version behavior is tested and accepted by T01. Add golden tests for every parameter category, lambdas/comprehensions, strings, annotations, type comments if supported, and version-sensitive syntax.

#### M03 - Static-analysis gate

**Blocked until:** T06, T07, T08, T09  
**Verification:** Scanner/parser tests pass; fixture modules with import-time side effects prove no project code executes; syntax-error and invalid-encoding files do not prevent valid files from being extracted; scan summaries expose skipped files.

### Phase 3: Deterministic Markdown and Marker Operations

#### T10 - Implement API normalization and Markdown generation

**Priority:** P0  
**Blocked until:** T04, T08, T09, and M03

Implement `markdown.py` and normalization helpers:

- Stable module, class, function, and method ordering.
- Readable headings and signatures.
- Class bases and docstrings.
- Standard missing-docstring text.
- Unicode preservation, line-ending normalization, and final newline.
- Safe rendering of docstrings containing Markdown, fences, HTML, backslashes, or marker-like text.
- Empty API section output.

Add deterministic/golden tests that render the same model repeatedly and compare bytes.

#### T11 - Implement pure marker parsing and replacement

**Priority:** P0  
**Blocked until:** T10 and T01

Implement `document.py` pure functions for:

- Exact marker-line recognition.
- Exactly one valid pair.
- Missing both markers versus malformed one-marker/reversed/duplicate cases.
- Empty generated sections.
- `prefix + markers + generated body + suffix` replacement.
- Append behavior when both markers are absent.
- Preservation of all outside content and configured newline policy.

Test CRLF/LF, trailing newlines, adjacent markers, duplicate markers, marker-like text, code fences, manual content, and idempotent replacement.

#### M04 - Pure content gate

**Blocked until:** T10 and T11  
**Verification:** Golden Markdown tests and marker tests pass; generated output is byte-stable; replacement changes only the generated region; malformed structures are rejected without producing an updated document.

### Phase 4: Filesystem Safety and Application Workflow

#### T12 - Implement target document I/O

**Priority:** P0  
**Blocked until:** T03, T11, M04, and T01

Implement `io.py`:

- UTF-8 target reads/writes according to T01.
- Missing-target handling for `sync` and drift handling for `check`.
- Validation of regular files, directories, special files, symlinks, and target/source collisions.
- Temporary file in the target directory.
- Flush/close, optional `fsync`, atomic `os.replace`, and cleanup on failure.
- Optional content/metadata check to detect target changes between read and replace.
- No unexpected parent-directory creation.

Test successful creation/update, permissions, missing parent directories, replacement failure, target mutation, and preservation of the original file.

#### T13 - Implement application orchestration

**Priority:** P0  
**Blocked until:** M03, M04, T12, and T05

Implement `application.py`:

- Execute discovery, parsing, normalization, rendering, and target inspection once per invocation.
- Aggregate scan diagnostics and summaries.
- Implement `check` without writes.
- Implement `sync` with missing-target creation and valid marker replacement.
- Return structured results for in-sync, drift, malformed, and operational outcomes.
- Apply the agreed syntax-error, unreadable-file, and incomplete-scan exit policy.

Test end-to-end application behavior with temporary directories before adding CLI parsing.

#### M05 - Application behavior gate

**Blocked until:** T12 and T13  
**Verification:** End-to-end service tests prove check is read-only, sync is idempotent, manual content is preserved, malformed markers are not overwritten, and exit outcomes match the requirements.

### Phase 5: CLI and User-Facing Contract

#### T14 - Implement CLI commands and entry points

**Priority:** P1  
**Blocked until:** T03, T05, T13, and M05

Implement `cli.py` and `__main__.py` with `argparse`:

- `doc-sync check [OPTIONS]`.
- `doc-sync sync [OPTIONS]`.
- `--root`, `--docs`, repeatable `--exclude`, `--verbose`, `--help`, and `--version`.
- Concise required output and stable exit codes.
- `stdout`/`stderr` routing.
- Actionable errors with target/source paths.

Keep CLI code limited to parsing, presentation, and exit-code mapping.

#### T15 - Add CLI contract and subprocess tests

**Priority:** P1  
**Blocked until:** T14

Test through the installed console command or `python -m doc_sync`:

- Default root/docs behavior.
- Custom root/docs and repeatable exclusions.
- Help/version output.
- In-sync, drift, malformed, invalid configuration, and operational failure codes.
- No file modification in `check`.
- Warnings on `stderr` for syntax errors.
- Verbose output and diagnostic ordering.

#### M06 - CLI contract gate

**Blocked until:** T14 and T15  
**Verification:** All required command examples execute against temporary projects and produce the documented exit codes and stream routing.

### Phase 6: Release Hardening and Acceptance

#### T16 - Add cross-platform and runtime matrix

**Priority:** P1  
**Blocked until:** M06 and T01

Run the suite on every declared Python version and Windows, macOS, and Linux where CI infrastructure permits. Verify:

- Path display and root containment.
- CRLF/LF behavior.
- Encoding and Unicode behavior.
- Symlink policy.
- Atomic replacement behavior.
- AST/signature output stability.

#### T17 - Add acceptance fixtures and regression suite

**Priority:** P1  
**Blocked until:** M06

Create representative fixtures for:

- No Python files.
- Only private APIs.
- Public classes with/without methods.
- Added/removed/changed APIs.
- Syntax errors alongside valid files.
- Missing, empty, valid, duplicate, reversed, and one-sided markers.
- Manual Markdown before and after the generated region.
- Huge/deep trees and resource-limit warnings.
- Unicode and declared source encodings.

#### T18 - Verify safety and idempotency invariants

**Priority:** P0  
**Blocked until:** T12, T13, T14, T16, and T17

Explicitly verify:

1. No scanned source is imported or executed.
2. `check` never writes source or documentation files.
3. `sync` changes only the generated section.
4. Malformed markers never cause a destructive update.
5. Repeated `sync` produces identical bytes.
6. A failed write leaves the original target intact.
7. Diagnostics identify skipped files and operational failures.
8. Generated output is deterministic for identical inputs and runtime contracts.

#### M07 - Release acceptance gate

**Blocked until:** T16, T17, and T18  
**Verification:** Requirements acceptance criteria pass, the full test suite is green on the supported matrix, and the release checklist contains no unresolved P0/P1 findings.

## 4. Testing Milestones Summary

| Milestone | Required evidence | Blocks |
|---|---|---|
| M01 Foundation | Package metadata, import smoke test, test runner | Domain implementation |
| M02 Domain contracts | Config, model, diagnostics, and exit-code unit tests | Scanner/parser work |
| M03 Static analysis | Discovery, encoding, AST, signature, and no-execution tests | Rendering/document work |
| M04 Pure content | Deterministic Markdown and marker transformation tests | Filesystem/application work |
| M05 Application behavior | Check/sync service tests and failure semantics | CLI work |
| M06 CLI contract | Subprocess tests for options, output, and exit codes | Release hardening |
| M07 Release acceptance | Cross-platform matrix, fixtures, invariants, acceptance criteria | Release |

## 5. Blocked Work Register

The following dependencies are intentional:

- **All implementation:** blocked by T01 because unresolved policies would change public behavior and test expectations.
- **Scanner:** blocked by T01 and M02 because symlink, limits, and configuration rules must be fixed before traversal code.
- **Parser:** blocked by scanner contracts and encoding decisions; it must consume discovered source records and a defined read policy.
- **Signature rendering:** blocked by AST extraction and the supported Python version decision.
- **Markdown generation:** blocked by normalized API models and signature output.
- **Marker replacement:** blocked by the Markdown/newline contract and marker grammar.
- **Filesystem writes:** blocked by pure replacement tests so file I/O cannot obscure content bugs.
- **Application orchestration:** blocked by all pure services and atomic I/O.
- **CLI:** blocked by the application result contract so command parsing does not become business logic.
- **Release testing:** blocked by a complete CLI surface and finalized runtime/platform policy.

## 6. Order Verification

The order is valid because each dependency points backward only:

```mermaid
flowchart LR
    T01[Design decisions] --> T02[Packaging and fixtures]
    T02 --> M01[Foundation gate]
    M01 --> T03[Config and exit codes]
    T03 --> T04[Domain models]
    T04 --> T05[Diagnostics]
    T05 --> M02[Domain gate]
    M02 --> T06[Scanner]
    T06 --> T07[Encoding-aware reader]
    T07 --> T08[AST extraction]
    T08 --> T09[Signature renderer]
    T09 --> M03[Static-analysis gate]
    M03 --> T10[Markdown generator]
    T10 --> T11[Marker operations]
    T11 --> M04[Pure-content gate]
    M04 --> T12[Atomic document I/O]
    T12 --> T13[Application orchestration]
    T13 --> M05[Application gate]
    M05 --> T14[CLI]
    T14 --> T15[CLI tests]
    T15 --> M06[CLI gate]
    M06 --> T16[Platform matrix]
    M06 --> T17[Acceptance fixtures]
    T16 --> T18[Invariant verification]
    T17 --> T18
    T18 --> M07[Release gate]
```

The only intentional parallelism is after M06: cross-platform execution and fixture expansion can proceed independently, then converge at invariant verification. All earlier parallel work is limited to test writing or documentation updates that do not alter unresolved contracts.

## 7. Definition of Done

The project is ready for Version 1 release when:

- The declared Python runtime and packaging metadata are complete.
- `doc-sync check` and `doc-sync sync` satisfy the CLI and exit-code contracts.
- All required scanner, parser, generator, marker, I/O, orchestration, and CLI tests pass.
- Syntax errors are isolated and reported without stopping valid-file processing.
- Source files are never imported or executed.
- Generated output is deterministic and idempotent.
- Manual Markdown outside the markers is preserved exactly.
- Failed or unsafe writes leave the original target unchanged.
- Resource, encoding, symlink, path, and concurrency policies from the design review are implemented or explicitly documented as Version 1 limitations.
- M07 release acceptance passes with no unresolved P0/P1 risk.
