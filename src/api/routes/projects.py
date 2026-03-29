from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
import os
from sqlite3 import Connection

from src.api.dependencies import get_db, get_current_user_id
from src.api.schemas.common import ApiResponse, DeleteResultDTO
from src.api.schemas.projects import ProjectListDTO, ProjectListItemDTO, ProjectDetailDTO
from src.api.schemas.uploads import (
    UploadDTO,
    UploadListDTO,
    UploadListItemDTO,
    ClassificationsRequest,
    ProjectTypesRequest,
    DedupResolveRequestDTO,
    RunAnalysisRequestDTO,
    RunAnalysisReadyDTO,
    UploadProjectFilesDTO,
    MainFileRequestDTO,
    MainFileSectionsResponseDTO,
    ContributedSectionsRequestDTO,
    ManualProjectSummaryRequestDTO,
    ManualContributionSummaryRequestDTO,
    KeyRoleRequestDTO,
)
from src.api.schemas.git_identities import (
    GitIdentitiesResponse,
    GitIdentitiesSelectRequest,
    GitIdentityOptionDTO,
)
from src.services.git_identities_service import (
    get_git_identities as get_git_identities_service,
    save_git_identities as save_git_identities_service,
)
from src.db.uploads import get_upload_by_id, list_uploads_for_user
from src.services.projects_service import (
    list_projects,
    get_project_by_id,
    delete_project,
    delete_all_projects,
)
from src.services.uploads_service import (
    start_upload,
    cancel_upload,
    get_upload_status,
    resolve_dedup,
    submit_classifications,
    submit_project_types,
    list_project_files,
    set_project_main_file,
    _resolve_project_key_to_name,
)
from src.services.uploads_run_service import run_analysis_preflight
from src.api.schemas.uploads import SupportingFilesRequestDTO
from src.services.uploads_supporting_contributions_service import (
    set_project_supporting_text_files,
    set_project_supporting_csv_files,
    set_project_key_role,
)
from src.services.uploads_contribution_service import (
    list_main_file_sections,
    set_main_file_contributed_sections,
)
from src.services.uploads_manual_summaries_service import (
    set_manual_project_summary,
    set_manual_contribution_summary,
)
from src.api.schemas.uploads import EligibleRolesResponseDTO

router = APIRouter(prefix="/projects", tags=["projects"])


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


