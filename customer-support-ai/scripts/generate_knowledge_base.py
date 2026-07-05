"""
Generate PDF knowledge base documents for TechMart Electronics.
Run: python scripts/generate_knowledge_base.py
"""
import os

# We use reportlab to create PDFs; falls back to writing .txt if not installed
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    USE_PDF = True
except ImportError:
    USE_PDF = False
    print("reportlab not installed — writing .txt files instead.")
    print("Install with: pip install reportlab")

KB_DIR = "knowledge_base"
os.makedirs(KB_DIR, exist_ok=True)


def read_document(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as file:
        return file.read()


DOCUMENTS = {
    "FAQ.txt": read_document("knowledge_base/FAQ.txt"),
    "RefundPolicy.txt": read_document("knowledge_base/RefundPolicy.txt"),
    "Pricing.txt": read_document("knowledge_base/Pricing.txt"),
    "UserManual.txt": read_document("knowledge_base/UserManual.txt"),
    "Warranty.txt": read_document("knowledge_base/Warranty.txt"),
}


def write_pdf(filename: str, content: str):
    path = os.path.join(KB_DIR, filename.replace(".txt", ".pdf"))
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=inch, bottomMargin=inch)
    story = []
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    body_style  = ParagraphStyle("body",  parent=styles["Normal"],   fontSize=10, leading=14)

    for line in content.strip().split("\n"):
        if line.startswith("===") or line.startswith("---"):
            story.append(Spacer(1, 4))
        elif line.isupper() and len(line) > 3:
            story.append(Paragraph(line, title_style))
        elif line.strip():
            story.append(Paragraph(line.replace("&", "&amp;"), body_style))
        else:
            story.append(Spacer(1, 8))

    doc.build(story)
    print(f"✅ Created {path}")


def write_txt(filename: str, content: str):
    path = os.path.join(KB_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Created {path}")


if __name__ == "__main__":
    for fname, content in DOCUMENTS.items():
        if not content:
            print(f"⚠️  Skipping {fname} — file not found.")
            continue
        if USE_PDF:
            write_pdf(fname, content)
        else:
            write_txt(fname, content)
    print("\nKnowledge base ready. Restart backend to re-index.")
