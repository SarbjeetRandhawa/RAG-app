import logging
import re
from collections import defaultdict

from ingestion.Extractors.pymupdf_loader import load_pdf_pages as load_pymupdf_pdf_pages


def _build_lightweight_pipeline_options():
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    pipeline_options = PdfPipelineOptions()

    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = False
    pipeline_options.do_picture_description = False
    pipeline_options.do_picture_classification = False
    pipeline_options.do_code_enrichment = False
    pipeline_options.do_formula_enrichment = False
    pipeline_options.do_chart_extraction = False

    pipeline_options.generate_page_images = False
    pipeline_options.generate_picture_images = False
    pipeline_options.generate_table_images = False
    pipeline_options.enable_remote_services = False

    return pipeline_options


def _is_heading(text):
    return bool(re.match(r"^(Chapter \d+:\s*.+|\d+\.\d+\s*.+)$", text.strip()))


def load_pdf_pages(pdf_path):
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pipeline_options = _build_lightweight_pipeline_options()
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    logging.info("Extracting PDF with Docling lightweight loader")
    result = converter.convert(pdf_path)
    document = result.document

    page_items = defaultdict(list)
    current_section = "Introduction"

    for item in document.texts:
        text = (getattr(item, "text", "") or "").strip()
        if not text:
            continue

        prov = getattr(item, "prov", None) or []
        page_no = prov[0].page_no if prov else 1

        if _is_heading(text):
            current_section = text

        page_items[page_no].append({
            "text": text,
            "section": current_section
        })

    pages_data = []
    for page_no in sorted(page_items):
        items = page_items[page_no]
        page_text = "\n".join(item["text"] for item in items)
        section = next(
            (item["section"] for item in reversed(items) if item["section"]),
            "Introduction"
        )
        pages_data.append({
            "text": page_text,
            "page": page_no,
            "section": section,
            "source": pdf_path
        })

    expected_pages = set(range(1, document.num_pages() + 1))
    extracted_pages = {page["page"] for page in pages_data}
    missing_pages = expected_pages - extracted_pages

    if missing_pages:
        logging.warning(
            "Docling skipped %s pages; filling missing pages with PyMuPDF",
            len(missing_pages)
        )
        fallback_pages = [
            page
            for page in load_pymupdf_pdf_pages(pdf_path)
            if page["page"] in missing_pages
        ]
        pages_data.extend(fallback_pages)
        pages_data.sort(key=lambda page: page["page"])

    return pages_data
