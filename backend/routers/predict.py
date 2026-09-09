"""
Inference & Prediction Router (WTN-A08: MLflow and Inference Worker Implementation)
-----------------------------------------------------------------------------------
ทำหน้าที่:
  1. POST /predict (หรือ /inference): รับข้อความ -> enqueue เข้า Redis (inference_queue)
     และรอรับ response คืนกลับให้ Client ทันที (Request / Response)
  2. GET /predict/{job_id} (หรือ /inference/{job_id}): ขอดูผลการทำงานด้วย job_id จาก Redis
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from services.job_service import job_service
from schemas.predict import PredictRequest, PredictResponse, JobStatusResponse
from schemas.common import ErrorResponse

INFERENCE_QUEUE_NAME = "inference_queue"

router = APIRouter(tags=["Inference & Prediction"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="ส่งข้อความไปทำนายผล Token Classification (NER)",
    description="""
ส่งข้อความไปยัง Inference Worker ผ่าน Redis Queue เพื่อระบุ Entities (NER) เช่น Person, Organization, Location

- **wait=true (ค่าเริ่มต้น)**: รอผลลัพธ์จาก Inference Worker ทันทีแบบ Synchronous Request / Response
- **wait=false**: Enqueue งานแล้วรับ `job_id` ทันที จากนั้นนำไปดึงผลลัพธ์ผ่าน `GET /predict/{job_id}`
    """,
    responses={
        200: {"description": "ประมวลผลการทำนายผลสำเร็จ (รอรับผลทันที)", "model": PredictResponse},
        202: {"description": "เข้าคิวสำเร็จ หรือกำลังประมวลผล (In progress / Queued)", "model": PredictResponse},
        500: {"description": "เกิดข้อผิดพลาดในการเชื่อมต่อ Redis / Inference Worker", "model": ErrorResponse},
    },
)
async def predict_endpoint(request: PredictRequest):
    try:
        # Enqueue งานเข้าคิว inference_queue
        job_info = await job_service.enqueue_job(
            job_name="predict_token_classification",
            kwargs={
                "text": request.text,
                "model_name": request.model_name,
                "model_version": request.model_version,
            },
            queue_name=INFERENCE_QUEUE_NAME,
        )
        job_id = job_info.job_id

        # กรณีต้องการรอรับผลทันที (ตาม Diagram /Predict Request / Response)
        if request.wait:
            result = await job_service.wait_for_job_result(
                job_id=job_id,
                queue_name=INFERENCE_QUEUE_NAME,
                timeout=request.timeout,
            )
            if result is not None and isinstance(result, dict):
                return PredictResponse(
                    job_id=job_id,
                    status=result.get("status", "complete"),
                    text=result.get("text", request.text),
                    entities=result.get("entities", []),
                    model_uri=result.get("model_uri"),
                    latency_ms=result.get("latency_ms"),
                    message="Prediction completed successfully",
                )
            else:
                # กรณีประมวลผลนานเกิน Timeout คืน 202 พร้อม job_id ให้เช็คต่อ
                return PredictResponse(
                    job_id=job_id,
                    status="in_progress",
                    text=request.text,
                    message=f"Inference is still processing. Check result with GET /predict/{job_id}",
                )

        # กรณีไม่ต้องการรอ (Async enqueue)
        return PredictResponse(
            job_id=job_id,
            status="queued",
            text=request.text,
            message=f"Job enqueued. Query status with GET /predict/{job_id}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"เกิดข้อผิดพลาดในการส่งคำขอ Predict: {str(e)}",
        )


# สร้าง Alias /inference ให้ตรงกับโจทย์ที่ระบุว่า "ควรมี /predict หรือ /inference"
@router.post(
    "/inference",
    response_model=PredictResponse,
    summary="ส่งข้อความไปทำนายผล (Alias ของ /predict)",
    include_in_schema=True,
)
async def inference_alias_endpoint(request: PredictRequest):
    return await predict_endpoint(request)


@router.get(
    "/predict/{job_id}",
    response_model=JobStatusResponse,
    summary="ขอดูผลการทำงานด้วย job_id (ของ Redis)",
    description="ตรวจสอบสถานะและดึงผลลัพธ์ของงานทำนายด้วย `job_id` จาก Redis (queued / in_progress / complete)",
)
async def get_predict_job_result(job_id: str):
    try:
        info = await job_service.get_job_status(job_id=job_id, queue_name=INFERENCE_QUEUE_NAME)
        return JobStatusResponse(
            job_id=info.job_id,
            status=info.status,
            result=info.result,
            success=info.success,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ไม่สามารถตรวจสอบผลการทำงาน job_id {job_id}: {str(e)}",
        )


@router.get(
    "/inference/{job_id}",
    response_model=JobStatusResponse,
    summary="ขอดูผลการทำงานด้วย job_id (Alias ของ /predict/{job_id})",
    include_in_schema=True,
)
async def get_inference_alias_result(job_id: str):
    return await get_predict_job_result(job_id)
