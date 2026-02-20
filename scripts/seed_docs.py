"""
Uploads the two demo documents to the backend under the alice account.
Run once after clearing the database:
    python scripts/seed_docs.py
"""
import httpx

API = "http://localhost:8000"
FILES = [
    "/Users/amaanfysal/Desktop/1_The History and Future of Artificial Intelligence.txt",
    "/Users/amaanfysal/Desktop/2_UHIF_RAG_Test_Document.txt",
]


def seed():
    with httpx.Client() as client:
        r = client.post(
            f"{API}/auth/token",
            data={"username": "alice", "password": "alice_password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        for path in FILES:
            with open(path, "rb") as f:
                content = f.read()
            filename = path.split("/")[-1]
            r = client.post(
                f"{API}/documents/upload",
                headers=headers,
                files={"file": (filename, content, "text/plain")},
                timeout=120,
            )
            data = r.json()
            print(f"  doc_id={data['document_id']}  status={data['status']}  file={filename}")


if __name__ == "__main__":
    seed()
