# ocean-back/services/document_service.py
from docx import Document
from pptx import Presentation
from pptx.util import Inches
import io

class DocumentService:
    @staticmethod
    def generate_word(title: str, sections: list) -> bytes:
        doc = Document()
        # Title
        doc.add_heading(title, 0)
        for section in sections:
            doc.add_heading(section.get("title", ""), level=1)
            if section.get("content"):
                doc.add_paragraph(section["content"])
            doc.add_paragraph()
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_powerpoint(title: str, sections: list) -> bytes:
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)
        # Title slide
        title_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_layout)
        if slide.shapes.title:
            slide.shapes.title.text = title
        # Slides
        for section in sections:
            slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(slide_layout)
            title_shape = slide.shapes.title
            body = slide.placeholders[1].text_frame
            title_shape.text = section.get("title", "")
            if section.get("content"):
                content = section["content"].split("\n")
                for line in content:
                    line = line.strip()
                    if not line:
                        continue
                    p = body.add_paragraph()
                    p.text = line.lstrip("-•").strip()
                    p.level = 0
        buffer = io.BytesIO()
        prs.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

document_service = DocumentService()
