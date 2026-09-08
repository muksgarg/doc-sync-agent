# Design Review: Automated Documentation Sync

## Review Scope

This review evaluates `architecture.md` against the functional and non-functional requirements in `requirements.md`, with emphasis on correctness, portability, resilience to hostile or unusual input, and predictable CI behavior.

## Executive Summary

The architecture has a sound separation of concerns and correctly makes static AST analysis the central safety boundary. The highest-priority work is to make resource and filesystem policies explicit before implementation:

1. Define encoding, undecodable-byte, and newline behavior.
2. Prevent symlink traversal loops and clarify whether symlinked files are eligible.
3. Bound work for huge files, deeply nested trees, very long paths, and excessive diagnostic output.
4. Specify safe source-level signature rendering, including annotations and default expressions.
5. Define atomic-write durability and concurrent-modification behavior.
6. Make partial-scan semantics visible so a successful result cannot be mistaken for a complete scan.

Without these decisions, normal repositories may behave inconsistently across Windows, macOS, and Linux, and CI could report a misleadingly clean result after silently omitting source files.

## Findings

### DR-001 - Source encoding policy is underspecified

**Severity:** High

The architecture says that the parser should use an explicit encoding policy, but does not select one. Python source may declare an encoding with a PEP 263 coding cookie, may contain UTF-8 text, or may contain undecodable bytes. Using the platform default can make identical projects produce different results across machines. A coding cookie must also be honored before AST parsing.

**Impact:** False syntax errors, inconsistent docstrings, platform-dependent output, or a command failure on a file that another platform can parse.

**Mitigation:**

- Use `tokenize.open()` (or equivalent coding-cookie-aware reading) for `.py` files.
- Define behavior for an invalid or missing encoding: warn with the path and encoding error, skip the file, and continue where possible.
- Use UTF-8 for generated Markdown and document that policy.
- Define newline normalization separately for source parsing and Markdown replacement.
- Add tests for UTF-8, a valid non-UTF-8 coding cookie, invalid bytes, BOM handling, and mixed source line endings.

### DR-002 - Symlinks can create cycles or escape the selected root

**Severity:** High

A recursive `pathlib` traversal can follow symlinked directories depending on the chosen implementation. A symlink can point back to an ancestor, causing repeated traversal, or outside `--root`, unexpectedly expanding the scan scope. Symlinked files also need an explicit inclusion policy.

**Impact:** Non-termination, duplicate APIs, scanning of unintended files, and inconsistent behavior by operating system.

**Mitigation:**

- Default to not following directory symlinks.
- Decide whether symlinked `.py` files are skipped or included; the safer default is to skip them and report this only in verbose mode.
- If following links becomes a supported option, track visited directory identities using `st_dev` and `st_ino` where available, resolve paths, and enforce the root boundary.
- Add tests for an ancestor symlink, an external-directory symlink, and a symlinked Python file on platforms that support them.

**Circular-import assessment:** Circular imports between scanned Python modules are not a traversal risk because the tool never imports or executes modules. They can still be mentioned in source-level docstrings or annotations, but those are treated as text and are not resolved. The relevant cycle risk is filesystem symlink traversal, which is covered above.

### DR-003 - Resource limits are missing for huge files and trees

**Severity:** High

The pipeline is approximately linear, but it has no limits on file size, total file count, directory depth, AST size, or generated Markdown size. A generated/vendor tree or an accidentally selected binary-like file with a `.py` suffix can consume excessive memory and CPU. `ast.parse` materializes both source text and an AST.

**Impact:** CI timeouts, process termination, memory exhaustion, or unusable diagnostics.

**Mitigation:**

- Add configurable limits such as maximum source file bytes, maximum file count, maximum generated output bytes, and optional maximum directory depth.
- Check file size before reading, then use a bounded read or reject files that grow during reading.
- Define the default response: a skipped file should produce a clear warning and a non-clean scan status, while preserving the requirement that one bad file does not stop other files.
- Consider an `--allow-large-files` override rather than an unlimited default.
- Cap verbose diagnostics and summarize repeated warnings.
- Test a large source file, many files, deep nesting, and output-size limits.

