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

def jaccard_similarity(hashes_a: set[str], hashes_b: set[str]) -> float:
    if not hashes_a and not hashes_b:
        return 1.0
    
    union = len(hashes_a | hashes_b)
    if union == 0:
        return 0.0
    
    inter = len(hashes_a & hashes_b)
    return inter / union