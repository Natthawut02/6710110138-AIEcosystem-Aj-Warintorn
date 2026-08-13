import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from test_minio import enable_versioning, upload_file, list_object_versions, download_file

PHOTO_PATH = "sandbox/minio/my-photos.png"

print("=== STEP 1: Enable Versioning ===")
enable_versioning("my-photos")

print("\n=== STEP 2: Upload (version 1) ===")
v1 = upload_file(PHOTO_PATH, "my-photos.png")

print("\n=== STEP 3: Upload again (version 2) ===")
v2 = upload_file(PHOTO_PATH, "my-photos.png")

print("\n=== STEP 4: List all versions ===")
list_object_versions("my-photos.png")

print("\n=== STEP 5: Download WITHOUT version (should get latest = v2) ===")
download_file("my-photos.png", "sandbox/minio/downloaded_no_version.png")

print("\n=== STEP 6: Download WITH version_id (should get v1) ===")
download_file("my-photos.png", "sandbox/minio/downloaded_with_version.png", version_id=v1)

print(f"\nv1 version_id = {v1}")
print(f"v2 version_id = {v2}")
