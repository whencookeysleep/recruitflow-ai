from pathlib import Path

from reportlab.pdfgen import canvas

from app.services.files import extract_pdf_text


def test_extract_pdf_text(tmp_path: Path) -> None:
    pdf_path = tmp_path / "resume.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(72, 720, "Name: Demo Candidate")
    c.drawString(72, 700, "Position: AI Product Manager")
    c.save()

    text = extract_pdf_text(pdf_path)

    assert "Demo Candidate" in text
    assert "AI Product Manager" in text
