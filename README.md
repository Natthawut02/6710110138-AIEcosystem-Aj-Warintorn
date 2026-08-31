# AI Ecosystem & Backend Orchestration Platform 🌐

Repository สำหรับการจัดวางโครงสร้างระบบ **AI Ecosystem** ครบวงจร เชื่อมต่อฐานข้อมูล PostgreSQL, S3 Object Storage (MinIO), Message Broker (Redis + ARQ), และเครื่องมือ Data Annotation (Label Studio) โดยมี **FastAPI** เป็น Backend Gateway กลาง

---

## 🏛️ สถาปัตยกรรมระบบ (System Architecture)

```mermaid
graph TD
    subgraph ClientLayer [Client & Consumer Layer]
        Swagger["Swagger UI / ReDoc<br/>(/docs, /redoc)"]
        ClientApp["Frontend / ML Pipelines"]
    end

    subgraph GatewayLayer [Backend Orchestration (FastAPI)]
        MainAPI["FastAPI Application<br/>(backend/main.py)"]
        HealthRouter["Health Diagnostics<br/>(/api/v1/health)"]
        StudentRouter["Student CRUD<br/>(/api/v1/students)"]
        StorageRouter["Storage & Versioning<br/>(/api/v1/storage)"]
        JobRouter["Job Dispatcher<br/>(/api/v1/jobs)"]
        LabelRouter["Label Studio Sync<br/>(/api/v1/labeling)"]
    end

    subgraph ServiceLayer [Business & Integration Layer]
        MinioSvc["MinIO Service<br/>(minio_service.py)"]
        JobSvc["ARQ Job Service<br/>(job_service.py)"]
        LabelSvc["Label Studio Service<br/>(label_studio_service.py)"]
        DBLayer["SQLAlchemy ORM<br/>(database.py / crud.py)"]
    end

    subgraph InfrastructureLayer [Infrastructure & Services (Docker Compose)]
        PG[(PostgreSQL<br/>Port 5432)]
        RedisCache[(Redis Queue<br/>Port 6379)]
        MinIOS3[(MinIO Storage<br/>Port 9000/9001)]
        LabelStudioEngine[Label Studio<br/>Port 8080]
        ARQWorker[ARQ Worker Nodes]
    end

    ClientApp --> MainAPI
    Swagger --> MainAPI

    MainAPI --> HealthRouter
    MainAPI --> StudentRouter
    MainAPI --> StorageRouter
    MainAPI --> JobRouter
    MainAPI --> LabelRouter

    StudentRouter --> DBLayer --> PG
    StorageRouter --> MinioSvc --> MinIOS3
    JobRouter --> JobSvc --> RedisCache
    RedisCache --> ARQWorker
    LabelRouter --> LabelSvc --> LabelStudioEngine
    HealthRouter --> DBLayer
    HealthRouter --> JobSvc
    HealthRouter --> MinioSvc
    HealthRouter --> LabelSvc
```

---

## 📂 โครงสร้าง Repository (Project Structure)

```
C:\AJ.Nt\
├── .env                       # Environment Variables สำหรับโปรเจกต์
├── compose.yml                # Docker Compose สำหรับ Infrastructure ทั้งหมด
├── README.md                  # เอกสารหลักภาพรวมระบบและคู่มือการติดตั้ง
├── openapi.json               # OpenAPI 3.x Specification Schema
├── api_snapshot.csv           # รายการ Snapshot API ทั้งหมดในรูปแบบ CSV
├── api_snapshot.xlsx          # รายงาน Snapshot API พร้อมสไตล์สีและ Summary Statistics
│
├── backend/                   # ซอร์สโค้ด Backend API Server (FastAPI)
│   ├── README.md              # คำอธิบายสถาปัตยกรรมและรายละเอียดของ Backend
│   ├── main.py                # จุดเริ่มต้นแอปพลิเคชันและการตั้งค่า OpenAPI Metadata
│   ├── pyproject.toml         # จัดการ Dependencies ด้วย uv / pyproject
│   ├── worker_settings.py     # การตั้งค่าสำหรับ ARQ Worker
│   ├── core/                  # Configuration & Centralized Colored Logger
│   ├── db/                    # SQLAlchemy Database Models, Session, CRUD
│   ├── schemas/               # Pydantic V2 DTOs (Request / Response Models)
│   ├── services/              # Wrapper Services สำหรับเชื่อมต่อ 3rd-party Libraries
│   ├── routers/               # Modular API Routers (Health, Students, Storage, Jobs, Labeling)
│   ├── logs/                  # Daily Rotating Log Files
│   └── sandbox/               # Automated Endpoint Test Suite & Verification Scripts
│
├── storage/                   # Local Storage, Model Artifacts & Server Logs
│   └── readme.md              # รายละเอียดการจัดเก็บ Model Artifacts
│
├── utils/                     # เครื่องมือสนับสนุนและ Helper Scripts
│   ├── export_openapi.py      # Script สกัด openapi.json เป็น Excel / CSV Snapshot
│   ├── dir_utils.py           # ตัวช่วยจัดการ Path และระบบไฟล์
│   ├── logging_utils.py       # ตัวช่วยอ่านและ Parse ข้อมูล Log
│   └── readme.md              # รายละเอียดเครื่องมือใน Utils
│
├── diagrams/                  # ไดอะแกรมแสดงสถาปัตยกรรมระบบ
└── workers/                   # รายละเอียดระบบ Background Asynchronous Workers
    └── readme.md
```

