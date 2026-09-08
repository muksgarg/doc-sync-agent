"""Deterministic, non-executing Python source discovery."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path

from .diagnostics import warning
from .model import Configuration, Diagnostic, ScanSummary, SourceFile


def _excluded(directory: Path, root: Path, exclusions: tuple[str, ...]) -> bool:
    name = directory.name
    if name.startswith(".") or name in exclusions:
        return True
    relative = directory.relative_to(root).as_posix()
    return any(
        fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(relative, pattern)
        for pattern in exclusions
    )


def discover_python_files(
    config: Configuration,
) -> tuple[list[SourceFile], list[Diagnostic], ScanSummary]:
    files: list[SourceFile] = []
    diagnostics: list[Diagnostic] = []
    summary = ScanSummary()
    stack: list[tuple[Path, int]] = [(config.root, 0)]

    while stack:
        directory, depth = stack.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name.casefold())
        except OSError as exc:
            diagnostics.append(warning("SCAN_READ", str(exc), path=str(directory)))
            summary.unreadable += 1
            continue

        child_directories: list[tuple[Path, int]] = []
        for entry in entries:
            path = Path(entry.path)
            try:
                is_directory = entry.is_dir(follow_symlinks=config.follow_symlinks)
                is_symlink = entry.is_symlink()
            except OSError as exc:
                diagnostics.append(warning("SCAN_ENTRY", str(exc), path=str(path)))
                summary.unreadable += 1
                continue

            if is_directory:
                if _excluded(path, config.root, config.exclusions):
                    continue
                if is_symlink and not config.follow_symlinks:
                    continue
                if config.max_depth is not None and depth >= config.max_depth:
                    diagnostics.append(
                        warning(
                            "SCAN_DEPTH",
                            f"maximum directory depth {config.max_depth} reached",
                            path=str(path),
                        )
                    )
                    summary.limited += 1
                    continue
                child_directories.append((path, depth + 1))
                continue

            if path.suffix != ".py" or (is_symlink and not config.follow_symlinks):
                continue
            summary.discovered += 1
            if len(files) >= config.max_files:
                diagnostics.append(
                    warning(
                        "SCAN_FILE_LIMIT",
                        f"maximum file count {config.max_files} reached",
                        path=str(path),
                    )
                )
                summary.limited += 1
                return files, diagnostics, summary
            try:
                size = entry.stat(follow_symlinks=False).st_size
            except OSError as exc:
                diagnostics.append(warning("SCAN_STAT", str(exc), path=str(path)))
                summary.unreadable += 1
                continue
            if size > config.max_file_bytes:
                diagnostics.append(
                    warning(
                        "SCAN_FILE_SIZE",
                        f"file exceeds maximum size of {config.max_file_bytes} bytes",
                        path=str(path),
                    )
                )
                summary.limited += 1
                continue
            files.append(
                SourceFile(
                    path=path,
                    display_path=path.relative_to(config.root).as_posix(),
                )
            )

        stack.extend(reversed(child_directories))

    files.sort(key=lambda source: source.display_path.casefold())
    return files, diagnostics, summary
