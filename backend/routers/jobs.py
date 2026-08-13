"""
Background Task & Asynchronous Job Endpoints (Redis + ARQ).
Enables dispatching long-running computational workloads to background workers and monitoring job execution.
"""

from fastapi import APIRouter, HTTPException, Path, status
from services.job_service import job_service
from schemas.job import JobCreate, JobInfo
from schemas.common import ErrorResponse

router = APIRouter(
    prefix="/jobs",
    tags=["Async Task & Worker Queue"]
)


@router.post(
    "",
    response_model=JobInfo,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Asynchronous Background Task",
    description="""
Submits a computational task into the Redis-backed ARQ message queue for asynchronous processing by worker processes.

- **job_name**: The registered python function name to run in the background (default: `simple_work`).
- **args**: Positional arguments list to pass to the worker.
- **kwargs**: Keyword arguments dictionary to pass to the worker.

Returns immediately with an assigned `job_id` and initial `queued` state.
    """,
    response_description="Enqueued job metadata containing generated job ID",
    responses={
        202: {"description": "Job placed on queue successfully", "model": JobInfo},
        500: {"description": "Redis connection or queue submission failure", "model": ErrorResponse}
    }
)
async def enqueue_background_job(job_in: JobCreate):
    """Enqueue a job to the background worker pool."""
    try:
        job_info = await job_service.enqueue_job(
            job_name=job_in.job_name,
            args=job_in.args,
            kwargs=job_in.kwargs
        )
        return job_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue background job: {str(e)}"
        )


@router.get(
    "/{job_id}",
    response_model=JobInfo,
    status_code=status.HTTP_200_OK,
    summary="Check Background Job Status",
    description="""
Queries the real-time execution state of a previously dispatched background task.
Possible status values:
- `queued`: Waiting in queue for an available worker thread.
- `in_progress`: Currently executing in worker process.
- `complete`: Finished execution; `result` contains worker return value.
- `not_found`: Job expired from Redis or does not exist.
    """,
    response_description="Current job lifecycle state and results if available",
    responses={
        200: {"description": "Job status retrieved successfully", "model": JobInfo},
        500: {"description": "Redis inspection error", "model": ErrorResponse}
    }
)
async def get_job_status(
    job_id: str = Path(..., description="Unique UUID of the background job", examples=["e7b1a23c4d5e6f7a8b9c0d1e2f3a4b5c"])
):
    """Inspect background job status and results."""
    try:
        job_info = await job_service.get_job_status(job_id=job_id)
        return job_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to inspect job ID {job_id}: {str(e)}"
        )
