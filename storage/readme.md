# Storage Layer & Artifacts Documentation 📦

ไดเรกทอรี `storage/` ทำหน้าที่เป็นพื้นที่จัดเก็บข้อมูลแบบ Local File System สำหรับ Artifacts, Log Files และ Model Checkpoints ที่เกิดขึ้นจากการประมวลผลของระบบ

---

## 📂 โครงสร้างไดเรกทอรี

```
storage/
├── artifacts/                     # โมเดลและผลลัพธ์จากการ Train/Evaluation
│   ├── non_time_serie_model/      # โมเดลทั่วไป (เช่น Classification, Regression)
│   └── time_serie_model/          # โมเดลประเภท Time Series (พยากรณ์ข้อมูลอนุกรมเวลา)
│       ├── 6906291404/            # โมเดล Checkpoints แต่ละ Experiment/Run ID
│       └── 6906291406/
├── logs/                          # ไฟล์บันทึกการทำงานของ Containers และ Server
│   ├── docker.log                 # Log จาก Docker Container Service
│   ├── server.log                 # Log จาก API Web Server
│   └── job_worker/                # Log จากการประมวลผลงานของ Background Workers
└── readme.md                      # เอกสารอธิบายการใช้งานส่วน Storage
```

---

## 🎯 หน้าที่ของแต่ละส่วน

1. **`artifacts/`**: 
   - จัดเก็บโมเดล AI ในรูปแบบ binary/weights (เช่น `.pkl`, `.pt`, `.onnx`) แยกตามประเภทของปัญหา (Time-Series vs Non-Time-Series) และระบุด้วย Experiment/Timestamp ID เพื่อให้สืบค้นและทำ Model Versioning ได้
2. **`logs/`**:
   - บันทึกประวัติการทำงานของระบบในระดับโครงสร้างพื้นฐาน (Docker), เซิร์ฟเวอร์ (FastAPI) และ Worker Nodes (ARQ/Redis) เพื่อความสะดวกในการ Debug และตรวจสอบย้อนหลัง (Auditability)

---

## 🔗 ความสัมพันธ์กับ MinIO Object Storage
* ในขณะที่ `storage/` จัดเก็บไฟล์ในเครื่อง Local สำหรับ Development/Caching
* MinIO (`services/minio_service.py`) จะทำหน้าที่เป็น Distributed S3 Object Storage สำหรับการใช้งานจริงระดับ Production พร้อมฟีเจอร์ Versioning และ Presigned URLs
