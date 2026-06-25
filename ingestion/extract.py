import fitz

def extract_text(pdf_path):

    doc = fitz.open(pdf_path)

    pages_data = []

    for i, page in enumerate(doc):
        pages_data.append({
            "text": page.get_text(),
            "page": i + 1,
            "source": pdf_path
        })

    return pages_data