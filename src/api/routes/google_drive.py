import html
import json

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from sqlite3 import Connection

from src.api.dependencies import get_current_user_id, get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.google_drive import (
    DriveStartRequest, DriveStartResponse,
    DriveFilesResponse, DriveFileDTO, DriveLinkRequest
)
from src.services.google_drive_service import (
    drive_start_connection, drive_handle_callback,
    drive_list_files, drive_link_files
)
from src.services.uploads_service import get_upload_status

router = APIRouter(tags=["google_drive"])
DRIVE_OAUTH_MESSAGE_SOURCE = "capstone-google-drive-oauth"


def _render_oauth_callback_page(
    *,
    title: str,
    detail: str,
    payload: dict,
    status_code: int = 200,
    auto_close: bool = False,
) -> HTMLResponse:
    payload_json = json.dumps(payload).replace("</", "<\\/")
    title_html = html.escape(title)
    detail_html = html.escape(detail)
    action_label = "Close this tab"
    action_class = "ok" if status_code < 400 else "error"

    content = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title_html}</title>
    <style>
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #f5f7fb;
        color: #14181f;
      }}
      .card {{
        width: min(560px, 92vw);
        background: #ffffff;
        border: 1px solid #d8dee8;
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 18px 34px rgba(15, 23, 42, 0.08);
      }}
      h1 {{
        margin: 0 0 10px 0;
        font-size: 1.05rem;
      }}
      p {{
        margin: 0;
        color: #4a5568;
        line-height: 1.45;
      }}
      .actions {{
        margin-top: 16px;
      }}
      button {{
        border: 1px solid #c9d2e1;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.92rem;
        background: #fff;
        cursor: pointer;
      }}
      .status.ok {{
        color: #0f5132;
      }}
      .status.error {{
        color: #842029;
      }}
    </style>
  </head>
  <body>
    <main class="card">
      <h1 class="status {action_class}">{title_html}</h1>
      <p>{detail_html}</p>
      <div class="actions">
        <button id="close-btn" type="button">{action_label}</button>
      </div>
    </main>
    <script>
      (function () {{
        var payload = {payload_json};
        try {{
          if (window.opener && !window.opener.closed) {{
            window.opener.postMessage(payload, "*");
            window.opener.focus();
          }}
        }} catch (_err) {{}}

        var closeBtn = document.getElementById("close-btn");
        closeBtn.addEventListener("click", function () {{
          window.close();
          try {{
            if (window.opener && !window.opener.closed) {{
              window.opener.focus();
            }}
          }} catch (_err) {{}}
        }});

        if ({str(auto_close).lower()}) {{
          setTimeout(function () {{
            window.close();
          }}, 180);
        }}
      }})();
    </script>
  </body>
</html>
"""
    return HTMLResponse(status_code=status_code, content=content)


@router.get("/auth/google/callback")
def get_google_callback(code: str = Query(...), state: str = Query(None), conn: Connection = Depends(get_db)):
    """OAuth callback endpoint for Google Drive."""
    try:
        result = drive_handle_callback(conn, code, state)
        return _render_oauth_callback_page(
            title="Google Drive connected",
            detail="Returning to setup and closing this tab.",
            payload={
                "source": DRIVE_OAUTH_MESSAGE_SOURCE,
                "status": "connected",
                "project_name": result.get("project_name"),
                "upload_id": result.get("upload_id"),
            },
            status_code=200,
            auto_close=True,
        )
    except HTTPException as exc:
        return _render_oauth_callback_page(
            title="Google Drive connection failed",
            detail=str(exc.detail),
            payload={
                "source": DRIVE_OAUTH_MESSAGE_SOURCE,
                "status": "error",
                "message": str(exc.detail),
            },
            status_code=exc.status_code,
            auto_close=False,
        )
    except Exception as e:
        detail = f"Failed to complete Google authorization: {str(e)}"
        return _render_oauth_callback_page(
            title="Google Drive connection failed",
            detail=detail,
            payload={
                "source": DRIVE_OAUTH_MESSAGE_SOURCE,
                "status": "error",
                "message": detail,
            },
            status_code=500,
            auto_close=False,
        )


@router.post("/projects/upload/{upload_id}/projects/{project}/drive/start", response_model=ApiResponse[DriveStartResponse])
def post_drive_start(upload_id: int, project: str, body: DriveStartRequest, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    """Start Google Drive connection flow for a project."""
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    result = drive_start_connection(conn, user_id, upload_id, project, body.connect_now)
    return ApiResponse(success=True, data=DriveStartResponse(auth_url=result.get("auth_url")), error=None)


@router.get("/projects/upload/{upload_id}/projects/{project}/drive/files", response_model=ApiResponse[DriveFilesResponse])
def get_drive_files(upload_id: int, project: str, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    """List user's Google Drive files for linking."""
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    files = drive_list_files(conn, user_id)
    if files is None:
        raise HTTPException(status_code=401, detail="Google Drive not connected. Please connect Google Drive first.")
    file_dtos = [DriveFileDTO(id=f["id"], name=f["name"], mime_type=f["mimeType"]) for f in files]
    return ApiResponse(success=True, data=DriveFilesResponse(files=file_dtos), error=None)


@router.post("/projects/upload/{upload_id}/projects/{project}/drive/link", response_model=ApiResponse[dict])
def post_drive_link(upload_id: int, project: str, body: DriveLinkRequest, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    """Link Google Drive files to a project's local files."""
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    links = [link.model_dump() for link in body.links]
    result = drive_link_files(conn, user_id, upload_id, project, links)
    if result is None:
        raise HTTPException(status_code=400, detail="Failed to link files. Check that Google Drive is connected.")
    return ApiResponse(success=True, data=result, error=None)
