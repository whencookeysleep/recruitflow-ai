from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.demo_data import CANDIDATES


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "output" / "pdf"
FONT_PATH = Path(r"C:\Windows\Fonts\simhei.ttf")


def styles() -> dict[str, ParagraphStyle]:
    pdfmetrics.registerFont(TTFont("SimHei", str(FONT_PATH)))
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ResumeTitle", parent=base["Title"], fontName="SimHei", fontSize=22, leading=28, textColor=colors.HexColor("#17324D")
        ),
        "badge": ParagraphStyle(
            "Badge", parent=base["BodyText"], fontName="SimHei", fontSize=9, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#A33A2B")
        ),
        "section": ParagraphStyle(
            "Section", parent=base["Heading2"], fontName="SimHei", fontSize=13, leading=20, textColor=colors.HexColor("#1F6FEB"), spaceBefore=8, spaceAfter=5
        ),
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="SimHei", fontSize=10.5, leading=18, textColor=colors.HexColor("#263238")
        ),
    }


def build_resume(candidate: dict[str, str], resume_styles: dict[str, ParagraphStyle]) -> Path:
    output = OUTPUT_DIR / f"demo-resume-{candidate['slug']}.pdf"
    document = SimpleDocTemplate(
        str(output), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=16 * mm
    )
    story = [
        Paragraph(candidate["name"], resume_styles["title"]),
        Spacer(1, 2 * mm),
        Table(
            [[Paragraph("虚构演示候选人 - 仅用于 RecruitFlow AI 面试作业", resume_styles["badge"])]],
            colWidths=[170 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF3E8")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E7A977")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        ),
        Spacer(1, 5 * mm),
        Paragraph(f"应聘岗位：{candidate['position']}", resume_styles["body"]),
        Paragraph(f"意向部门：{candidate['department']}", resume_styles["body"]),
        Paragraph(f"电话：{candidate['phone']}　邮箱：{candidate['email']}", resume_styles["body"]),
        Paragraph("教育背景", resume_styles["section"]),
        Paragraph(
            f"学校：{candidate['school']}<br/>学历：{candidate['degree']}<br/>专业：{candidate['major']}<br/>毕业时间：{candidate['graduation']}",
            resume_styles["body"],
        ),
        Paragraph("专业技能", resume_styles["section"]),
        Paragraph(candidate["skills"], resume_styles["body"]),
        Paragraph("实习经历", resume_styles["section"]),
        Paragraph(candidate["experience"], resume_styles["body"]),
        Paragraph("项目经历", resume_styles["section"]),
        Paragraph(candidate["project"], resume_styles["body"]),
        Paragraph("个人说明", resume_styles["section"]),
        Paragraph("重视可验证结果、清晰协作和持续学习。所有姓名、联系方式、学校与经历均为虚构数据。", resume_styles["body"]),
    ]
    document.build(story)
    return output


def generate_resumes() -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    resume_styles = styles()
    return [build_resume(candidate, resume_styles) for candidate in CANDIDATES]


def main() -> None:
    for output in generate_resumes():
        print(output)


if __name__ == "__main__":
    main()
