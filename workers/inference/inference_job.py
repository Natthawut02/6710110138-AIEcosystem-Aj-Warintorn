"""
inference_job.py
----------------
ฟังก์ชันหลักของ Inference Worker (WTN-A08)
ทำหน้าที่:
  1. โหลดโมเดล Token Classification (NER) จาก MLflow Model Registry
  2. รอรับคำของาน Inference จาก FastAPI ผ่าน Redis Queue (ARQ)
  3. ประมวลผลข้อความและส่งผลลัพธ์ Entities (PER, ORG, LOC, MISC) กลับไป
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
import mlflow
import mlflow.transformers
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "inference_worker.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("inference_worker")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
DEFAULT_MODEL_NAME = os.getenv("DEFAULT_MODEL_NAME", "ner_model")
BASE_MODEL_NAME = os.getenv("BASE_MODEL_NAME", "dslim/bert-base-NER")

# Global pipeline cache
CURRENT_PIPELINE = None
CURRENT_MODEL_URI = None


def get_model_pipeline(model_name: Optional[str] = None, model_version: Optional[str] = None):
    """
    โหลดโมเดลจาก MLflow Model Registry
    ถ้ายังไม่มีโมเดลใน MLflow จะ fallback ไปโหลด base pretrained NER model ให้ชั่วคราว
    """
    global CURRENT_PIPELINE, CURRENT_MODEL_URI

    target_name = model_name or DEFAULT_MODEL_NAME
    target_version = model_version or "latest"
    model_uri = f"models:/{target_name}/{target_version}"

    # ถ้าโหลดไว้แล้วและ URI เดิม ไม่ต้องโหลดซ้ำ
    if CURRENT_PIPELINE is not None and CURRENT_MODEL_URI == model_uri:
        return CURRENT_PIPELINE, CURRENT_MODEL_URI

    logger.info(f"กำลังพยายามโหลดโมเดลจาก MLflow URI: {model_uri} (Tracking URI: {MLFLOW_TRACKING_URI}) ...")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    try:
        local_model_path = mlflow.artifacts.download_artifacts(artifact_uri=model_uri)
        loaded_pipe = pipeline(
            "ner",
            model=local_model_path,
            tokenizer=local_model_path,
            aggregation_strategy="simple",
        )
        CURRENT_PIPELINE = loaded_pipe
        CURRENT_MODEL_URI = model_uri
        logger.info(f"✅ โหลดโมเดลจาก MLflow ({model_uri}) สำเร็จเรียบร้อย!")
        return CURRENT_PIPELINE, CURRENT_MODEL_URI
    except Exception as e:
        logger.warning(f"ยังไม่พบโมเดล '{model_uri}' ใน MLflow ({e}). กำลังใช้โมเดลสำรอง '{BASE_MODEL_NAME}' ...")

    # Fallback to local / huggingface base model
    if CURRENT_PIPELINE is None:
        try:
            logger.info(f"กำลังดาวน์โหลดโมเดลสำรอง {BASE_MODEL_NAME} ...")
            CURRENT_PIPELINE = pipeline(
                "ner",
                model=BASE_MODEL_NAME,
                tokenizer=BASE_MODEL_NAME,
                aggregation_strategy="simple"
            )
            CURRENT_MODEL_URI = f"huggingface:{BASE_MODEL_NAME}"
            logger.info("✅ โหลดโมเดลสำรองสำเร็จ")
        except Exception as e2:
            logger.error(f"ไม่สามารถโหลดโมเดลสำรองได้: {e2}")
            raise e2

    return CURRENT_PIPELINE, CURRENT_MODEL_URI


async def startup(ctx: dict):
    """รันเมื่อ Inference Worker เริ่มทำงาน"""
    logger.info("=" * 60)
    logger.info("Inference Worker กำลังเริ่มต้นทำงาน...")
    logger.info(f"MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
    logger.info(f"Default Model Name: {DEFAULT_MODEL_NAME}")
    try:
        pipe, uri = get_model_pipeline()
        ctx["pipeline"] = pipe
        ctx["model_uri"] = uri
        logger.info(f"Inference Worker พร้อมใช้งานกับโมเดล: {uri}")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดระหว่างเตรียมโมเดลตอน startup: {e}")
    logger.info("=" * 60)


async def shutdown(ctx: dict):
    """รันเมื่อ Inference Worker หยุดทำงาน"""
    logger.info("Inference Worker กำลังหยุดการทำงาน...")


async def predict_token_classification(
    ctx: dict,
    text: str,
    model_name: Optional[str] = None,
    model_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    ARQ Background Task สำหรับประมวลผล Inference
    - รับข้อความ text
    - ใช้โมเดล Token Classification ทำนายผล
    - ส่งคืนรายการ Entity ที่ตรวจพบ พร้อมคะแนนความมั่นใจ
    """
    start_time = time.time()
    job_id = ctx.get("job_id", "unknown")
    logger.info(f"[{job_id}] ได้รับคำขอ predict: '{text[:80]}...'")

    # โหลดหรือสลับโมเดลตามที่ร้องขอ (ถ้ามี)
    pipe, model_uri = get_model_pipeline(model_name, model_version)

    try:
        raw_results = pipe(text)
        
        LABEL_MAP = {
            "LABEL_0": "O",
            "LABEL_1": "B-PER",
            "LABEL_2": "I-PER",
            "LABEL_3": "B-ORG",
            "LABEL_4": "I-ORG",
            "LABEL_5": "B-LOC",
            "LABEL_6": "I-LOC",
            "LABEL_7": "B-MISC",
            "LABEL_8": "I-MISC",
        }

        # จัดรูปแบบผลลัพธ์ให้อ่านง่ายและเป็นมาตรฐาน JSON
        entities = []
        for item in raw_results:
            raw_label = item.get("entity_group") or item.get("entity") or ""
            mapped_label = LABEL_MAP.get(raw_label, raw_label)
            if mapped_label == "O":
                continue
            clean_label = mapped_label.replace("B-", "").replace("I-", "")
            entities.append({
                "entity_group": clean_label,
                "score": round(float(item.get("score", 0.0)), 4),
                "word": item.get("word", "").strip(),
                "start": int(item.get("start", 0)),
                "end": int(item.get("end", 0)),
            })

        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"[{job_id}] Predict สำเร็จใน {latency_ms} ms (พบ {len(entities)} entities)")

        return {
            "status": "success",
            "job_id": job_id,
            "text": text,
            "entities": entities,
            "model_uri": model_uri,
            "latency_ms": latency_ms,
        }
    except Exception as e:
        logger.exception(f"[{job_id}] Predict ล้มเหลว: {e}")
        return {
            "status": "error",
            "job_id": job_id,
            "text": text,
            "error": str(e),
            "model_uri": model_uri,
        }
