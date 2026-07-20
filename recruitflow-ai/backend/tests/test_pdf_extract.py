from pathlib import Path

from reportlab.pdfgen import canvas

import pytest

from app.services.files import extract_pdf_text, store_uploaded_pdf


def test_extract_pdf_text(tmp_path: Path) -> None:
    pdf_path = tmp_path / "resume.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(72, 720, "Name: Demo Candidate")
    c.drawString(72, 700, "Position: AI Product Manager")
    c.save()

    text = extract_pdf_text(pdf_path)

    assert "Demo Candidate" in text
    assert "AI Product Manager" in text


def test_store_uploaded_pdf_validates_magic_and_preserves_same_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="valid PDF"):
        store_uploaded_pdf(b"not-a-pdf", "resume.pdf", tmp_path)

    first = store_uploaded_pdf(b"%PDF-1.4\nfirst", "resume.pdf", tmp_path)
    second = store_uploaded_pdf(b"%PDF-1.4\nsecond", "resume.pdf", tmp_path)

    assert first.name == "resume.pdf"
    assert second.name.startswith("resume-")
    assert first.read_bytes() == b"%PDF-1.4\nfirst"
    assert second.read_bytes() == b"%PDF-1.4\nsecond"
