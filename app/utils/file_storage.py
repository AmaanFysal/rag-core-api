import hashlib
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def build_storage_path(document_id: int, original_filename: str) -> str:
    safe_name = original_filename.replace("/", "_").replace("\\", "_")
    return str(UPLOAD_DIR / f"{document_id}_{safe_name}")

def save_bytes(path: str, data: bytes) -> None:
    Path(path).write_bytes(data)