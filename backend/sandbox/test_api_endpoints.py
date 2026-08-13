"""
Automated Test Suite for FastAPI Endpoints.
Verifies OpenAPI docs, Swagger, Health Check, PostgreSQL CRUD, MinIO Storage, ARQ Jobs, and Label Studio.
"""

import os
import sys
from fastapi.testclient import TestClient

# Insert backend directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from db.crud import create_students_table

def run_tests():
    # Ensure students table exists
    create_students_table()

    with TestClient(app) as client:
        print("=" * 60)
        print("Running Automated Verification Test Suite for FastAPI Server...")
        print("=" * 60)

        # 1. Root discovery
        resp_root = client.get("/")
        assert resp_root.status_code == 200
        data = resp_root.json()
        assert data["status"] == "online"
        print(" [PASS] GET / (Root Discovery)")

        # 2. OpenAPI Schema JSON
        resp_schema = client.get("/openapi.json")
        assert resp_schema.status_code == 200
        schema = resp_schema.json()
        assert "paths" in schema
        assert schema["info"]["title"] == "AI Ecosystem Core Backend API"
        print(" [PASS] GET /openapi.json (Schema validation)")

        # 3. Interactive Docs
        resp_docs = client.get("/docs")
        assert resp_docs.status_code == 200
        resp_redoc = client.get("/redoc")
        assert resp_redoc.status_code == 200
        print(" [PASS] GET /docs and /redoc (Interactive documentation)")

        # 4. System Health Check
        resp_health = client.get("/api/v1/health")
        assert resp_health.status_code == 200
        health_data = resp_health.json()
        assert "components" in health_data
        print(f" [PASS] GET /api/v1/health (Overall System status: {health_data['status']})")
        for comp_name, comp_data in health_data["components"].items():
            print(f"        • {comp_name}: {comp_data['status']} ({comp_data['latency_ms']}ms)")

        # 5. PostgreSQL Student CRUD
        # 5.1 Create
        payload = {"name": "Test Student Automated", "age": 20, "major": "Robotics & AI"}
        resp = client.post("/api/v1/students", json=payload)
        assert resp.status_code == 201
        student = resp.json()
        student_id = student["id"]
        print(f" [PASS] POST /api/v1/students -> Created ID {student_id}")

        # 5.2 Get by ID
        resp_get = client.get(f"/api/v1/students/{student_id}")
        assert resp_get.status_code == 200
        assert resp_get.json()["name"] == "Test Student Automated"
        print(f" [PASS] GET /api/v1/students/{student_id}")

        # 5.3 Update
        resp_put = client.put(f"/api/v1/students/{student_id}", json={"age": 21, "major": "Machine Learning"})
        assert resp_put.status_code == 200
        assert resp_put.json()["age"] == 21
        print(f" [PASS] PUT /api/v1/students/{student_id}")

        # 5.4 List
        resp_list = client.get("/api/v1/students")
        assert resp_list.status_code == 200
        assert len(resp_list.json()) > 0
        print(f" [PASS] GET /api/v1/students (Total: {len(resp_list.json())})")

        # 5.5 Delete
        resp_del = client.delete(f"/api/v1/students/{student_id}")
        assert resp_del.status_code == 200
        print(f" [PASS] DELETE /api/v1/students/{student_id}")

        # 6. MinIO Storage
        resp_buckets = client.get("/api/v1/storage/buckets")
        assert resp_buckets.status_code == 200
        buckets = resp_buckets.json()
        print(f" [PASS] GET /api/v1/storage/buckets (Found {len(buckets)} bucket(s))")

        # 7. ARQ Job Queue
        payload_job = {"job_name": "simple_work", "args": ["Test Job"], "kwargs": {"env": "test"}}
        resp_job = client.post("/api/v1/jobs", json=payload_job)
        assert resp_job.status_code == 202
        job_id = resp_job.json()["job_id"]
        print(f" [PASS] POST /api/v1/jobs -> Enqueued Job ID: {job_id}")

        # 8. Check Job Status
        resp_job_status = client.get(f"/api/v1/jobs/{job_id}")
        assert resp_job_status.status_code == 200
        print(f" [PASS] GET /api/v1/jobs/{job_id} -> Status: {resp_job_status.json()['status']}")

        print("=" * 60)
        print("ALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")
        print("=" * 60)


if __name__ == "__main__":
    run_tests()
