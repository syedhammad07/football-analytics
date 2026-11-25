"""Turn docs/ARTICLE.md (every chart with its explanation) into reports/Christian_Eriksen_article.pdf

Design: Tottenham navy and white, Anton headlines and Lato text, a full cover page, numbered chapter openers,
key-number tiles and quote cards. Extra layout comes from HTML comments in the Markdown, which GitHub hides:
    <!-- cover-kpi: 109 | Goals + assists | most of any PL midfielder, 2013/14-2018/19 -->
    <!-- kpi: 17,132 | Minutes | most of any midfielder -->
"""
import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether, PageBreak,
                                ListFlowable, ListItem, Table, TableStyle, Flowable)

HERE = Path(__file__).parent
SRC = HERE.parent / "docs" / "ARTICLE.md"
OUT = HERE / "Christian_Eriksen_article.pdf"

# Tottenham Hotspur: navy and white
NAVY, NAVY_2, NAVY_3, NAVY_4 = HexColor("#132257"), HexColor("#1B2C66"), HexColor("#25387A"), HexColor("#3A4E95")
WHITE, MUTED, GOLD = HexColor("#FFFFFF"), HexColor("#B8C0D9"), HexColor("#C9A227")
W = A4[0] - 36 * mm   # text width

FONT_DIR = HERE.parent / "assets" / "fonts"   # Anton and Lato (SIL Open Font License)
for name, f in [("Lato", "Lato-Regular.ttf"), ("Lato-Bold", "Lato-Bold.ttf"), ("Lato-Italic", "Lato-Italic.ttf"),
                ("Lato-BoldItalic", "Lato-BoldItalic.ttf"), ("Lato-Black", "Lato-Black.ttf"), ("Anton", "Anton-Regular.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / f)))
addMapping("Lato", 0, 0, "Lato"); addMapping("Lato", 1, 0, "Lato-Bold")
addMapping("Lato", 0, 1, "Lato-Italic"); addMapping("Lato", 1, 1, "Lato-BoldItalic")

S = {
    "h": ParagraphStyle("h", fontName="Anton", fontSize=26, leading=31, textColor=WHITE, spaceAfter=4),
    "chap_title": ParagraphStyle("ct", fontName="Anton", fontSize=25, leading=29, textColor=WHITE),
    "chart": ParagraphStyle("chart", fontName="Lato-Bold", fontSize=12, leading=16, textColor=WHITE, spaceBefore=12, spaceAfter=6),
    "meta": ParagraphStyle("meta", fontName="Lato-Italic", fontSize=8.5, leading=12, textColor=MUTED, spaceAfter=12),
    "cell": ParagraphStyle("cell", fontName="Lato", fontSize=9, leading=12, textColor=WHITE),
    "callout": ParagraphStyle("callout", fontName="Lato", fontSize=10.5, leading=15.5, textColor=WHITE),
    "quote": ParagraphStyle("quote", fontName="Lato-Italic", fontSize=10.5, leading=14.5, textColor=WHITE),
    "who": ParagraphStyle("who", fontName="Lato", fontSize=8.5, leading=11.5, textColor=MUTED, spaceBefore=5),
    "body": ParagraphStyle("body", fontName="Lato", fontSize=10.5, leading=15.5, textColor=WHITE, spaceAfter=7, alignment=TA_LEFT),
    "kpi_n": ParagraphStyle("kn", fontName="Anton", fontSize=22, leading=25, textColor=WHITE, alignment=TA_LEFT),
    "kpi_l": ParagraphStyle("kl", fontName="Lato-Bold", fontSize=8.5, leading=10.5, textColor=WHITE),
    "kpi_s": ParagraphStyle("ks", fontName="Lato", fontSize=7.8, leading=10, textColor=MUTED),
}


def inline(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" color="#FFFFFF"><u>\1</u></a>', text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text.replace("&lt;br&gt;", "<br/>")


def chart_image(rel):
    path = (SRC.parent / rel.replace("/figures/", "/figures_dark/")).resolve()   # navy-background charts for the navy page
    w, h = PILImage.open(path).size
    s = min(W / w, 138 * mm / h)
    return Image(str(path), w * s, h * s)


def kpi_table(items, cover=False):
    """A row of key-number tiles: big number, label, small note."""
    cells = [[[Paragraph(n, S["kpi_n"]), Paragraph(l.upper(), S["kpi_l"]), Paragraph(s, S["kpi_s"])] for n, l, s in items]]
    t = Table(cells, colWidths=[W / len(items)] * len(items))
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY_2 if not cover else NAVY_3),
                           ("LINEABOVE", (0, 0), (-1, 0), 2.2, WHITE), ("LINEAFTER", (0, 0), (-2, -1), 3, NAVY),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return t


def callout(text):
    t = Table([[Paragraph(inline(text), S["callout"])]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY_3), ("LINEBEFORE", (0, 0), (0, -1), 4, WHITE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                           ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 11)]))
    return [Spacer(1, 4), t, Spacer(1, 12)]


