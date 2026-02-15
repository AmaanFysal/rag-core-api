from pathlib import Path
from pypdf import PdfReader


def extract_text_from_txt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def extract_text(path: str, file_type: str) -> str:
    ft = file_type.lower()
    if ft == "txt":
        return extract_text_from_txt(path)
    if ft == "pdf":
        return extract_text_from_pdf(path)
    raise ValueError(f"Unsupported file_type for extraction: {file_type}")
