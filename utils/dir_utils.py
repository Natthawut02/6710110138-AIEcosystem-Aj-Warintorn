"""
Directory and Filesystem Utility Module.
Provides helper functions for path resolution, safe directory creation, and file manipulation.
"""

import os
from pathlib import Path
from typing import Union, List


def get_project_root() -> Path:
    """Returns the absolute Path of the project root directory."""
    return Path(__file__).resolve().parent.parent


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensures that a directory exists, creating all parent directories if necessary.
    Returns the resolved Path object.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_files_by_extension(directory: Union[str, Path], extension: str) -> List[Path]:
    """
    Recursively scans and returns all files matching a specific file extension (e.g. '.json', '.log').
    """
    ext = extension if extension.startswith(".") else f".{extension}"
    target_dir = Path(directory)
    if not target_dir.exists():
        return []
    return list(target_dir.rglob(f"*{ext}"))


def get_file_size_human(path: Union[str, Path]) -> str:
    """
    Returns a human-readable representation of a file size (e.g. 1.25 MB, 450 KB).
    """
    p = Path(path)
    if not p.exists() or not p.is_file():
        return "0 B"
    
    size_bytes = p.stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
