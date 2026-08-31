# Utilities & CLI Tooling Documentation 🛠️

ไดเรกทอรี `utils/` บรรจุเครื่องมือและฟังก์ชันช่วยเหลือ (Helper Scripts) สำหรับสนับสนุนการทำงานของระบบและนักพัฒนา

---

## 📂 โครงสร้างและไฟล์สำคัญ

```
utils/
├── export_openapi.py      # CLI Tool สำหรับ Snapshot API Spec ออกเป็น CSV และ Excel (.xlsx)
├── dir_utils.py           # ฟังก์ชันจัดการ Path และระบบไฟล์
├── logging_utils.py       # เครื่องมือช่วยอ่านและแยกวิเคราะห์ Log
└── readme.md              # คำอธิบายเครื่องมือ Utility
```

---

## 📊 1. API Snapshot Tool (`export_openapi.py`)

เครื่องมืออัตโนมัติสำหรับการสกัด (Extract) รายการ Endpoint ทั้งหมดจาก FastAPI OpenAPI Specification ออกมาเป็นไฟล์ตารางสำหรับทำรายงานและ Snapshot สถานะของ API

### ✨ ความสามารถเด่น:
1. **รองรับ 3 แหล่งข้อมูล (Data Sources)**:
   - สกัดโดยตรงจาก FastAPI App Instance (`--from-app`)
   - ดึงจาก URL ของ Server ที่กำลังรันอยู่ (`--url http://localhost:8000/openapi.json`)
   - อ่านจากไฟล์ JSON ท้องถิ่น (`--file path/to/openapi.json`)
2. **ส่งออกเป็นทั้ง CSV และ Excel (.xlsx)**:
   - **`api_snapshot.csv`**: รายการ Flat Table สรุป Method, Path, Summary, Description, Parameters, Request Body, Responses
   - **`api_snapshot.xlsx`**: รายงาน Excel แบบมืออาชีพ ใช้สไตล์สีแยกตาม HTTP Method (GET=เขียว, POST=ฟ้า, PUT=ส้ม, DELETE=แดง, PATCH=ม่วง) พร้อมระบบ Auto-Fit Column Width และแผ่นงาน **Summary Statistics** สรุปจำนวน Endpoint แยกตามโมดูล
3. **บันทึก `openapi.json`**: สำหรับใช้เป็น Schema Snapshot อ้างอิง

### 💻 วิธีการเรียกใช้งาน:

```powershell
# วิธีที่ 1: สกัดตรงจาก FastAPI App (ค่าเริ่มต้น)
python utils/export_openapi.py --from-app --output-dir .

# วิธีที่ 2: ดึงจาก Live Server Endpoint
python utils/export_openapi.py --url http://localhost:8000/openapi.json --output-dir .

# วิธีที่ 3: ระบุไฟล์ JSON ที่ต้องการแปลง
python utils/export_openapi.py --file backend/openapi.json --output-dir .
```

---

## 📁 2. Directory Helpers (`dir_utils.py`)
* `get_project_root()`: ค้นหา Path รูทของโปรเจกต์
* `ensure_dir(path)`: สร้างโฟลเดอร์อัตโนมัติหากยังไม่มี
* `list_files_by_extension(directory, ext)`: ค้นหาไฟล์ตามนามสกุลแบบ Recursive
* `get_file_size_human(path)`: แปลงขนาดไฟล์เป็นหน่วยที่อ่านง่าย (KB, MB, GB)

---

## 📜 3. Logging Helpers (`logging_utils.py`)
* `read_latest_logs(log_file, num_lines)`: ดึง Log ล่าสุด $N$ บรรทัด (Tail Log)
* `parse_log_line(line)`: แยกโครงสร้างส่วนประกอบของ Log (Timestamp, Level, Module, Message)