---

## 🛠️ รายละเอียด Components และ Library ที่ใช้งาน

| Component | Library / Driver | หน้าที่การทำงาน |
|---|---|---|
| **API Framework** | `fastapi`, `uvicorn`, `pydantic` | ให้บริการ RESTful API Gateway, Validation, และ OpenAPI Schema อัตโนมัติ |
| **Relational Database** | `sqlalchemy`, `psycopg2-binary` | จัดการฐานข้อมูล PostgreSQL ผ่าน ORM และ Connection Pool |
| **Object Storage** | `minio` Python SDK | อัปโหลด/ดาวน์โหลดไฟล์ขนาดใหญ่ และทำ Object Versioning |
| **Task Queue / Broker** | `arq`, `redis` | จัดคิวและประมวลผลงานแบบ Asynchronous เบื้องหลัง |
| **Data Annotation** | `label-studio-sdk`, `httpx` | เชื่อมต่อและส่งต่องาน Annotation เข้า Label Studio |
| **Config & Logging** | `pydantic-settings`, `logging` | จัดการ Environment variables และระบบ Log 5 ระดับแบบหมุนเวียนรายวัน |
| **Export & Snapshot Tool** | `openpyxl`, `pandas` | สกัด OpenAPI Specification ออกเป็นไฟล์ Excel และ CSV |

---

## 📋 การใช้งาน FastAPI Metadata สำหรับ API Documentation

ระบบได้นำคุณสมบัติ Metadata ของ FastAPI มาใช้อย่างครบถ้วน:
* **App Metadata**: กำหนด `title`, `summary`, `description`, `version`, `contact`, `license_info`, และ `openapi_tags`
* **Route Metadata**: ทุก Endpoint มี `tags`, `summary`, `description` (Markdown), `response_description`, `status_code`, และแบบจำลอง Error responses
* **Pydantic Validation**: มีคำอธิบาย Field ทุกฟิลด์ พร้อม Example Data

### จุดเชื่อมต่อเอกสาร API:
* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 📊 ระบบ Snapshot API List (แปลง openapi.json -> Excel / CSV)

สามารถใช้ Script `utils/export_openapi.py` เพื่อ Snapshot รายการ Endpoint ทั้งหมดในระบบ:

```powershell
# สกัดรายการ API และสร้าง openapi.json, api_snapshot.csv, api_snapshot.xlsx
python utils/export_openapi.py --from-app --output-dir .
```

### ผลลัพธ์ที่ได้:
1. **`openapi.json`**: สเปกเต็มของ API ตามมาตรฐาน OpenAPI 3.1
2. **`api_snapshot.csv`**: ตาราง Flat format เหมาะสำหรับนำไปวิเคราะห์ต่อ
3. **`api_snapshot.xlsx`**: รายงาน Excel สวยงาม จัดสีตาม HTTP Method (GET, POST, PUT, DELETE) พร้อมแผ่นงาน Summary สรุปจำนวน Endpoint แยกตามโมดูล

---

## 🚀 เริ่มต้นใช้งาน (Quick Start)

### วิธีที่ 1: รันระบบทั้งหมดด้วย Docker Compose (แนะนำ)
สั่ง Build และรัน Services ทั้งหมด (FastAPI, Redis, PostgreSQL, MinIO, Label Studio, Trainer Worker):
```powershell
docker compose up -d --build
```

### วิธีที่ 2: รัน Backend API Server ใน Local Development Mode
```powershell
# 1. รัน Infrastructure Services
docker compose up -d redis postgres minio label-studio

# 2. รัน FastAPI Backend Server
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 3. รัน Background Task Worker (เปิด Terminal ใหม่)
cd backend
.\.venv\Scripts\arq.exe worker_settings.WorkerSettings
```

### การทดสอบระบบ (Automated Test Suite)
```powershell
cd backend
.\.venv\Scripts\python.exe sandbox/test_api_endpoints.py
```
