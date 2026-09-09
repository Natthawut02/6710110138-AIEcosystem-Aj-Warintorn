"""
train_job.py
-------------
ฟังก์ชันหลักที่ Trainer Worker เรียกใช้เมื่อมีงานเข้าคิว
ทำหน้าที่ตาม Diagram ของโจทย์ WTN-A07:
  1. โหลด Training Data ที่เก็บไว้ใน MinIO มาใช้
  2. เทรนโมเดล Token Classification (อ้างอิงจาก HuggingFace LLM Course บทที่ 7)
  3. บันทึก Log การเทรนไว้ (ไฟล์ .log)
  4. เก็บโมเดลที่เทรนเสร็จกลับไปที่ MinIO พร้อม Versioning
"""

import json
import logging
import os
import shutil
import tarfile
import tempfile
from datetime import datetime

import torch
from datasets import Dataset
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)

from minio_client import download_file, upload_file, ensure_bucket

import mlflow
import mlflow.transformers

DATASET_BUCKET = os.getenv("DATASET_BUCKET", "datasets")
MODEL_BUCKET = os.getenv("MODEL_BUCKET", "models")
BASE_MODEL_NAME = os.getenv("BASE_MODEL_NAME", "distilbert-base-uncased")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "token_classification")

LABEL_LIST = [
    "O", "B-PER", "I-PER", "B-ORG", "I-ORG",
    "B-LOC", "I-LOC", "B-MISC", "I-MISC",
]


