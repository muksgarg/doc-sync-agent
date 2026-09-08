"""Configuration parsing and path validation."""

from __future__ import annotations

from pathlib import Path

from .model import Configuration


DEFAULT_EXCLUSIONS = (".venv", "venv", "env", "virtualenv", "__pycache__")


def build_configuration(
    root: Path,
    docs: Path,
    exclusions: tuple[str, ...] = (),
    *,
    verbose: bool = False,
    max_file_bytes: int = 5_000_000,
    max_files: int = 100_000,
    max_depth: int | None = 100,
    max_output_bytes: int = 10_000_000,
    follow_symlinks: bool = False,
    fsync: bool = False,
) -> Configuration:
    root = root.expanduser().resolve()
    if not root.exists():
        raise ValueError(f"root directory does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"root path is not a directory: {root}")
    for name, value in (
        ("max_file_bytes", max_file_bytes),
        ("max_files", max_files),
        ("max_output_bytes", max_output_bytes),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero")
    if max_depth is not None and max_depth < 0:
        raise ValueError("max_depth must be non-negative or omitted")

    target = docs if docs.is_absolute() else root / docs
    target = target.expanduser().resolve()
    combined_exclusions = tuple(dict.fromkeys((*DEFAULT_EXCLUSIONS, *exclusions)))
    return Configuration(
        root=root,
        docs=target,
        exclusions=combined_exclusions,
        verbose=verbose,
        max_file_bytes=max_file_bytes,
        max_files=max_files,
        max_depth=max_depth,
        max_output_bytes=max_output_bytes,
        follow_symlinks=follow_symlinks,
        fsync=fsync,
    )
