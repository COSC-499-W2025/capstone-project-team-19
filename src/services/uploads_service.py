from pathlib import Path
from fastapi import UploadFile
import re

from src.db.uploads import create_upload, update_upload_zip_metadata, set_upload_state, get_upload_by_id
from src.utils.parsing import ZIP_DATA_DIR

UPLOAD_DIR = Path(ZIP_DATA_DIR) / "_uploads"

def _safe_name(name: str) -> str:
    name = (name or "").strip()
    name = name.split("/")[-1].split("\\")[-1]  # drop any path parts
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name or "upload.zip"

def start_upload(conn, user_id: int, file: UploadFile) -> dict:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload_id = create_upload(conn, user_id, status="started", state={})

    zip_name = _safe_name(file.filename or f"upload_{upload_id}.zip")
    zip_path = UPLOAD_DIR / f"{upload_id}_{zip_name}"

    with open(zip_path, "wb") as f:
        f.write(file.file.read())

    update_upload_zip_metadata(conn, upload_id, zip_name=zip_name, zip_path=str(zip_path))

    set_upload_state(conn, upload_id, state={"message": "zip saved"}, status="parsed")

    return {
        "upload_id": upload_id,
        "status": "parsed",
        "zip_name": zip_name,
        "state": {"message": "zip saved"},
    }

def get_upload_status(conn, user_id: int, upload_id: int) -> dict | None:
    row = get_upload_by_id(conn, upload_id)
    if not row or row["user_id"] != user_id:
        return None

    return {
        "upload_id": row["upload_id"],
        "status": row["status"],
        "zip_name": row.get("zip_name"),
        "state": row.get("state") or {},
    }
