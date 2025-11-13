"""
Utilities for working with source-code file extensions.

We lean on Pygments' lexer definitions to broaden extension coverage. This
allows the parsing pipeline to recognize more programming languages without
hand-maintaining long lists.
"""
from functools import lru_cache
from collections import defaultdict
from typing import Dict, Iterable, Set, FrozenSet
import re

from pygments.lexers import get_all_lexers

_WILDCARD_CHARS = set("*?{}[]")


def _expand_braces(pattern: str) -> Iterable[str]:
    match = re.search(r"\{([^{}]+)\}", pattern)
    if not match:
        return [pattern]

    prefix = pattern[: match.start()]
    suffix = pattern[match.end() :]
    options = match.group(1).split(",")

    expanded: list[str] = []
    for option in options:
        expanded.extend(_expand_braces(prefix + option + suffix))
    return expanded


def _expand_sets(pattern: str) -> Iterable[str]:
    match = re.search(r"\[([^\]]+)\]", pattern)
    if not match:
        return [pattern]

    prefix = pattern[: match.start()]
    suffix = pattern[match.end() :]
    chars = match.group(1)

    expanded: list[str] = []
    for char in chars:
        expanded.extend(_expand_sets(prefix + char + suffix))
    return expanded


def _expand_pattern(pattern: str) -> Iterable[str]:
    """
    Expand brace and character-set globs that appear in Pygments filename
    patterns. Example:

        "*. {yaml,yml}" -> ["*.yaml", "*.yml"]
        "*.[ch]"        -> ["*.c", "*.h"]
    """
    results: list[str] = [pattern]
    expanded: list[str] = []

    while results:
        current = results.pop()
        braces = list(_expand_braces(current))
        if len(braces) > 1:
            results.extend(braces)
            continue

        sets = list(_expand_sets(current))
        if len(sets) > 1:
            results.extend(sets)
            continue

        expanded.append(current)

    return expanded


def _extract_extensions(pattern: str) -> Set[str]:
    """
    Convert a Pygments filename pattern into concrete extensions (e.g.
    "*.py" -> {".py"}). Patterns without a discernible extension are ignored.
    """
    extensions: Set[str] = set()

    for variant in _expand_pattern(pattern.strip()):
        variant = variant.lstrip("*")
        if "/" in variant:
            variant = variant.split("/")[-1]
        if "." not in variant:
            continue

        ext = variant[variant.rfind(".") :].lower()
        if not ext or any(ch in _WILDCARD_CHARS for ch in ext):
            continue
        extensions.add(ext)

    return extensions


@lru_cache(maxsize=1)
def _extension_language_map() -> Dict[str, FrozenSet[str]]:
    """
    Build a mapping of extensions -> lexers using the metadata provided by
    Pygments. The result is cached since lexer discovery is moderately
    expensive.
    """
    mapping: Dict[str, Set[str]] = defaultdict(set)

    for name, _aliases, filenames, _mimetypes in get_all_lexers():
        label = name  # human-readable name (e.g., "Python")
        if not filenames:
            continue
        for pattern in filenames:
            for ext in _extract_extensions(pattern):
                mapping[ext].add(label)

    return {ext: frozenset(sorted(names)) for ext, names in mapping.items()}


@lru_cache(maxsize=1)
def code_extensions() -> FrozenSet[str]:
    """All known code file extensions recognized via Pygments."""
    return frozenset(_extension_language_map().keys())


def get_languages_for_extension(extension: str) -> FrozenSet[str]:
    """
    Return the set of languages associated with an extension. The lookup is
    case-insensitive.
    """
    if not extension:
        return frozenset()
    ext = extension.lower()
    return _extension_language_map().get(ext, frozenset())
