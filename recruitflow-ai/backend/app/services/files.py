import hashlib
import shutil
import time
from pathlib import Path

import fitz


MAX_PDF_BYTES = 10 * 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wait_for_stable_file(path: Path, *, timeout_seconds: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_size = -1
    stable_checks = 0
    while time.monotonic() < deadline:
        size = path.stat().st_size
        if size == last_size:
            stable_checks += 1
            if stable_checks >= 2:
                return
        else:
            stable_checks = 0
            last_size = size
        time.sleep(0.25)
    raise TimeoutError(f"File did not become stable: {path}")


def extract_pdf_text(path: Path) -> str:
    with fitz.open(path) as document:
        pages = [page.get_text("text") for page in document]
    text = "\n".join(page.strip() for page in pages if page.strip()).strip()
    if not text:
        raise ValueError(f"PDF contains no extractable text: {path.name}")
    return text


def copy_to_upload_dir(source: Path, upload_dir: Path) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / source.name
    if destination.exists():
        suffix = int(time.time())
        destination = upload_dir / f"{source.stem}-{suffix}{source.suffix}"
    shutil.copy2(source, destination)
    return destination


def store_uploaded_pdf(content: bytes, filename: str, upload_dir: Path) -> Path:
    safe_name = Path(filename).name
    if not safe_name.lower().endswith(".pdf"):
        raise ValueError("Only PDF resumes are supported")
    if not content:
        raise ValueError("PDF file is empty")
    if len(content) > MAX_PDF_BYTES:
        raise ValueError("PDF file exceeds the 10 MB limit")
    if not content.startswith(b"%PDF-"):
        raise ValueError("Uploaded file is not a valid PDF")

    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / safe_name
    if destination.exists():
        digest = hashlib.sha256(content).hexdigest()[:12]
        destination = upload_dir / f"{destination.stem}-{digest}{destination.suffix}"
    if not destination.exists():
        destination.write_bytes(content)
    return destination
