import os
from dotenv import load_dotenv
from label_studio_sdk import Client

# 1. เติม override=True เพื่อบังคับล้างค่าเก่าที่ค้างในระบบทิ้ง
load_dotenv(override=True)

LABEL_STUDIO_URL = os.getenv("LABEL_STUDIO_URL")
LABEL_STUDIO_API_KEY = os.getenv("LABEL_STUDIO_API_KEY")

def main():
    # 2. ลองพริ้นต์เช็คดูก่อนว่า Token เปลี่ยนเป็นอันใหม่แล้วหรือยัง?
    print(f"Loaded URL: {LABEL_STUDIO_URL}")
    print(f"Loaded API Key: {LABEL_STUDIO_API_KEY}") 

    # 1. เชื่อมต่อ Label Studio
    print(f"Connecting to Label Studio...")
    ls = Client(url=LABEL_STUDIO_URL, api_key=LABEL_STUDIO_API_KEY)

    # 2. ดึงรายชื่อโปรเจกต์ทั้งหมด
    ls_projects = ls.get_projects()
    print("\n=== All Projects ===")
    for proj in ls_projects:
        print(f"Project ID: {proj.id} | Title: {proj.title}")

    # 3. ดึง Task จากโปรเจกต์ที่เลือก (สมมติว่าเป็นโปรเจกต์ ID 1)
    # *** อย่าลืมเปลี่ยนเลข 1 เป็น ID ของโปรเจกต์ที่คุณสร้างไว้จริงๆ ***
    TARGET_PROJECT_ID = 1 
    
    try:
        project = ls.get_project(TARGET_PROJECT_ID)
        tasks = project.get_tasks()
        print(f"\n=== Tasks in Project ID {TARGET_PROJECT_ID} ===")
        for task in tasks:
            print(f"Task ID: {task['id']} | Data: {task['data']}")
    except Exception as e:
        print(f"\nError fetching tasks: {e}")

if __name__ == "__main__":
    main()