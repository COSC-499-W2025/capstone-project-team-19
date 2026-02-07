from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse, DeleteResultDTO
from src.api.schemas.projects import ProjectListDTO, ProjectListItemDTO, ProjectDetailDTO
from src.api.schemas.uploads import (
    UploadDTO,
    ClassificationsRequest,
    ProjectTypesRequest,
    DedupResolveRequestDTO,
    UploadProjectFilesDTO,
    MainFileRequestDTO,
)
from src.api.schemas.git_identities import (
    GitIdentitiesResponse,
    GitIdentitiesSelectRequest,
    GitIdentityOptionDTO,
)
from src.analysis.code_collaborative.code_collaborative_analysis_helper import (
    collect_repo_authors,
    load_user_github,
    save_user_github,
    resolve_repo_for_project,
)
from src.db.uploads import get_upload_by_id
from src.db.projects import get_project_classifications
from src.db.consent import get_latest_external_consent
from src.db.uploads import update_upload_status, mark_upload_failed
from src.project_analysis import send_to_analysis
from src.services.projects_service import (
    list_projects,
    get_project_by_id,
    delete_project,
    delete_all_projects,
)
from src.services.uploads_service import (
    start_upload,
    get_upload_status,
    resolve_dedup,
    submit_classifications,
    submit_project_types,
    list_project_files,
    set_project_main_file,
)
from src.utils.helpers import zip_paths

router = APIRouter(prefix="/projects", tags=["projects"])


def _get_git_identity_options(conn: Connection, user_id: int, project: str, upload: dict) -> list[GitIdentityOptionDTO]:
    zip_path = upload.get("zip_path")
    if not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_path")

    zip_data_dir, zip_name, _base_path = zip_paths(zip_path)
    repo_dir = resolve_repo_for_project(conn, zip_data_dir, zip_name, project, user_id)
    if not repo_dir:
        raise HTTPException(status_code=404, detail="No local Git repo found for this project")

    authors = collect_repo_authors(repo_dir)
    if not authors:
        return []

    return [
        GitIdentityOptionDTO(index=i, name=an or None, email=ae or None, commit_count=c)
        for i, (an, ae, c) in enumerate(authors, start=1)
    ]


