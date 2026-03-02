"""
Ignore rules, to avoid false matches.
We are looking for similar projects, but many of them may contain the same framework, so we must ignore them.
"""

IGNORE_DIRS = {
    ".git", ".svn", ".hg",
    "node_modules", "dist", "build", ".next", ".nuxt",
    "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache",
    ".idea", ".vscode",
    "target",  # maven
    ".gradle",
}

IGNORE_FILE_SUFFIXES = {
    ".class", ".jar", ".war",
    ".pyc", ".pyo",
    ".o", ".a", ".so", ".dll", ".dylib",
    ".exe",
}

IGNORE_FILES = {
    ".DS_Store",        # macOS folder metadata
    "Thumbs.db",        # Windows thumbnail cache
    "desktop.ini",      # Windows folder settings
    ".thumbs",          # Linux thumbnail metadata
}