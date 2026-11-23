"""Turn notes.md into BookLog-notes.pdf.

Run from the project folder:
    venv\\Scripts\\python.exe notes\\build_pdf.py

notes.md format (kept deliberately simple):
    # Title               -> document title (first line)
    ## Heading            -> a new entry (date + what the prompt was about)
    - text                -> bullet point
    any other line        -> plain paragraph
    *Prompt:* text        -> the prompt summary, shown in grey italics
"""
import os
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, HRFlowable

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "notes.md"
OUTPUT = HERE / "BookLog-notes.pdf"

# Segoe UI (Windows) covers dashes, quotes and arrows; fall back to Helvetica elsewhere.
FONTS = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
try:
    pdfmetrics.registerFont(TTFont("UI", str(FONTS / "segoeui.ttf")))
    pdfmetrics.registerFont(TTFont("UI-Bold", str(FONTS / "segoeuib.ttf")))
    pdfmetrics.registerFont(TTFont("UI-Italic", str(FONTS / "segoeuii.ttf")))
    pdfmetrics.registerFontFamily("UI", normal="UI", bold="UI-Bold", italic="UI-Italic", boldItalic="UI-Bold")
    BODY, BOLD = "UI", "UI-Bold"
except Exception:
    BODY, BOLD = "Helvetica", "Helvetica-Bold"

GOLD = colors.HexColor("#b78600")
INK = colors.HexColor("#171717")
MUTED = colors.HexColor("#5f656b")

title_style = ParagraphStyle("title", fontName=BOLD, fontSize=22, leading=27, textColor=INK, spaceAfter=2)
subtitle_style = ParagraphStyle("subtitle", fontName=BODY, fontSize=10, leading=14, textColor=MUTED, spaceAfter=10)
entry_style = ParagraphStyle("entry", fontName=BOLD, fontSize=13, leading=17, textColor=INK, spaceBefore=12, spaceAfter=3)
prompt_style = ParagraphStyle("prompt", fontName=BODY, fontSize=9.5, leading=13, textColor=MUTED, spaceAfter=4)
body_style = ParagraphStyle("body", fontName=BODY, fontSize=10, leading=14, textColor=INK, spaceAfter=4)
bullet_style = ParagraphStyle("bullet", parent=body_style, spaceAfter=1)


def inline(text):
    """Escape for ReportLab, then allow **bold**, *italic* and `code`."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font face="Courier" size="9">\1</font>', text)
    return text


def build():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story, bullets = [], []

    def flush_bullets():
        if bullets:
            story.append(ListFlowable(
                [ListItem(Paragraph(inline(b), bullet_style), leftIndent=12, value="•") for b in bullets],
                bulletType="bullet", bulletColor=GOLD, leftIndent=12, spaceAfter=4,
            ))
            bullets.clear()

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("# "):
            flush_bullets()
            story.append(Paragraph(inline(line[2:]), title_style))
            story.append(Paragraph("Running notes: a short entry for every change to the project.", subtitle_style))
            story.append(HRFlowable(width="100%", thickness=1.2, color=GOLD, spaceAfter=4))
        elif line.startswith("## "):
            flush_bullets()
            story.append(Paragraph(inline(line[3:]), entry_style))
        elif line.startswith("- "):
            bullets.append(line[2:])
        elif line.startswith("*Prompt:*"):
            flush_bullets()
            story.append(Paragraph(inline(line), prompt_style))
        elif line.strip():
            flush_bullets()
            story.append(Paragraph(inline(line), body_style))
        else:
            flush_bullets()
    flush_bullets()

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(BODY, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 10 * mm, "BookLog · project notes")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title="BookLog – project notes", author="BookLog")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
