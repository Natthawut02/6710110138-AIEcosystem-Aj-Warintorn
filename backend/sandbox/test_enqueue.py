import sys
import os
import asyncio
from datetime import datetime

# Add the backend/ directory to the system path to allow importing core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from arq.connections import create_pool, RedisSettings
from core.config import settings

async def main():
    print("=" * 55)
    print("  ARQ Job Enqueue Test Tool")
    print("=" * 55)
    
    # 1. Establish connection to Redis
    print(f"Connecting to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}...")
    try:
        redis_settings = RedisSettings(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT
        )
        pool = await create_pool(redis_settings)
        print("Connected to Redis successfully.")
    except Exception as e:
        print(f"ERROR: Failed to connect to Redis: {e}")
        sys.exit(1)

    # 2. Enqueue the sample job
    job_name = "simple_work"
    sample_data = {
        "title": "AIEcosystem Verification Job",
        "description": "This is a test job enqueued to verify the ARQ worker functionality.",
        "timestamp": datetime.now().isoformat(),
        "priority": "HIGH",
        "metadata": {
            "version": "1.0",
            "triggered_by": "test_enqueue.py"
        }
    }
    
    print(f"\nEnqueuing job '{job_name}' with data:")
    for k, v in sample_data.items():
        print(f"  {k}: {v}")

    try:
        # Enqueue with positional and keyword arguments
        job = await pool.enqueue_job(job_name, "Sample Positional Argument", **sample_data)
        print(f"\nSUCCESS: Job enqueued successfully!")
        print(f"  Job ID: {job.job_id}")
    except Exception as e:
        print(f"\nERROR: Failed to enqueue job: {e}")
    finally:
        # 3. Clean up and close pool
        print("\nClosing Redis pool connection...")
        await pool.close()
        print("Redis pool connection closed.")
        print("=" * 55)

if __name__ == "__main__":
    asyncio.run(main())