@router.get("", response_model=ApiResponse[ProjectListDTO])
def get_projects(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    rows = list_projects(conn, user_id)
    dto = ProjectListDTO(projects=[ProjectListItemDTO(**row) for row in rows])
    return ApiResponse(success=True, data=dto, error=None)


@router.post("/upload", response_model=ApiResponse[UploadDTO])
def post_projects_upload(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = start_upload(conn, user_id, file)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.get("/upload/{upload_id}", response_model=ApiResponse[UploadDTO])
def get_projects_upload(
    upload_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = get_upload_status(conn, user_id, upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.post("/upload/{upload_id}/dedup/resolve", response_model=ApiResponse[UploadDTO])
def post_upload_dedup_resolve(
    upload_id: int,
    body: DedupResolveRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = resolve_dedup(conn, user_id, upload_id, body.decisions)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.post("/upload/{upload_id}/classifications", response_model=ApiResponse[UploadDTO])
def post_upload_classifications(
    upload_id: int,
    payload: ClassificationsRequest,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = submit_classifications(conn, user_id, upload_id, payload.assignments)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.post("/upload/{upload_id}/project-types", response_model=ApiResponse[UploadDTO])
def post_upload_project_types(
    upload_id: int,
    body: ProjectTypesRequest,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = submit_project_types(conn, user_id, upload_id, body.project_types)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.get(
    "/upload/{upload_id}/projects/{project_name}/files",
    response_model=ApiResponse[UploadProjectFilesDTO],
)
def get_upload_project_files(
    upload_id: int,
    project_name: str,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    data = list_project_files(conn, user_id, upload_id, project_name)
    return ApiResponse(success=True, data=UploadProjectFilesDTO(**data), error=None)


@router.post(
    "/upload/{upload_id}/projects/{project_name}/main-file",
    response_model=ApiResponse[UploadDTO],
)
def post_upload_project_main_file(
    upload_id: int,
    project_name: str,
    body: MainFileRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = set_project_main_file(conn, user_id, upload_id, project_name, body.relpath)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.post("/upload/{upload_id}/run", response_model=ApiResponse[UploadDTO])
def post_upload_run(
    upload_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload["status"] not in {"needs_file_roles", "needs_summaries"}:
        raise HTTPException(
            status_code=409,
            detail=f"Upload not ready to run (status={upload['status']})",
        )

    zip_name = upload.get("zip_name")
    zip_path = upload.get("zip_path")
    if not zip_name or not zip_path:
        raise HTTPException(status_code=400, detail="Upload missing zip_name or zip_path")

    assignments = get_project_classifications(conn, user_id, zip_name)
    if not assignments:
        raise HTTPException(status_code=409, detail="No project classifications found for this upload")

    external_consent = get_latest_external_consent(conn, user_id)

    try:
        update_upload_status(conn, upload_id, "analyzing")
        send_to_analysis(conn, user_id, assignments, external_consent, zip_path)
        update_upload_status(conn, upload_id, "done")
    except Exception as exc:
        mark_upload_failed(conn, upload_id, str(exc))
        raise HTTPException(status_code=500, detail="Analysis failed")

    final_upload = get_upload_status(conn, user_id, upload_id)
    return ApiResponse(success=True, data=UploadDTO(**final_upload), error=None)


@router.get(
    "/upload/{upload_id}/projects/{project}/git/identities",
    response_model=ApiResponse[GitIdentitiesResponse],
)
def get_git_identities(
    upload_id: int,
    project: str,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    options = _get_git_identity_options(conn, user_id, project, upload)
    aliases = load_user_github(conn, user_id)

    selected_indices: list[int] = []
    for opt in options:
        if opt.email and opt.email.lower() in aliases["emails"]:
            selected_indices.append(opt.index)
        elif opt.name and opt.name.strip().lower() in aliases["names"]:
            selected_indices.append(opt.index)

    return ApiResponse(
        success=True,
        data=GitIdentitiesResponse(options=options, selected_indices=selected_indices),
        error=None,
    )


@router.post(
    "/upload/{upload_id}/projects/{project}/git/identities",
    response_model=ApiResponse[GitIdentitiesResponse],
)
def post_git_identities(
    upload_id: int,
    project: str,
    body: GitIdentitiesSelectRequest,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")

    options = _get_git_identity_options(conn, user_id, project, upload)
    if not options:
        raise HTTPException(status_code=404, detail="No git identities found for this project")

    max_idx = len(options)
    bad = [i for i in body.selected_indices if i < 1 or i > max_idx]
    if bad:
        raise HTTPException(
            status_code=422,
            detail={"invalid_indices": bad, "valid_range": [1, max_idx]},
        )

    emails: list[str] = []
    names: list[str] = []
    for opt in options:
        if opt.index in body.selected_indices:
            if opt.email:
                emails.append(opt.email)
            if opt.name:
                names.append(opt.name)

    if body.extra_emails:
        emails.extend(body.extra_emails)

    save_user_github(conn, user_id, emails, names)

    aliases = load_user_github(conn, user_id)
    selected_indices: list[int] = []
    for opt in options:
        if opt.email and opt.email.lower() in aliases["emails"]:
            selected_indices.append(opt.index)
        elif opt.name and opt.name.strip().lower() in aliases["names"]:
            selected_indices.append(opt.index)

    return ApiResponse(
        success=True,
        data=GitIdentitiesResponse(options=options, selected_indices=selected_indices),
        error=None,
    )


@router.delete("", response_model=ApiResponse[DeleteResultDTO])
def delete_all_user_projects(
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Delete all projects for the current user."""
    count = delete_all_projects(conn, user_id)
    return ApiResponse(success=True, data=DeleteResultDTO(deleted_count=count), error=None)


# Use `:int` so non-integers like "ranking" never match this route.
@router.get("/{project_id:int}", response_model=ApiResponse[ProjectDetailDTO])
def get_project(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    project = get_project_by_id(conn, user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    dto = ProjectDetailDTO(**project)
    return ApiResponse(success=True, data=dto, error=None)


@router.delete("/{project_id:int}", response_model=ApiResponse[None])
def delete_single_project(
    project_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Delete a single project by ID."""
    deleted = delete_project(conn, user_id, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(success=True, data=None, error=None)
