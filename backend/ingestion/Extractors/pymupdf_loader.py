import re

import fitz


def load_pdf_pages(pdf_path):
    doc = fitz.open(pdf_path)

    pages_data = []
    current_section = "Introduction"

    for i, page in enumerate(doc):
        page_num = i + 1
        lines = page.get_text().split("\n")
        current_chunk_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if re.match(r"^(Chapter \d+:\s*.+|\d+\.\d+\s*.+)$", stripped):
                if current_chunk_lines:
                    pages_data.append({
                        "text": "\n".join(current_chunk_lines),
                        "page": page_num,
                        "section": current_section,
                        "source": pdf_path
                    })
                    current_chunk_lines = []
                current_section = stripped

            current_chunk_lines.append(line)

        if current_chunk_lines:
            pages_data.append({
                "text": "\n".join(current_chunk_lines),
                "page": page_num,
                "section": current_section,
                "source": pdf_path
            })

    return pages_data
