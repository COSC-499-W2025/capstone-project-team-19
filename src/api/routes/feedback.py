from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from src.api.dependencies import get_current_user_id, get_db
from src.api.schemas.common import ApiResponse
from src.api.schemas.feedback import ProjectFeedbackDTO, ProjectFeedbackItemDTO
from src.services.project_feedback_service import get_project_feedback_by_project_id

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/{project_id:int}/feedback", response_model=ApiResponse[ProjectFeedbackDTO])
def get_feedback_for_project(project_id: int, user_id: int = Depends(get_current_user_id), conn: Connection = Depends(get_db)):
    data = get_project_feedback_by_project_id(conn, user_id, project_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Project not found")

    dto = ProjectFeedbackDTO(
        project_id=data["project_id"],
        project_name=data["project_name"],
        feedback=[ProjectFeedbackItemDTO(**r) for r in data["feedback"]],
    )
    return ApiResponse(success=True, data=dto, error=None)