### DR-004 - Deep directory trees and path portability need explicit handling

**Severity:** Medium

The architecture says recursive scanning but does not specify iterative traversal, depth behavior, or path normalization. Recursion can hit Python's recursion limit if implemented recursively. Windows adds drive letters, UNC paths, reserved names, case-insensitive comparisons, and long-path configuration concerns.

**Impact:** Crashes, missed exclusions, unstable module labels, or failures only on Windows.

**Mitigation:**

- Use an iterative `os.scandir`/`Path.iterdir` traversal with a directory stack, pruning excluded directories before enqueueing them.
- Normalize comparisons with platform-aware `Path` operations; do not compare raw path strings for root containment.
- Store root-relative POSIX-style display paths separately from filesystem paths.
- Define behavior for inaccessible directories: warn and continue where possible, but surface an incomplete-scan status.
- Add tests for deep nesting, inaccessible entries, Windows-style paths, UNC-like paths where available, and case variants.

### DR-005 - Source-level signature rendering is not sufficiently specified

**Severity:** High

The parser must preserve positional-only, keyword-only, variadic, annotations, defaults, async status, and class bases without evaluating expressions. The architecture does not define how AST nodes become stable text. Naive string conversion or `ast.unparse` alone can change formatting between supported Python versions and can mishandle comments or unavailable syntax features.

**Impact:** False drift reports, unsafe evaluation, lost signature information, or output changes after a Python upgrade.

**Mitigation:**

- Define a dedicated source-safe renderer for `ast.arguments`, return annotations, defaults, and bases.
- Use `ast.unparse` only as an implementation detail after pinning the supported Python versions and testing its output; never use `eval`, `compile` for execution, or runtime introspection.
- Decide whether formatting is canonical AST formatting or source-segment formatting. Prefer canonical formatting for determinism.
- Include `async` explicitly and define handling for type comments and positional-only separators.
- Add golden tests covering every parameter category, complex annotations, lambdas/comprehensions in defaults, strings with quotes, and Python-version-sensitive syntax.

### DR-006 - Partial-scan semantics can produce misleading success

**Severity:** High

Syntax errors are intentionally warnings, but the architecture does not distinguish a complete scan from a scan that omitted unreadable or unparsable files. `check` could return `0` when the generated documentation matches only the successfully parsed subset, even though the project contains a skipped file. The requirements allow syntax errors not to be operational failures, but users still need to know that the result is incomplete.

**Impact:** CI may pass while documentation is missing APIs from skipped files.

**Mitigation:**

- Return a structured `ScanSummary` with counts for discovered, parsed, skipped, unreadable, and oversized files.
- Always print warnings to `stderr` and include a concise incomplete-scan summary in normal output or verbose output.
- Decide and document whether skipped files affect the exit code. A conservative policy is: syntax errors remain non-fatal as required, but unreadable files return `3`; syntax-error-only scans may return the normal check/sync result while clearly warning.
- Add tests proving the exact exit-code policy for syntax errors, unreadable files, and mixed valid/invalid projects.

### DR-007 - Atomic replacement does not by itself prevent lost updates

**Severity:** High

`os.replace` protects the destination from partial writes, but it does not prevent a concurrent editor or second `doc-sync` process from changing the target between read and replace. The current architecture also does not mention flushing durability or cleanup of temporary files after failure.

**Impact:** A valid manual edit can be overwritten, or a successful return can occur before data is durable after a system failure.

**Mitigation:**