def _setup_job_logger(job_id: str, log_dir: str) -> tuple[logging.Logger, str]:
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"train_{job_id}.log")

    logger = logging.getLogger(f"trainer.{job_id}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger, log_path


def _load_dataset_from_minio(dataset_object_name: str, workdir: str, logger: logging.Logger) -> Dataset:
    local_path = os.path.join(workdir, "dataset.jsonl")
    logger.info(f"กำลังโหลด dataset '{dataset_object_name}' จาก MinIO bucket '{DATASET_BUCKET}' ...")
    download_file(DATASET_BUCKET, dataset_object_name, local_path)

    rows = []
    with open(local_path, "r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    logger.info(f"โหลด dataset สำเร็จ พบ {len(rows)} rows")
    return Dataset.from_list(rows)


def _tokenize_and_align_labels(examples, tokenizer):
    tokenized_inputs = tokenizer(
        examples["tokens"], truncation=True, is_split_into_words=True
    )
    all_labels = []
    for i, labels in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(labels[word_idx])
            else:
                label_ids.append(-100)
            previous_word_idx = word_idx
        all_labels.append(label_ids)
    tokenized_inputs["labels"] = all_labels
    return tokenized_inputs


async def train_token_classification(
    ctx: dict,
    dataset_object_name: str,
    model_output_name: str,
    epochs: int = 1,
) -> dict:
    job_id = ctx.get("job_id", "unknown")
    workdir = tempfile.mkdtemp(prefix=f"train_{job_id}_")
    log_dir = os.getenv("LOG_DIR", "/app/logs")
    logger, log_path = _setup_job_logger(job_id, log_dir)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"เริ่มงานเทรน job_id={job_id} บนอุปกรณ์: {device}")

    try:
        dataset = _load_dataset_from_minio(dataset_object_name, workdir, logger)

        logger.info(f"กำลังโหลด base model '{BASE_MODEL_NAME}' ...")
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
        model = AutoModelForTokenClassification.from_pretrained(
            BASE_MODEL_NAME, num_labels=len(LABEL_LIST)
        ).to(device)

        tokenized_dataset = dataset.map(
            lambda batch: _tokenize_and_align_labels(batch, tokenizer),
            batched=True,
        )
        data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

        output_dir = os.path.join(workdir, "output")
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=8,
            logging_steps=10,
            save_strategy="no",
            report_to=[],
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
            tokenizer=tokenizer,
        )

        logger.info(f"เริ่มเทรนโมเดล {epochs} epoch(s) ...")
        train_result = trainer.train()
        logger.info(f"เทรนเสร็จสิ้น. Training loss สุดท้าย: {train_result.training_loss:.4f}")

        final_model_dir = os.path.join(workdir, "final_model")
        trainer.save_model(final_model_dir)
        tokenizer.save_pretrained(final_model_dir)

        # -------------------------------------------------------------
        # MLflow Tracking & Model Registry (WTN-A08)
        # -------------------------------------------------------------
        mlflow_run_id = None
        mlflow_model_uri = None
        try:
            logger.info(f"กำลังเชื่อมต่อไปยัง MLflow Tracking URI: {MLFLOW_TRACKING_URI} ...")
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

            with mlflow.start_run(run_name=f"train_{job_id}") as run:
                mlflow_run_id = run.info.run_id
                logger.info(f"เริ่ม MLflow Run ID: {mlflow_run_id}")

                # 1. บันทึก Parameters
                mlflow.log_params({
                    "job_id": job_id,
                    "base_model": BASE_MODEL_NAME,
                    "dataset_object_name": dataset_object_name,
                    "model_output_name": model_output_name,
                    "epochs": epochs,
                    "batch_size": 8,
                    "device": device,
                })

                # 2. บันทึก Metrics
                mlflow.log_metric("training_loss", float(train_result.training_loss))

                # 3. บันทึกและลงทะเบียน Model เข้า MLflow Model Registry
                logger.info(f"กำลังบันทึกและลงทะเบียนโมเดลเข้า MLflow Model Registry ('{model_output_name}') ...")
                mlflow.log_artifacts(final_model_dir, artifact_path="model")
                model_uri = f"runs:/{mlflow_run_id}/model"
                try:
                    reg_model = mlflow.register_model(model_uri=model_uri, name=model_output_name)
                    mlflow_model_uri = f"models:/{model_output_name}/{reg_model.version}"
                    logger.info(f"✅ ลงทะเบียนโมเดลใน MLflow Model Registry สำเร็จ: {mlflow_model_uri}")
                except Exception as reg_err:
                    logger.warning(f"MLflow model registration: {reg_err}")
                    mlflow_model_uri = model_uri

                # 4. บันทึกไฟล์ Log เข้า Artifacts ของ MLflow
                if os.path.exists(log_path):
                    mlflow.log_artifact(log_path, artifact_path="logs")

        except Exception as ml_err:
            logger.warning(f"⚠️ คำเตือนการบันทึกข้อมูลเข้า MLflow: {ml_err}")

        # -------------------------------------------------------------
        # บันทึกไฟล์ zip ลง MinIO (ยังคงเก็บไว้เพื่อความเข้ากันได้)
        # -------------------------------------------------------------
        archive_path = os.path.join(workdir, f"{model_output_name}.tar.gz")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(final_model_dir, arcname=model_output_name)
        logger.info(f"บีบอัดโมเดลเป็น {archive_path} เรียบร้อย")

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        model_object_name = f"models/{model_output_name}/{timestamp}.tar.gz"
        version_id = upload_file(MODEL_BUCKET, model_object_name, archive_path, content_type="application/gzip")
        logger.info(
            f"อัปโหลดโมเดลไปที่ MinIO bucket '{MODEL_BUCKET}' object '{model_object_name}' "
            f"(version_id={version_id}) สำเร็จ"
        )

        log_object_name = f"logs/{model_output_name}/{timestamp}.log"
        upload_file(MODEL_BUCKET, log_object_name, log_path, content_type="text/plain")

        return {
            "status": "success",
            "model_output_name": model_output_name,
            "version_id": version_id,
            "training_loss": train_result.training_loss,
            "log_object_name": log_object_name,
            "mlflow_run_id": mlflow_run_id,
            "mlflow_model_uri": mlflow_model_uri,
        }

    except Exception as e:
        logger.exception(f"งานเทรน job_id={job_id} ล้มเหลว: {e}")
        raise
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
