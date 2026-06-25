import fitz
import re

def extract_text(pdf_path):

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

            # Check if this line is a heading (e.g., Chapter 1: ... or 1.1 ...)
            if re.match(r"^(Chapter \d+:\s*.+|\d+\.\d+\s*.+)$", stripped):
                # Save previous accumulated lines under the previous section
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

        # Append any remaining lines of the page
        if current_chunk_lines:
            pages_data.append({
                "text": "\n".join(current_chunk_lines),
                "page": page_num,
                "section": current_section,
                "source": pdf_path
            })

    return pages_data