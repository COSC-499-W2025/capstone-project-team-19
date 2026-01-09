"""Deduplication helpers, checking for duplication, etc."""

from pathlib import Path
from .rules import IGNORE_DIRS, IGNORE_FILE_SUFFIXES

def should_ignore_path(path: Path) -> bool:
    parts = set(path.parts)

    if any(p in IGNORE_DIRS for p in parts):
        return True
    if path.suffix.lower() in IGNORE_FILE_SUFFIXES: 
        return True
    
    return False