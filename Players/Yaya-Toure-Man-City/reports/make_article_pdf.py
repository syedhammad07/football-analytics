"""Turn docs/ARTICLE.md (every chart with its explanation) into reports/Yaya_Toure_article.pdf"""
import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether,
                                PageBreak, HRFlowable, ListFlowable, ListItem, Table, TableStyle)

HERE = Path(__file__).parent
SRC = HERE.parent / "docs" / "ARTICLE.md"
OUT = HERE / "Yaya_Toure_article.pdf"
DARK, MUTED, BLUE, RULE = HexColor("#1A1A18"), HexColor("#6B6A64"), HexColor("#1C2C5B"), HexColor("#DCDAD3")

FONT_DIR = str(HERE.parent / "assets" / "fonts") + "/"  # Barlow (SIL Open Font License)
try:
    for name, f in [("Body", "Barlow-Regular.ttf"), ("Body-Bold", "Barlow-SemiBold.ttf"),
                    ("Body-Italic", "Barlow-Italic.ttf"), ("Body-BoldItalic", "Barlow-SemiBold.ttf"),
                    ("Head", "BarlowCondensed-Bold.ttf")]:
        pdfmetrics.registerFont(TTFont(name, FONT_DIR + f))
    addMapping("Body", 0, 0, "Body"); addMapping("Body", 1, 0, "Body-Bold")
    addMapping("Body", 0, 1, "Body-Italic"); addMapping("Body", 1, 1, "Body-BoldItalic")
    BODY, BOLD, HEAD = "Body", "Body-Bold", "Head"
except Exception:
    BODY, BOLD, HEAD = "Helvetica", "Helvetica-Bold", "Helvetica-Bold"

S = {
    "title": ParagraphStyle("title", fontName=HEAD, fontSize=34, leading=37, textColor=DARK, spaceAfter=8),
    "sub": ParagraphStyle("sub", fontName=BOLD, fontSize=13, leading=17, textColor=DARK, spaceAfter=6),
    "meta": ParagraphStyle("meta", fontName=BODY, fontSize=9, leading=13, textColor=MUTED, spaceAfter=14),
    "part": ParagraphStyle("part", fontName=HEAD, fontSize=24, leading=28, textColor=BLUE, spaceBefore=4, spaceAfter=10),
    "chart": ParagraphStyle("chart", fontName=BOLD, fontSize=12.5, leading=16, textColor=DARK, spaceBefore=14, spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName=BODY, fontSize=8.5, leading=11, textColor=DARK),
    "callout": ParagraphStyle("callout", fontName=BODY, fontSize=10.5, leading=15, textColor=DARK, backColor=HexColor("#E8F1FA"),
                              borderColor=BLUE, borderWidth=0, borderPadding=(8, 10, 8, 10), leftIndent=10, rightIndent=10,
                              spaceBefore=10, spaceAfter=14),
    "quote": ParagraphStyle("quote", fontName=BODY, fontSize=10.5, leading=15, textColor=DARK, backColor=HexColor("#F4F2EE"),
                            borderPadding=(6, 10, 6, 10), leftIndent=10, rightIndent=10, spaceBefore=6, spaceAfter=12),
    "body": ParagraphStyle("body", fontName=BODY, fontSize=10.5, leading=15, textColor=DARK, spaceAfter=7, alignment=TA_LEFT),
}

def inline(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)            # links -> text
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text.replace("&lt;br&gt;", "<br/>")

def chart_image(rel):
    path = (SRC.parent / rel).resolve()
    w, h = PILImage.open(path).size
    max_w, max_h = A4[0] - 40 * mm, 120 * mm
    s = min(max_w / w, max_h / h)
    return Image(str(path), w * s, h * s)

story, block, bullets, numbered, rows = [], None, [], [], []

def flush_lists():
    global bullets, numbered, rows
    if rows:
        cells = [[Paragraph(("<b>%s</b>" if i == 0 else "%s") % inline(c), S["cell"]) for c in r] for i, r in enumerate(rows)]
        tbl = Table(cells, colWidths=[(A4[0] - 40 * mm) / len(rows[0])] * len(rows[0]), repeatRows=1)
        tbl.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.8, BLUE), ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE),
                                 ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        (block if block is not None else story).extend([tbl, Spacer(1, 8)])
        rows = []
    for items, kind in ((bullets, "bullet"), (numbered, "1")):
        if items:
            lst = ListFlowable([ListItem(Paragraph(inline(t), S["body"]), leftIndent=14) for t in items],
                               bulletType=kind, start="•" if kind == "bullet" else None,
                               bulletFontName=BODY, bulletFontSize=9, leftIndent=14)
            (block if block is not None else story).append(lst)
    bullets, numbered = [], []

def close_block():
    global block
    flush_lists()
    if block:
        story.append(KeepTogether(block[:3]))   # keep heading, chart and first paragraph on one page
        story.extend(block[3:])
    block = None

for line in SRC.read_text(encoding="utf-8").splitlines():
    t = line.strip()
    if t.startswith("|"):
        if not re.match(r"^\|[\s\-:|]+\|$", t):
            rows.append([c.strip() for c in t.strip("|").split("|")])
        continue
    if t.startswith("- "):
        bullets.append(t[2:]); continue
    if re.match(r"^\d+\. ", t):
        numbered.append(re.sub(r"^\d+\. ", "", t)); continue
    flush_lists()
    target = block if block is not None else story
    if not t or t == "---":
        continue
    if t.startswith("# "):
        story.append(Paragraph(inline(t[2:]), S["title"]))
    elif t.startswith("## "):
        close_block()
        if t[3:] not in ("The career in numbers", "The question"):  # keep the summary on the cover page
            story.append(PageBreak())   # every chapter starts on a new page
        story.append(Paragraph(inline(t[3:]), S["part"]))
        story.append(HRFlowable(width="100%", color=RULE, thickness=0.8, spaceAfter=6))
    elif t.startswith("### "):
        close_block()
        block = [Paragraph(inline(t[4:]), S["chart"])]
    elif t.startswith('> "'):                    # a quote from a player, with "<br>" before the attribution
        target.append(Paragraph(inline(t[2:]), S["quote"]))
    elif t.startswith("> "):
        target.append(Paragraph(inline(t[2:]), S["callout"]))
    elif t.startswith("!["):
        target.append(chart_image(re.search(r"\(([^)]+)\)", t).group(1)))
        target.append(Spacer(1, 6))
    elif t.startswith("**") and t.endswith("**") and story and len(story) == 1:
        story.append(Paragraph(inline(t), S["sub"]))
    elif t.startswith("*") and t.endswith("*") and not t.startswith("**"):
        target.append(Paragraph(inline(t), S["meta"]))
    else:
        target.append(Paragraph(inline(t), S["body"]))
close_block()

def footer(c, doc):
    c.saveState()
    c.setFillColor(BLUE); c.rect(0, A4[1] - 6, A4[0], 6, fill=1, stroke=0)
    c.setFont(BODY, 8); c.setFillColor(MUTED)
    c.drawString(20 * mm, 10 * mm, "Yaya Touré · Was he under-rated? · Hammad")
    c.drawRightString(A4[0] - 20 * mm, 10 * mm, str(doc.page))
    c.restoreState()

doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                        topMargin=18 * mm, bottomMargin=18 * mm,
                        title="Yaya Touré: was he under-rated?", author="Hammad")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("saved", OUT)
