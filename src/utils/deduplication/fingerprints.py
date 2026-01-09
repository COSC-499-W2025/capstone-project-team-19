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
    Returns:
      - fp_strict: hash of sorted "relpath:hash"
      - fp_loose:  hash of sorted file hashes
      - file_entries: list of (relpath_str, file_hash)
    """

    root = Path(project_root)

    entries = []
    for p in root.rglob("*"):
        if not p.is_file(): continue
        if should_ignore_path(p): continue

        relative = p.relative_to(root).as_posix()
        h = file_content_hash(p, normalize_text=True)
        entries.append((relative, h))

    # deterministic ordering
    strict_payload = "\n".join(sorted(f"{rel}:{h}" for rel, h in entries)).encode("utf-8")
    loose_payload = "\n".join(sorted(h for _, h in entries)).encode("utf-8")

    fp_strict = hashlib.sha256(strict_payload).hexdigest()
    fp_loose = hashlib.sha256(loose_payload).hexdigest()

    return fp_strict, fp_loose, entries