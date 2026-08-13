# Backend Service - AI Ecosystem 🚀

ระบบ Backend Server พัฒนาด้วย **FastAPI** เพื่อทำหน้าที่เป็นศูนย์กลาง (Central Orchestrator) ในการเชื่อมต่อและให้บริการ API สำหรับ Component ต่าง ๆ ในระบบ AI Ecosystem

---

## 🏗️ Architecture & Component Overview

Backend ถูกออกแบบตามแนวคิด **Modular & Layered Architecture (สถาปัตยกรรมแบบแยกชั้นและแยกโมดูล)** เพื่อให้ง่ายต่อการขยายระบบ (Scalability), บำรุงรักษา (Maintainability) และทดสอบ (Testability):

```
backend/
├── main.py                 # FastAPI Application Entrypoint & OpenAPI Configuration
├── pyproject.toml          # Project dependencies & package settings
├── worker_settings.py      # ARQ Worker settings for Redis background tasks
├── core/                   # การตั้งค่าส่วนกลางและ Utility ระบบ
│   ├── config.py           # จัดการ Environment Variables ด้วย Pydantic Settings
│   ├── logger.py           # ระบบ Logging แบบ TimedRotatingFileHandler + ANSI Console
│   └── __init__.py
├── db/                     # Data Access Layer สำหรับ PostgreSQL
│   ├── database.py         # SQLAlchemy Engine, SessionLocal, get_db Dependency
│   ├── models.py           # SQLAlchemy ORM Models (เช่น Student)
│   ├── crud.py             # CRUD Operations ฟังก์ชันมาตรฐาน
│   └── __init__.py
├── schemas/                # Data Transfer Objects (DTO) และ Pydantic V2 Schemas
│   ├── common.py           # StandardResponse, ErrorResponse, PaginatedResponse
│   ├── student.py          # StudentCreate, StudentUpdate, StudentResponse
│   ├── storage.py          # ObjectInfo, UploadResponse, BucketInfo
│   ├── job.py              # JobCreate, JobInfo
│   ├── labeling.py         # LabelStudioProject, LabelStudioTask
│   ├── health.py           # SystemHealthResponse, ComponentHealth
│   └── __init__.py
├── services/               # Business Logic Layer & Third-party SDK Wrappers
│   ├── minio_service.py    # จัดการ MinIO Object Storage & Versioning
│   ├── label_studio_service.py # เชื่อมต่อ Label Studio SDK สำหรับ Data Annotation
│   ├── job_service.py      # จัดการ ARQ Redis Queue สำหรับ Background Tasks
│   └── __init__.py
├── routers/                # API Route Controllers (พร้อม Metadata & Docs ครบถ้วน)
│   ├── health.py           # /api/v1/health (ตรวจสอบสถานะทุก Component)
│   ├── students.py         # /api/v1/students (PostgreSQL CRUD)
│   ├── storage.py          # /api/v1/storage (MinIO Upload, Download, Versioning)
│   ├── jobs.py             # /api/v1/jobs (ARQ Asynchronous Task Dispatch)
│   ├── labeling.py         # /api/v1/labeling (Label Studio Projects & Tasks)
│   └── __init__.py
├── logs/                   # บันทึก Log ประจำวัน (Daily Log Rotation)
└── sandbox/                # Test Scripts และ Verification Suite
```

---

## 🧩 รายละเอียดการทำงานของแต่ละ Component

### 1. PostgreSQL Database (`db/`)
* **หน้าที่**: จัดเก็บข้อมูลเชิงสัมพันธ์ (Relational Data)
* **Library ที่ใช้**: `SQLAlchemy 2.0`, `psycopg2-binary`
* **การทำงาน**:
  * ใช้ `database.py` จัดการ Connection Pool และสร้าง `get_db` Dependency สำหรับ FastAPI Request Lifecycle
  * `models.py` กำหนดโครงสร้างตาราง เช่น ตาราง `students`
  * `crud.py` รวมฟังก์ชัน Create, Read, Update, Delete

