from ingestion.Extractors.docling_loader import load_pdf_pages as load_docling_pdf_pages
from ingestion.Extractors.pymupdf_loader import load_pdf_pages as load_pymupdf_pdf_pages


def extract_text(pdf_path, loader="pymupdf"):
    loader = (loader or "pymupdf").lower()

    if loader in {"pymupdf", "fitz", "fast"}:
        return load_pymupdf_pdf_pages(pdf_path)

    if loader in {"docling", "structured"}:
        return load_docling_pdf_pages(pdf_path)

    raise ValueError(f"Unsupported PDF loader: {loader}")