@router.get("/uploads", response_model=ApiResponse[UploadListDTO])
def get_projects_uploads(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    rows = list_uploads_for_user(conn, user_id, limit=limit, offset=offset)
    dto = UploadListDTO(
        uploads=[
            UploadListItemDTO(
                upload_id=row["upload_id"],
                status=row["status"],
                zip_name=row.get("zip_name"),
                created_at=row.get("created_at"),
            )
            for row in rows
        ]
    )
    return ApiResponse(success=True, data=dto, error=None)


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


@router.delete("/upload/{upload_id}", response_model=ApiResponse[None])
def delete_projects_upload(
    upload_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    cancel_upload(conn, user_id, upload_id)
    return ApiResponse(success=True, data=None, error=None)


@router.post("/upload/{upload_id}/run", response_model=ApiResponse[RunAnalysisReadyDTO])
def post_upload_run_preflight(
    upload_id: int,
    body: RunAnalysisRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    data = run_analysis_preflight(
        conn,
        user_id,
        upload_id,
        body.scope,
        body.force_rerun,
        mode=body.mode,
    )
    return ApiResponse(success=True, data=RunAnalysisReadyDTO(**data), error=None)


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


def _resolve_upload_project(
    conn: Connection,
    user_id: int,
    upload_id: int,
    project_key: int,
) -> tuple[dict, str]:
    """Resolve project_key to project_name for an upload. Returns (upload, project_name). Raises 404 if not found."""
    upload = get_upload_status(conn, user_id, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    project_name = _resolve_project_key_to_name(upload, project_key)
    if not project_name:
        raise HTTPException(status_code=404, detail="Project not found in this upload")
    return upload, project_name


@router.get(
    "/upload/{upload_id}/projects/{project_key:int}/files",
    response_model=ApiResponse[UploadProjectFilesDTO],
)
def get_upload_project_files(
    upload_id: int,
    project_key: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload, project_name = _resolve_upload_project(conn, user_id, upload_id, project_key)
    data = list_project_files(conn, user_id, upload_id, project_name)
    return ApiResponse(success=True, data=UploadProjectFilesDTO(**data), error=None)


@router.post(
    "/upload/{upload_id}/projects/{project_key:int}/main-file",
    response_model=ApiResponse[UploadDTO],
)
def post_upload_project_main_file(
    upload_id: int,
    project_key: int,
    body: MainFileRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload, project_name = _resolve_upload_project(conn, user_id, upload_id, project_key)
    result = set_project_main_file(conn, user_id, upload_id, project_name, body.relpath)
    return ApiResponse(success=True, data=UploadDTO(**result), error=None)


@router.get(
    "/upload/{upload_id}/projects/{project_key:int}/text/sections",
    response_model=ApiResponse[MainFileSectionsResponseDTO],
)
def get_main_file_sections_route(
    upload_id: int,
    project_key: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload, project_name = _resolve_upload_project(conn, user_id, upload_id, project_key)
    data = list_main_file_sections(conn, user_id, upload_id, project_name)
    if not data:
        raise HTTPException(status_code=404, detail="Main file sections not found")
    return ApiResponse(success=True, data=MainFileSectionsResponseDTO(**data), error=None)


@router.post(
    "/upload/{upload_id}/projects/{project_key:int}/text/contributions",
    response_model=ApiResponse[UploadDTO],
)
def post_main_file_contributed_sections(
    upload_id: int,
    project_key: int,
    body: ContributedSectionsRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload, project_name = _resolve_upload_project(conn, user_id, upload_id, project_key)
    result = set_main_file_contributed_sections(conn, user_id, upload_id, project_name, body.selected_section_ids)
    return ApiResponse(success=True, data=UploadDTO(**result), error=None)


@router.post(
    "/upload/{upload_id}/projects/{project_key:int}/supporting-text-files",
    response_model=ApiResponse[UploadDTO],
)
def post_upload_project_supporting_text_files(
    upload_id: int,
    project_key: int,
    body: SupportingFilesRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload, project_name = _resolve_upload_project(conn, user_id, upload_id, project_key)
    result = set_project_supporting_text_files(conn, user_id, upload_id, project_name, body.relpaths)
    return ApiResponse(success=True, data=UploadDTO(**result), error=None)


@router.post(
    "/upload/{upload_id}/projects/{project_key:int}/supporting-csv-files",
    response_model=ApiResponse[UploadDTO],
)
def post_upload_project_supporting_csv_files(
    upload_id: int,
    project_key: int,
    body: SupportingFilesRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload, project_name = _resolve_upload_project(conn, user_id, upload_id, project_key)
    result = set_project_supporting_csv_files(conn, user_id, upload_id, project_name, body.relpaths)
    return ApiResponse(success=True, data=UploadDTO(**result), error=None)


@router.post(
    "/upload/{upload_id}/projects/{project_key:int}/key-role",
    response_model=ApiResponse[UploadDTO],
)
def post_upload_project_key_role(
    upload_id: int,
    project_key: int,
    body: KeyRoleRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload, project_name = _resolve_upload_project(conn, user_id, upload_id, project_key)
    result = set_project_key_role(conn, user_id, upload_id, project_name, body.key_role)
    return ApiResponse(success=True, data=UploadDTO(**result), error=None)


@router.get(
    "/upload/{upload_id}/projects/{project_key}/git/identities",
    response_model=ApiResponse[GitIdentitiesResponse],
)
def get_git_identities_route(
    upload_id: int,
    project_key: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")
    options, selected_indices = get_git_identities_service(conn, user_id, upload, project_key)

    return ApiResponse(
        success=True,
        data=GitIdentitiesResponse(options=options, selected_indices=selected_indices),
        error=None,
    )


@router.post(
    "/upload/{upload_id}/projects/{project_key}/git/identities",
    response_model=ApiResponse[GitIdentitiesResponse],
)
def post_git_identities_route(
    upload_id: int,
    project_key: int,
    body: GitIdentitiesSelectRequest,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = get_upload_by_id(conn, upload_id)
    if not upload or upload["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Upload not found")
    options, selected_indices = save_git_identities_service(
        conn,
        user_id,
        upload,
        project_key,
        body.selected_indices,
        body.extra_emails,
    )

    return ApiResponse(
        success=True,
        data=GitIdentitiesResponse(options=options, selected_indices=selected_indices),
        error=None,
    )


@router.delete("", response_model=ApiResponse[DeleteResultDTO])
def delete_all_user_projects(
    refresh_resumes: bool = Query(False, description="If true, remove deleted projects from resume snapshots"),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Delete all projects for the current user."""
    count = delete_all_projects(conn, user_id, refresh_resumes=refresh_resumes)
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
    refresh_resumes: bool = Query(False, description="If true, remove deleted project from resume snapshots"),
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    """Delete a single project by ID."""
    deleted = delete_project(conn, user_id, project_id, refresh_resumes=refresh_resumes)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return ApiResponse(success=True, data=None, error=None)


@router.post(
    "/upload/{upload_id}/projects/{project_key:int}/manual-project-summary",
    response_model=ApiResponse[UploadDTO],
)
def post_manual_project_summary(
    upload_id: int,
    project_key: int,
    body: ManualProjectSummaryRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = set_manual_project_summary(conn, user_id, upload_id, project_key, body.summary_text)
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.post(
    "/upload/{upload_id}/projects/{project_key:int}/manual-contribution-summary",
    response_model=ApiResponse[UploadDTO],
)
def post_manual_contribution_summary(
    upload_id: int,
    project_key: int,
    body: ManualContributionSummaryRequestDTO,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload = set_manual_contribution_summary(
        conn,
        user_id,
        upload_id,
        project_key,
        body.manual_contribution_summary,
    )
    return ApiResponse(success=True, data=UploadDTO(**upload), error=None)


@router.get(
    "/upload/{upload_id}/projects/{project_key:int}/eligible-roles",
    response_model=ApiResponse[EligibleRolesResponseDTO],
)
def get_eligible_roles_route(
    upload_id: int,
    project_key: int,
    user_id: int = Depends(get_current_user_id),
    conn: Connection = Depends(get_db),
):
    upload, project_name = _resolve_upload_project(conn, user_id, upload_id, project_key)
    roles = get_eligible_roles_for_project(conn, user_id, upload_id, project_name)
    return ApiResponse(
        success=True,
        data=EligibleRolesResponseDTO(project_name=project_name, roles=roles),
        error=None,
    )