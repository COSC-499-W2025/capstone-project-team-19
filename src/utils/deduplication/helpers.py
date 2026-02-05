"""Deduplication helpers, checking for duplication, etc."""

from pathlib import Path
from .rules import IGNORE_DIRS, IGNORE_FILE_SUFFIXES, IGNORE_FILES

"""
Decide whether a file inside a project should be ignored for deduplication and similarity
'path' is a relative path inside the project, so src/main.py instead of C://name//projectA/projectAstudd/src/main.py

We ignore any file inside a known framework / build directories and any file with known binary / compiled suffixes.
"""
def should_ignore_path(path: Path) -> bool:
    parts = set(path.parts)

    if any(p in IGNORE_DIRS for p in parts):
        return True
    if path.suffix.lower() in IGNORE_FILE_SUFFIXES:
        return True
    if path.name in IGNORE_FILES:
        return True
    if path.name.startswith("._"):
        return True

    return False


"""
Compute Jaccard similarity between two sets of file hashes, which basically answers 'How much of these two project snapshots overlap in content?'

Calculation: |A ∩ B| / |A U B|
    1.0 - identical
    ~0.9 - same project, small changes
    ~0.2 - different projects with shared template
    0.0 - totally different projects
"""
def jaccard_similarity(hashes_a: set[str], hashes_b: set[str]) -> float:
    if not hashes_a and not hashes_b:
        return 1.0
    
    union = len(hashes_a | hashes_b)
    if union == 0:
        return 0.0
    
    inter = len(hashes_a & hashes_b)
    return inter / union