- Before replacement, optionally compare the target's metadata or content hash with the version read at the start; abort with exit `3` if it changed.
- Document that synchronization is not a locking transaction, or add a platform-appropriate lock if concurrent use must be supported.
- Flush and close the temporary file, and optionally call `os.fsync` for a stronger durability guarantee.
- Keep the temporary file in the target directory and clean it up in all error paths.
- Test replacement failure, target mutation during the operation where practical, and preservation of the original file.

### DR-008 - Marker parsing needs a precise grammar

**Severity:** Medium

The architecture correctly rejects ambiguous marker structures, but “locate exactly one” leaves edge cases open: markers inside fenced code blocks, markers with surrounding whitespace, different line endings, and marker-like text in manually maintained content. It also does not state whether the generated section includes the markers or only the content between them.

**Impact:** Accidental replacement of a code example, false malformed-document errors, or non-idempotent output.

**Mitigation:**

- Define markers as exact full lines after newline normalization, with no leading/trailing whitespace accepted unless explicitly intended.
- State that marker occurrences are structural everywhere in the document, including code fences, or implement a Markdown-aware rule. The simpler and safer Version 1 policy is to treat every exact marker line as structural and document that constraint.
- Represent the document as `prefix + start marker + generated body + end marker + suffix`, making marker ownership unambiguous.
- Add tests for code fences, inline marker text, CRLF, duplicate markers, empty bodies, adjacent markers, and trailing newlines.

### DR-009 - Target path safety and aliasing are underdefined

**Severity:** Medium

`--docs` is relative to `--root` unless absolute, but the architecture does not define whether paths containing `..`, a target equal to a source file, or a target outside the root are allowed. A target can also be a symlink, directory, device, or read-only file.

**Impact:** Accidental overwrite of an unrelated file or confusing cross-platform behavior.

**Mitigation:**

- Validate that the target is a regular file or a new regular-file path, not a directory or special file.
- Resolve relative paths against the selected root and expose the resolved target in diagnostics.
- Decide whether an absolute path outside root is supported; if supported, require explicit intent, otherwise reject it as configuration error (`2`).
- Refuse to replace a symlink target by default, or define carefully whether the link itself or its referent is updated.
- Add tests for `..`, absolute paths, existing directories, symlinks, and target/source collisions.

### DR-010 - API extraction policy has semantic ambiguities

**Severity:** Medium

The architecture repeats the requirement to include `__init__`, but does not define whether the constructor appears as a method, is folded into the class signature, or both. It also does not specify handling for overloaded definitions, decorated definitions, `if TYPE_CHECKING` blocks, class assignments, duplicate names, or a public class nested in another class.

**Impact:** Unstable or surprising generated APIs and duplicate entries.

**Mitigation:**

- Choose one representation for constructors, preferably a class entry with the `__init__` signature and no separate `__init__` method entry unless explicitly requested.
- Define that only direct module-level definitions and direct class-body methods are included in Version 1; exclude nested classes and conditional/runtime constructs unless documented otherwise.
- Preserve source order only where it is part of the output contract; otherwise sort by qualified name and kind.
- Define duplicate-name handling and add tests for overloads, decorators, `TYPE_CHECKING`, nested classes, and redefinitions.

### DR-011 - Docstring normalization can alter meaningful content or Markdown

**Severity:** Medium

`ast.get_docstring(..., clean=True)` removes indentation, but the architecture does not define how docstrings containing Markdown fences, HTML, backslashes, leading blank lines, or non-ASCII characters are escaped and embedded. A docstring can also contain text that resembles the generated markers.

**Impact:** Broken generated Markdown or unstable comparisons after normalization.

**Mitigation:**

- Define a canonical docstring policy: dedent using AST semantics, normalize line endings, preserve Unicode, and trim only specified outer whitespace.
- Render docstrings in a fenced or indented block with a fence length that cannot be closed by the content, or escape Markdown deliberately.
- Ensure marker-like text inside a docstring remains inside the generated body and cannot be mistaken for a document boundary by the updater.
- Add tests for nested fences, HTML, Unicode, blank lines, backslashes, and marker-like docstrings.

