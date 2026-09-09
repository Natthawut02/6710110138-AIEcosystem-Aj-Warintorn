import os
import socket
import sys
import time
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

def wait_for_port(host: str, port: int, service_name: str, timeout: int = 60):
    start = time.time()
    print(f"[MLflow Init] Waiting for {service_name} at {host}:{port}...")
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"[MLflow Init] {service_name} ({host}:{port}) is ready!")
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(1)
    print(f"[MLflow Init] Timed out waiting for {service_name} at {host}:{port}")
    return False

def ensure_minio_bucket(bucket_name: str):
    endpoint_url = os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://minio:9000")
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "admin")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "password123")
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    print(f"[MLflow Init] Checking MinIO bucket '{bucket_name}' at {endpoint_url}...")
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            region_name=region,
        )
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"[MLflow Init] Bucket '{bucket_name}' already exists.")
        except ClientError:
            print(f"[MLflow Init] Bucket '{bucket_name}' does not exist. Creating...")
            s3.create_bucket(Bucket=bucket_name)
            print(f"[MLflow Init] Bucket '{bucket_name}' created successfully!")
    except Exception as e:
        print(f"[MLflow Init] Warning when checking/creating bucket: {e}")

def main():
    pg_host = os.getenv("POSTGRES_HOST", "postgres")
    pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
    minio_host = os.getenv("MINIO_HOST", "minio")
    minio_port = int(os.getenv("MINIO_PORT", "9000"))

    wait_for_port(pg_host, pg_port, "PostgreSQL")
    wait_for_port(minio_host, minio_port, "MinIO")

    artifact_bucket = os.getenv("MLFLOW_BUCKET", "mlflow")
    ensure_minio_bucket(artifact_bucket)

    backend_store = os.getenv(
        "BACKEND_STORE_URI",
        "postgresql://admin:password123@postgres:5432/ai_database",
    )
    default_artifact_root = os.getenv(
        "DEFAULT_ARTIFACT_ROOT",
        f"s3://{artifact_bucket}/",
    )

    cmd = [
        "mlflow",
        "server",
        "--backend-store-uri",
        backend_store,
        "--default-artifact-root",
        default_artifact_root,
        "--host",
        "0.0.0.0",
        "--port",
        "5000",
    ]
    print(f"[MLflow Init] Starting MLflow Server: {' '.join(cmd)}")
    os.execvp("mlflow", cmd)

if __name__ == "__main__":
    main()
