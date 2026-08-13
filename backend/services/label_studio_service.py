"""
Label Studio Service.
Encapsulates Label Studio SDK / API interactions for annotation projects and tasks.
"""

from typing import List, Dict, Any, Optional
from label_studio_sdk import Client
from core.config import settings
from core.logger import get_logger
from schemas.labeling import LabelStudioProject, LabelStudioTask

logger = get_logger(__name__)


class LabelStudioService:
    """Service wrapper for communicating with the Label Studio data labeling platform."""

    def __init__(self):
        self._client: Optional[Client] = None

    def get_client(self) -> Client:
        """Lazily initialize and return Label Studio SDK Client."""
        if self._client is None:
            logger.debug(f"Initializing Label Studio client for URL: {settings.LABEL_STUDIO_URL}")
            self._client = Client(
                url=settings.LABEL_STUDIO_URL,
                api_key=settings.LABEL_STUDIO_API_KEY
            )
        return self._client

    def list_projects(self) -> List[LabelStudioProject]:
        """Fetch all projects from Label Studio."""
        client = self.get_client()
        try:
            projects = client.get_projects()
            result = []
            for p in projects:
                result.append(LabelStudioProject(
                    id=p.id,
                    title=p.title,
                    description=getattr(p, "description", None),
                    created_at=str(getattr(p, "created_at", "")),
                    task_number=getattr(p, "task_number", 0),
                    total_annotations_number=getattr(p, "total_annotations_number", 0)
                ))
            return result
        except Exception as e:
            logger.error(f"Failed to fetch Label Studio projects: {e}")
            raise

    def get_project_tasks(self, project_id: int) -> List[LabelStudioTask]:
        """Fetch all tasks within a specified project ID."""
        client = self.get_client()
        try:
            project = client.get_project(project_id)
            tasks_raw = project.get_tasks()
            tasks = []
            for t in tasks_raw:
                tasks.append(LabelStudioTask(
                    id=t.get("id"),
                    project_id=project_id,
                    data=t.get("data", {}),
                    annotations=t.get("annotations", []),
                    created_at=str(t.get("created_at", ""))
                ))
            return tasks
        except Exception as e:
            logger.error(f"Failed to fetch tasks for project ID {project_id}: {e}")
            raise

    def create_task(self, project_id: int, data: Dict[str, Any]) -> LabelStudioTask:
        """Create and push a new task into a Label Studio project."""
        client = self.get_client()
        try:
            project = client.get_project(project_id)
            task_resp = project.import_tasks([{"data": data}])
            logger.info(f"Imported task into Label Studio project ID {project_id}: {task_resp}")
            # If import_tasks returns task IDs or objects
            task_id = task_resp[0] if isinstance(task_resp, list) and task_resp else 0
            if isinstance(task_id, dict):
                task_id = task_id.get("id", 0)

            return LabelStudioTask(
                id=int(task_id) if task_id else 1,
                project_id=project_id,
                data=data,
                annotations=[],
                created_at=None
            )
        except Exception as e:
            logger.error(f"Failed to create task in project ID {project_id}: {e}")
            raise


# Global singleton instance
label_studio_service = LabelStudioService()