def quote_cards(quotes):
    """Quotes as cards, two to a row, with a big opening quote mark."""
    cards = []
    for q in quotes:
        said, _, who = q.partition("<br>")
        cards.append([Paragraph('<font name="Anton" size="22" color="#8C9CC8">“</font>', S["quote"]),
                      Paragraph(inline(said.strip().strip('"')), S["quote"]),
                      Paragraph(inline(who.strip().lstrip("—").strip()), S["who"])])
    odd = len(cards) % 2
    if odd:
        cards.append("")
    rows = [cards[i:i + 2] for i in range(0, len(cards), 2)]
    t = Table(rows, colWidths=[W / 2] * 2)
    t.setStyle(TableStyle(([("SPAN", (0, len(rows) - 1), (1, len(rows) - 1))] if odd else []) + [("BACKGROUND", (0, 0), (-1, -1), NAVY_2), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LINEAFTER", (0, 0), (0, -1), 4, NAVY), ("LINEBELOW", (0, 0), (-1, -2), 4, NAVY),
                           ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    return [t, Spacer(1, 12)]


class ChapterOpener(Flowable):
    """Big outlined chapter number with the title beside it, and a white rule."""
    def __init__(self, num, title):
        super().__init__(); self.num, self.title = num, title
        self.p = Paragraph(inline(title), S["chap_title"])
        self.width, _ = W, 0
    def wrap(self, aw, ah):
        _, ph = self.p.wrap(W - 34 * mm, ah)
        self.height = max(ph, 24 * mm) + 8 * mm
        return W, self.height
    def draw(self):
        c = self.canv
        c.setFont("Lato-Bold", 8); c.setFillColor(MUTED)
        c.drawString(0, self.height - 3 * mm, "CHAPTER")
        c.setFont("Anton", 58); c.setFillColor(NAVY_4)
        c.drawString(-1.5, self.height - 24 * mm, f"{self.num:02d}")
        _, ph = self.p.wrap(W - 34 * mm, self.height)
        self.p.drawOn(c, 34 * mm, self.height - 6 * mm - ph - 4 * mm)
        c.setStrokeColor(WHITE); c.setLineWidth(1.4); c.line(0, 2 * mm, W, 2 * mm)


class Heading(Flowable):
    """Section heading for the non-chapter parts: Anton, with a short thick white bar above."""
    def __init__(self, title):
        super().__init__(); self.p = Paragraph(inline(title), S["h"])
    def wrap(self, aw, ah):
        _, ph = self.p.wrap(W, ah); self.height = ph + 8 * mm; return W, self.height
    def draw(self):
        c = self.canv; c.setFillColor(WHITE); c.rect(0, self.height - 1.6 * mm, 18 * mm, 1.6 * mm, fill=1, stroke=0)
        _, ph = self.p.wrap(W, self.height); self.p.drawOn(c, 0, self.height - 4 * mm - ph)


# ---------- parse ----------
lines = SRC.read_text(encoding="utf-8").splitlines()
COVER = {"title": "", "sub": "", "by": "", "kpis": []}
story, block, bullets, numbered, rows, quotes, kpis = [Spacer(1, 1), PageBreak()], None, [], [], [], [], []
section = ""


def flush():
    global bullets, numbered, rows, quotes, kpis
    tgt = block if block is not None else story
    if kpis:
        k, sp = kpi_table(kpis), Spacer(1, 12); k.keepWithNext = sp.keepWithNext = True
        tgt.extend([k, sp]); kpis = []
    if quotes:
        tgt.extend(quote_cards(quotes)); quotes = []
    if rows:
        cells = [[Paragraph(("<b>%s</b>" % inline(c)) if j == 0 else inline(c), S["cell"]) for j, c in enumerate(r)] for r in rows[1:]]
        t = Table(cells, colWidths=[W * 0.3, W * 0.7])
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, NAVY_4), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        tgt.extend([t, Spacer(1, 10)]); rows = []
    for items, kind in ((bullets, "bullet"), (numbered, "1")):
        if items:
            tgt.append(ListFlowable([ListItem(Paragraph(inline(x), S["body"]), leftIndent=16) for x in items],
                                    bulletType=kind, start="■" if kind == "bullet" else None, bulletFontName="Lato-Bold",
                                    bulletFontSize=7 if kind == "bullet" else 10, bulletColor=WHITE, leftIndent=16))
    bullets, numbered = [], []


def close_block():
    global block
    flush()
    if block:
        story.append(KeepTogether(block[:4])); story.extend(block[4:])
    block = None


for i, line in enumerate(lines):
    t = line.strip()
    m = re.match(r"<!--\s*(cover-kpi|kpi):(.*)-->", t)
    if m:
        parts = [p.strip() for p in m.group(2).split("|")]
        (COVER["kpis"] if m.group(1) == "cover-kpi" else kpis).append(parts); continue
    if not section:   # the cover: title, standfirst, byline
        if t.startswith("# "): COVER["title"] = t[2:]
        elif t.startswith("**"): COVER["sub"] = t.strip("*")
        elif t.startswith("*"): COVER["by"] = t.strip("*")
        if not t.startswith("## "): continue
    if t.startswith("|"):
        if not re.match(r"^\|[\s\-:|]+\|$", t): rows.append([c.strip() for c in t.strip("|").split("|")])
        continue
    if t.startswith("- "): bullets.append(t[2:]); continue
    if re.match(r"^\d+\. ", t): numbered.append(re.sub(r"^\d+\. ", "", t)); continue
    if t.startswith('> "'): quotes.append(t[2:]); continue
    if not t:
        continue
    flush()
    target = block if block is not None else story
    if t == "---":
        continue
    if t.startswith("## "):
        close_block(); section = t[3:]
        if section in ("Chapter 1 · Six and a half seasons",):
            story.append(PageBreak())
        elif section.startswith("Chapter") or section in ("Sources", "The verdict", "Method and data"):
            story.append(Spacer(1, 10))
        cm = re.match(r"Chapter (\d+) · (.+)", section)
        h = ChapterOpener(int(cm.group(1)), cm.group(2)) if cm else Heading(section)
        h.keepWithNext = True; story.append(h)
        sp = Spacer(1, 6); sp.keepWithNext = True; story.append(sp)
    elif t.startswith("### "):
        close_block(); block = [Paragraph(inline(t[4:]), S["chart"])]
    elif t.startswith("> "):
        target.extend(callout(t[2:]))
    elif t.startswith("!["):
        target.append(chart_image(re.search(r"\(([^)]+)\)", t).group(1))); target.append(Spacer(1, 5))
    elif t.startswith("*") and t.endswith("*") and not t.startswith("**"):
        cap = Paragraph(inline(t), S["meta"])
        if len(target) >= 2 and isinstance(target[-2], Image):
            sp = target.pop(); img = target.pop(); target.append(KeepTogether([img, sp, cap]))
        else:
            target.append(cap)
    else:
        target.append(Paragraph(inline(t), S["body"]))
close_block()


# ---------- pages ----------
def cover(c, doc):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    c.setFont("Anton", 430); c.setFillColor(NAVY_2); c.drawRightString(A4[0] + 14 * mm, 52 * mm, "23")   # his Spurs shirt number
    c.setFillColor(WHITE); c.rect(18 * mm, A4[1] - 30 * mm, 22 * mm, 2 * mm, fill=1, stroke=0)
    c.setFont("Lato-Bold", 9); c.setFillColor(MUTED)
    c.drawString(18 * mm, A4[1] - 38 * mm, "PLAYER REPORT  ·  TOTTENHAM HOTSPUR  ·  2013–2020")
    title = Paragraph(inline(COVER["title"]), ParagraphStyle("ct", fontName="Anton", fontSize=46, leading=52, textColor=WHITE))
    _, th = title.wrap(150 * mm, 200 * mm); title.drawOn(c, 18 * mm, A4[1] - 46 * mm - th)
    sub = Paragraph(inline(COVER["sub"]), ParagraphStyle("cs", fontName="Lato", fontSize=12.5, leading=18, textColor=WHITE))
    _, sh = sub.wrap(135 * mm, 100 * mm); sub.drawOn(c, 18 * mm, A4[1] - 54 * mm - th - sh)
    if COVER["kpis"]:
        k = kpi_table(COVER["kpis"][:4], cover=True); _, kh = k.wrap(W, 100 * mm); k.drawOn(c, 18 * mm, 40 * mm)
    by = Paragraph(inline(COVER["by"]), ParagraphStyle("cb", fontName="Lato", fontSize=8.5, leading=12, textColor=MUTED))
    _, bh = by.wrap(W, 40 * mm); by.drawOn(c, 18 * mm, 22 * mm)
    c.restoreState()


def page(c, doc):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    c.setFont("Lato-Bold", 7.5); c.setFillColor(MUTED)
    c.drawString(18 * mm, A4[1] - 11 * mm, "CHRISTIAN ERIKSEN  ·  THE MOST PRODUCTIVE MIDFIELDER NOBODY TALKS ABOUT?")
    c.drawRightString(A4[0] - 18 * mm, A4[1] - 11 * mm, "HAMMAD")
    c.setStrokeColor(NAVY_4); c.setLineWidth(0.6); c.line(18 * mm, A4[1] - 13.5 * mm, A4[0] - 18 * mm, A4[1] - 13.5 * mm)
    c.setFillColor(WHITE); c.rect(A4[0] - 30 * mm, 0, 12 * mm, 15 * mm, fill=1, stroke=0)
    c.setFont("Anton", 15); c.setFillColor(NAVY); c.drawCentredString(A4[0] - 24 * mm, 5 * mm, str(doc.page))
    c.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=20 * mm, bottomMargin=20 * mm,
                        title="Christian Eriksen: the most productive midfielder nobody talks about?", author="Hammad")
doc.build(story, onFirstPage=cover, onLaterPages=page)
print("saved", OUT)
