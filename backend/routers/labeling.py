"""
Label Studio Data Annotation Management Endpoints.
Integrates with Label Studio SDK to retrieve projects, inspect labeling tasks, and submit new annotations.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Path, status
from services.label_studio_service import label_studio_service
from schemas.labeling import LabelStudioProject, LabelStudioTask, CreateTaskRequest
from schemas.common import ErrorResponse

router = APIRouter(
    prefix="/labeling",
    tags=["Label Studio Integration"]
)


@router.get(
    "/projects",
    response_model=List[LabelStudioProject],
    status_code=status.HTTP_200_OK,
    summary="List Annotation Projects",
    description="""
Fetches all existing labeling projects configured in Label Studio.
Returns project metadata including total task count and completed annotation statistics.
    """,
    response_description="List of Label Studio annotation projects",
    responses={
        200: {"description": "Projects retrieved successfully", "model": List[LabelStudioProject]},
        500: {"description": "Label Studio connection error", "model": ErrorResponse}
    }
)
def list_projects():
    """Retrieve all annotation projects from Label Studio."""
    try:
        return label_studio_service.list_projects()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Label Studio projects: {str(e)}"
        )


@router.get(
    "/projects/{project_id}/tasks",
    response_model=List[LabelStudioTask],
    status_code=status.HTTP_200_OK,
    summary="List Tasks in Project",
    description="""
Retrieves all annotation tasks associated with a specific project ID in Label Studio.
Each task contains the payload (e.g. image URLs or text) and any completed annotation labels.
    """,
    response_description="List of labeling tasks within the specified project",
    responses={
        200: {"description": "Project tasks retrieved successfully", "model": List[LabelStudioTask]},
        404: {"description": "Project ID not found", "model": ErrorResponse},
        500: {"description": "Label Studio error", "model": ErrorResponse}
    }
)
def get_project_tasks(
    project_id: int = Path(..., ge=1, description="Label Studio Project ID", examples=[1])
):
    """Retrieve all tasks under a specific project."""
    try:
        return label_studio_service.get_project_tasks(project_id=project_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tasks for project {project_id}: {str(e)}"
        )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=LabelStudioTask,
    status_code=status.HTTP_201_CREATED,
    summary="Import New Task into Project",
    description="""
Submits a new data item (e.g. S3 image URL or dataset sample) into Label Studio for manual annotation.
    """,
    response_description="The created annotation task in Label Studio",
    responses={
        201: {"description": "Task created successfully", "model": LabelStudioTask},
        500: {"description": "Failed to create task", "model": ErrorResponse}
    }
)
def create_project_task(
    project_id: int = Path(..., ge=1, description="Target Label Studio Project ID", examples=[1]),
    task_in: CreateTaskRequest = ...
):
    """Push a new data task into a Label Studio project."""
    try:
        return label_studio_service.create_task(project_id=project_id, data=task_in.data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import task into Label Studio: {str(e)}"
        )
