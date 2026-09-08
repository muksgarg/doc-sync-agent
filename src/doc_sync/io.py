"""Safe target document reads and atomic writes."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .model import Configuration, Diagnostic


def validate_target(config: Configuration) -> Diagnostic | None:
    target = config.docs
    if target.exists() and not target.is_file():
        from .diagnostics import error

        return error("DOC_TARGET", "documentation target is not a regular file", path=str(target))
    if target.is_symlink():
        from .diagnostics import error

        return error("DOC_SYMLINK", "documentation target symlinks are not supported", path=str(target))
    return None


def atomic_write(path: Path, text: str, *, fsync: bool = False) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(text)
            handle.flush()
            if fsync:
                os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
