from __future__ import annotations

from pathlib import Path
import shutil
from typing import Set

from PIL import Image


SUPPORTED_EXTS: Set[str] = {".png", ".jpg", ".jpeg", ".webp"}


def validate_image_path(path_str: str) -> Path:
    p = Path(path_str).expanduser()
    if not p.exists() or not p.is_file():
        raise ValueError("Image path does not exist or is not a file.")
    if p.suffix.lower() not in SUPPORTED_EXTS:
        raise ValueError(f"Unsupported file type: {p.suffix}. Use PNG/JPG/JPEG/WEBP.")
    with Image.open(p) as img:
        img.verify()
    return p

MAX_SIZE = 800  # px

def save_standardized_thumbnail(
    src: Path,
    images_dir: Path,
    user_id: int,
    project_name: str,
) -> Path:
    images_dir.mkdir(parents=True, exist_ok=True)

    safe = "".join(ch if ch.isalnum() else "_" for ch in project_name).strip("_").lower()
    if not safe:
        safe = "project"

    dst = images_dir / f"u{user_id}_{safe}.png"

    with Image.open(src) as img:
        img = img.convert("RGB")  # normalize format

        # Downscale only if larger than max
        if img.width > MAX_SIZE or img.height > MAX_SIZE:
            img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)

        img.save(dst, format="PNG", optimize=True)

    return dst
