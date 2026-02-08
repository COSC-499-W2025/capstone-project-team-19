"""
Export endpoints for resumes and portfolios.

Provides file downloads (DOCX, PDF) for:
- GET /resume/{resume_id}/export/docx
- GET /resume/{resume_id}/export/pdf
- GET /portfolio/export/docx
- GET /portfolio/export/pdf
"""

import shutil
import tempfile
from sqlite3 import Connection

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from src.api.dependencies import get_current_user, get_db
from src.db.resumes import get_resume_snapshot
from src.export.resume_docx import export_resume_record_to_docx
from src.export.resume_pdf import export_resume_record_to_pdf
from src.export.portfolio_docx import export_portfolio_to_docx
from src.export.portfolio_pdf import export_portfolio_to_pdf


router = APIRouter(tags=["export"])


def _cleanup_temp_dir(path: str) -> None:
    """Remove temporary directory after response is sent."""
    shutil.rmtree(path, ignore_errors=True)


# ------------------------------------------------------------------------------
# Resume Export Endpoints
# ------------------------------------------------------------------------------

@router.get("/resume/{resume_id}/export/docx", response_class=FileResponse)
def export_resume_docx(
    resume_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """Export a resume to DOCX format."""
    user_id = current_user["id"]
    username = current_user["username"]

    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Resume not found")

    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(_cleanup_temp_dir, temp_dir)

    filepath = export_resume_record_to_docx(
        username=username,
        record=record,
        out_dir=temp_dir,
    )

    return FileResponse(
        path=str(filepath),
        filename=filepath.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/resume/{resume_id}/export/pdf", response_class=FileResponse)
def export_resume_pdf(
    resume_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """Export a resume to PDF format."""
    user_id = current_user["id"]
    username = current_user["username"]

    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Resume not found")

    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(_cleanup_temp_dir, temp_dir)

    filepath = export_resume_record_to_pdf(
        username=username,
        record=record,
        out_dir=temp_dir,
    )

    return FileResponse(
        path=str(filepath),
        filename=filepath.name,
        media_type="application/pdf",
    )


# ------------------------------------------------------------------------------
# Portfolio Export Endpoints
# ------------------------------------------------------------------------------

@router.get("/portfolio/export/docx", response_class=FileResponse)
def export_portfolio_docx(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """Export the user's portfolio to DOCX format."""
    user_id = current_user["id"]
    username = current_user["username"]

    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(_cleanup_temp_dir, temp_dir)

    filepath = export_portfolio_to_docx(
        conn=conn,
        user_id=user_id,
        username=username,
        out_dir=temp_dir,
    )

    return FileResponse(
        path=str(filepath),
        filename=filepath.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/portfolio/export/pdf", response_class=FileResponse)
def export_portfolio_pdf(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    """Export the user's portfolio to PDF format."""
    user_id = current_user["id"]
    username = current_user["username"]

    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(_cleanup_temp_dir, temp_dir)

    filepath = export_portfolio_to_pdf(
        conn=conn,
        user_id=user_id,
        username=username,
        out_dir=temp_dir,
    )

    return FileResponse(
        path=str(filepath),
        filename=filepath.name,
        media_type="application/pdf",
    )