### 2. MinIO Object Storage (`services/minio_service.py`, `routers/storage.py`)
* **หน้าที่**: จัดเก็บไฟล์ขนาดใหญ่ โมเดล รูปภาพ และชุดข้อมูลแบบ S3-Compatible
* **Library ที่ใช้**: `minio` Python SDK
* **ฟีเจอร์เด่น**:
  * **Object Versioning**: รองรับการเปิด/ปิด Versioning ใน Bucket และเก็บประวัติไฟล์ทุก Revision
  * **Binary Streaming**: ดาวน์โหลดไฟล์โดยตรงผ่าน HTTP Stream
  * **Metadata Tracking**: รองรับการระบุ `Content-Type`, ขนาดไฟล์, ETag

### 3. Redis & ARQ Worker (`services/job_service.py`, `routers/jobs.py`, `worker_settings.py`)
* **หน้าที่**: รองรับการประมวลผลงานหนักแบบ Asynchronous (Background Processing) เช่น การ Train โมเดล หรือ Data Preprocessing
* **Library ที่ใช้**: `arq`, `redis`
* **การทำงาน**:
  * API Endpoint `/api/v1/jobs` รับคำสั่งแล้ว Enqueue ลง Redis ทันทีโดยไม่บล็อก Web Server
  * Worker ดึงงานไปประมวลผลและเก็บ Status / Result กลับมาตรวจสอบได้ผ่าน `GET /api/v1/jobs/{job_id}`

### 4. Label Studio Integration (`services/label_studio_service.py`, `routers/labeling.py`)
* **หน้าที่**: จัดการ Pipeline สำหรับ Data Annotation และ Data Labeling
* **Library ที่ใช้**: `label-studio-sdk`, `httpx`
* **การทำงาน**:
  * ดึงรายการ Projects และ Tasks
  * รองรับการ Import ข้อมูลภาพ/ข้อความจาก MinIO ส่งเข้า Label Studio อัตโนมัติ

### 5. Centralized Logger & Diagnostics (`core/logger.py`, `routers/health.py`)
* **หน้าที่**: บันทึก Log และตรวจสอบสถานะระบบ
* **ฟีเจอร์เด่น**:
  * มีระดับ Log 5 ระดับ (DEBUG, INFO, WARNING, ERROR, CRITICAL) พร้อมสี ANSI บน Console
  * หมุนเวียนไฟล์ Log รายวันอัตโนมัติ (`TimedRotatingFileHandler`) เก็บย้อนหลัง 7 วัน
  * Endpoint `/api/v1/health` ยิงทดสอบ Latency ของ PostgreSQL, Redis, MinIO, และ Label Studio แบบ Real-time

---

## 📖 API Documentation & Metadata Features

FastAPI ถูกตั้งค่า Metadata ครบถ้วนตามมาตรฐาน [FastAPI Metadata Tutorial](https://fastapi.tiangolo.com/tutorial/metadata/):

* **OpenAPI Tags & Metadata**: มีคำอธิบายรายละเอียดและ Link เอกสารภายนอกของแต่ละโมดูล
* **Rich Endpoint Annotations**: ทุก Route มี `summary`, `description` (Markdown), `response_description`, `status_code`, และแบบจำลอง Error responses (400, 404, 500)
* **Pydantic Validation & Examples**: กำหนด Validation Rules และตัวอย่าง JSON Request/Response ชัดเจน

### การเข้าดูเอกสาร API
* **Swagger UI (Interactive)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc (Detailed Spec)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **OpenAPI Schema (JSON)**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 🚀 วิธีการติดตั้งและรัน Server

### 1. ติดตั้ง Dependencies (แนะนำใช้ `uv`)
```powershell
# ติดตั้ง dependencies ผ่าน uv
uv sync
```

### 2. รัน Backend API Server
```powershell
# รันผ่าน Python ใน venv
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. รัน ARQ Worker สำหรับ Background Tasks
```powershell
# รัน ARQ Worker
.\.venv\Scripts\arq.exe worker_settings.WorkerSettings
```

### 4. รัน Automated Test Suite
```powershell
.\.venv\Scripts\python.exe sandbox/test_api_endpoints.py
```
