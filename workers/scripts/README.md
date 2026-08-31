# Worker Pre-flight & Seeding Scripts 🛠️

ไดเรกทอรี `workers/scripts/` รวบรวมสคริปต์สำหรับการเตรียมข้อมูลล่วงหน้า (Pre-flight / Seeding) ก่อนเริ่มการฝึกสอนโมเดลบนระบบ AI Ecosystem

---

## 📂 รายละเอียดไฟล์

| ไฟล์ | หน้าที่และความรับผิดชอบ |
| :--- | :--- |
| **`seed_dataset_to_minio.py`** | ดาวน์โหลดชุดข้อมูล `conll2003` จาก Hugging Face Hub และแปลงเป็นรูปแบบ `.jsonl` เพื่ออัปโหลดเข้า MinIO Bucket `datasets` แยกตาม split (`train`, `validation`, `test`) |
| **`requirements.txt`** | ระบุ Dependencies ขั้นต่ำสำหรับการรัน Seeding Script (`datasets`, `minio`) |

---

## 🚀 วิธีการรัน Seeding Script

### 1. ติดตั้ง Dependencies
```powershell
cd workers/scripts
pip install -r requirements.txt
```

### 2. กำหนดค่า Environment Variables (หาก MinIO ไม่ได้อยู่ที่ localhost:9000)
```powershell
$env:MINIO_ENDPOINT="localhost:9000"
$env:MINIO_ACCESS_KEY="admin"
$env:MINIO_SECRET_KEY="password123"
$env:DATASET_BUCKET="datasets"
```

### 3. รัน Script เพื่อนำเข้าชุดข้อมูล
```powershell
python seed_dataset_to_minio.py
```

เมื่อทำงานสำเร็จ จะได้ไฟล์ใน MinIO:
- `conll2003/train.jsonl`
- `conll2003/validation.jsonl`
- `conll2003/test.jsonl`
