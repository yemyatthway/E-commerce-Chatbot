import os
import textwrap
from datetime import date


OUTPUT_PDF = "Ecommerce_Chatbot.pdf"
PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT = 48
TOP = 790
BOTTOM = 52


SOURCE_FILES = [
    "README.md",
    "chatbot_engine.py",
    "chatbot_features.py",
    "product_catalog.py",
    "analytics.py",
    "category_predictor.py",
    "evaluation.py",
    "app.py",
    "chat.py",
    "db.py",
    "train.py",
    "model.py",
    "nltk_utils.py",
    "intents.json",
    "products.csv",
    "orders.csv",
    "evaluation_survey.csv",
    "requirements.txt",
]


def escape_pdf_text(text):
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


class PdfDocument:
    def __init__(self):
        self.pages = []
        self.current = []
        self.y = TOP

    def new_page(self):
        if self.current:
            self.pages.append(self.current)
        self.current = []
        self.y = TOP

    def ensure_space(self, line_height):
        if self.y - line_height < BOTTOM:
            self.new_page()

    def add_line(self, text="", font="F1", size=10, x=LEFT, line_height=13):
        self.ensure_space(line_height)
        self.current.append((font, size, x, self.y, text))
        self.y -= line_height

    def add_heading(self, text):
        if self.y < TOP - 20:
            self.y -= 6
        self.add_line(text, font="F1", size=16, line_height=22)
        self.y -= 2

    def add_subheading(self, text):
        self.y -= 4
        self.add_line(text, font="F1", size=13, line_height=18)

    def add_paragraph(self, text, width=92):
        for line in textwrap.wrap(text, width=width) or [""]:
            self.add_line(line, font="F1", size=10, line_height=14)
        self.y -= 4

    def add_bullets(self, items, width=88):
        for item in items:
            wrapped = textwrap.wrap(item, width=width)
            if not wrapped:
                self.add_line("-")
                continue
            self.add_line(f"- {wrapped[0]}", font="F1", size=10, line_height=14)
            for line in wrapped[1:]:
                self.add_line(f"  {line}", font="F1", size=10, line_height=14)
        self.y -= 4

    def add_code_block(self, text, width=96):
        for raw_line in text.splitlines():
            line = raw_line.replace("\t", "    ")
            wrapped = textwrap.wrap(
                line,
                width=width,
                replace_whitespace=False,
                drop_whitespace=False,
            )
            if not wrapped:
                self.add_line("", font="F2", size=7, line_height=9)
            for part in wrapped:
                self.add_line(part, font="F2", size=7, line_height=9)
        self.y -= 6

    def finish(self):
        if self.current:
            self.pages.append(self.current)


def build_report(doc):
    doc.add_line("E-commerce Chatbot Source Code", font="F1", size=22, line_height=30)
    doc.add_line(f"Generated {date.today().isoformat()}", size=11)
    doc.y -= 18
    doc.add_heading("Included Files")
    for path in SOURCE_FILES:
        if os.path.exists(path):
            doc.add_line(path, font="F2", size=9, line_height=12)


def add_sources(doc):
    for path in SOURCE_FILES:
        if not os.path.exists(path):
            continue
        doc.new_page()
        doc.add_heading(path)
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            doc.add_code_block(file.read())


def write_pdf(doc, output_path):
    doc.finish()
    objects = []

    def add_object(content):
        objects.append(content)
        return len(objects)

    catalog_id = add_object("")
    pages_id = add_object("")
    font_helvetica_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_courier_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_ids = []
    for page in doc.pages:
        lines = []
        for font, size, x, y, text in page:
            lines.append(
                f"BT /{font} {size} Tf {x} {y} Td ({escape_pdf_text(text)}) Tj ET"
            )
        stream = "\n".join(lines)
        stream_obj = (
            f"<< /Length {len(stream.encode('utf-8'))} >>\n"
            f"stream\n{stream}\nendstream"
        )
        stream_id = add_object(stream_obj)
        page_obj = (
            f"<< /Type /Page /Parent {pages_id} 0 R "
            f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_helvetica_id} 0 R "
            f"/F2 {font_courier_id} 0 R >> >> "
            f"/Contents {stream_id} 0 R >>"
        )
        page_ids.append(add_object(page_obj))

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>"
    objects[pages_id - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, content in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n{content}\nendobj\n".encode("utf-8"))

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("utf-8"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("utf-8"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("utf-8")
    )

    with open(output_path, "wb") as file:
        file.write(pdf)


def main():
    doc = PdfDocument()
    build_report(doc)
    add_sources(doc)
    write_pdf(doc, OUTPUT_PDF)
    print(f"Updated {OUTPUT_PDF} with {len(doc.pages)} pages.")


if __name__ == "__main__":
    main()
