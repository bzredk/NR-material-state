"""Render the one-page English card; no data or device access."""
from pathlib import Path
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parent
def fmt(s):
    s=s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    s=re.sub(r"\*\*(.+?)\*\*",r"<b>\1</b>",s)
    s=re.sub(r"`(.+?)`",r'<font name="Courier">\1</font>',s)
    return s

if __name__=="__main__":
    styles={
        "title":ParagraphStyle("title",fontName="Helvetica-Bold",fontSize=17,leading=19,spaceAfter=6,textColor=colors.HexColor("#16354B")),
        "head":ParagraphStyle("head",fontName="Helvetica-Bold",fontSize=10.5,leading=12,spaceBefore=7,spaceAfter=3,textColor=colors.HexColor("#16354B")),
        "body":ParagraphStyle("body",fontName="Helvetica",fontSize=10,leading=12.4,spaceAfter=4),
    }
    blocks=(ROOT/"EXPERIMENTER_CARD_EN.md").read_text().split("\n\n")
    flow=[]
    for block in blocks:
        if block.startswith("# "):flow.append(Paragraph(fmt(block[2:].strip()),styles["title"]))
        elif block.startswith("## "):flow.append(Paragraph(fmt(block[3:].strip()),styles["head"]))
        else:
            # List entries remain separate paragraphs, without a dense wall of text.
            lines=block.strip().splitlines()
            if lines and (lines[0].startswith("- ") or re.match(r"\d+\. ",lines[0])):
                for line in lines:flow.append(Paragraph(fmt(line),styles["body"]))
            else:flow.append(Paragraph(fmt("<br/>".join(lines)).replace("&lt;br/&gt;","<br/>"),styles["body"]))
    out=ROOT/"EXPERIMENTER_CARD_EN.pdf"
    doc=SimpleDocTemplate(str(out),pagesize=letter,rightMargin=.48*inch,leftMargin=.48*inch,
                          topMargin=.42*inch,bottomMargin=.42*inch,
                          title="Recovery memory: first acquisition",author="NR Research")
    doc.build(flow)
    pages=len(PdfReader(out).pages)
    if pages!=1:raise RuntimeError(f"Execution card must be one page, got {pages}.")
    preview=ROOT/"verification";preview.mkdir(exist_ok=True)
    pdf=pdfium.PdfDocument(str(out))
    pdf[0].render(scale=2).to_pil().save(preview/"execution_card.png")
    print("One-page card generated and rendered.")
