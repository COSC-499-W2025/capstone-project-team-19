from .helpers import should_ignore_path
from pathlib import Path
import hashlib

TEXT_EXTS = {
    ".py",".js",".ts",".tsx",".jsx",".java",".kt",".c",".cpp",".h",".hpp",
    ".cs",".go",".rs",".php",".rb",".swift",
    ".html",".css",".scss",
    ".json",".yml",".yaml",".toml",".md",".txt",".xml",
}

def file_content_hash(path, normalize_text = True) -> str:
    """
    Returns hex SHA-256 of file contents. If normalize_text = True end ext looks like text, normalize CRLF -> LF.
    """

    ext = path.suffix.lower()
    h = hashlib.sha256()

    with open(path, "rb") as f:
        data = f.read()

    if normalize_text and ext in TEXT_EXTS:
        # normalize windows line endings
        data = data.replace(b"\r\n", b"\n")

    h.update(data)
    return h.hexdigest()

def project_fingerprints(project_root):
    """
    Goes through a project and computes fp_strict, fp_loose, and entries.
        fp_strict: hash of sorted "relpath:file_hash" (used for exact duplicate detection)
        fp_loose: hash of sorted file_hash values only (optional, check for same project btu different name / different location)
        entries: list of (relpath, file_hash) (stored so we can perform jaccard similarity as needed)
    """

    root = Path(project_root)
    entries: list[tuple[str, str]] = []

    # go through every file under the project root
    for p in root.rglob("*"):
        if not p.is_file(): continue

        rel = p.relative_to(root)
        if should_ignore_path(rel): 
            continue

        rel_str = rel.as_posix() # using POSIX style paths so that linux and windows behave the same

        # hash the file contents
        h = file_content_hash(p, normalize_text=True)
        entries.append((rel_str, h))

    # Build the strict fingerprint: "relpath:hash" for every file, sorted deterministically
    strict_payload = "\n".join(f"{rel}:{h}" for rel, h in sorted(entries)).encode("utf-8")

    # Build the loose fingerprint: just the file hashes, sorted
    loose_payload = "\n".join(h for _, h in sorted(entries)).encode("utf-8")

    fp_strict = hashlib.sha256(strict_payload).hexdigest()
    fp_loose = hashlib.sha256(loose_payload).hexdigest()

    return fp_strict, fp_loose, entries