### DR-012 - Filesystem races and source consistency are not addressed

**Severity:** Medium

The scanner discovers paths, then the parser reads them later. A file can be deleted or changed between those operations, and the target can change during comparison. The architecture currently treats these as ordinary operational failures but does not define retry or reporting behavior.

**Impact:** Nondeterministic output and confusing diagnostics in active worktrees or CI checkouts.

**Mitigation:**

- Read each source file once after discovery and associate the parsed result with the bytes actually read.
- Treat disappearing or changing files as skipped/read errors with path-specific diagnostics; do not silently reuse stale data.
- Optionally record file metadata or a content hash for verbose diagnostics, not as the API identity.
- Add tests for deleted files and target changes where the filesystem test can control timing.

### DR-013 - Diagnostics can become noisy or nondeterministic

**Severity:** Low

Large repositories can produce thousands of warnings. Filesystem iteration errors and warning order may vary unless all diagnostics are collected and sorted. The architecture calls for logging or a diagnostic service but does not define a stable format.

**Impact:** Unreadable CI logs, flaky snapshot tests, and difficult automation parsing.

**Mitigation:**

- Store diagnostics as structured records with severity, code, path, line, and message.
- Sort diagnostics by normalized path, line, and diagnostic code before rendering.
- Add a summary count and a configurable output cap; preserve the exit status even when individual messages are capped.
- Keep machine-relevant status on the exit code and avoid requiring scripts to parse prose.

### DR-014 - Python version compatibility is too broad for AST output

**Severity:** Low

The architecture proposes Python 3.11+ but the requirements ask for a currently supported Python 3 version. AST fields and `ast.unparse` output can evolve, and newer syntax can fail on an older runtime. A generated document may therefore differ by interpreter version.

**Impact:** Cross-environment drift and unsupported syntax failures that are not clearly explained.

**Mitigation:**

- Pin and publish a supported version range in `pyproject.toml` and CI.
- Test every supported interpreter.
- Use `ast.parse` with the running interpreter's grammar and report unsupported syntax as a source warning with location.
- Treat the Python runtime version as part of the determinism contract, or define a minimum canonical output policy.

## Cross-Cutting Decisions Required Before Implementation

1. **Encoding:** coding-cookie-aware source reads, generated Markdown encoding, and invalid-byte behavior.
2. **Symlinks:** whether directory and file symlinks are followed.
3. **Limits:** maximum file size, file count, output size, and directory depth.
4. **Incomplete scans:** exact reporting and exit-code behavior for skipped/unreadable files.
5. **Signature formatting:** canonical AST rendering versus source segments and supported Python versions.
6. **Markers:** exact line grammar, whitespace, code-fence behavior, and body ownership.
7. **Concurrency:** whether target-change detection or locking is required.
8. **Path policy:** allowed target locations, symlink targets, and special files.
9. **Constructor/API semantics:** representation of `__init__`, overloads, nested classes, and duplicates.

## Recommended Implementation Sequence

1. Specify the decisions above in the architecture and CLI help.
2. Implement domain models and structured diagnostics first.
3. Implement scanner safety policies, including iterative traversal and symlink behavior.
4. Implement coding-cookie-aware parsing and bounded resource checks.
5. Implement a dedicated source-safe signature renderer with golden tests.
6. Implement pure marker parsing/replacement before filesystem writes.
7. Add atomic writing with target-change detection and failure cleanup.
8. Complete application orchestration and exit-code mapping.
9. Run a cross-platform test matrix with Python versions declared in `pyproject.toml`.

## Review Conclusion

The proposed component boundaries are appropriate for Version 1 and do not need a major structural redesign. The architecture should be amended with explicit policies for encoding, symlinks, resource limits, incomplete scans, signature rendering, marker grammar, path safety, and concurrent writes before implementation begins. These are specification gaps rather than reasons to replace the overall pipeline.
