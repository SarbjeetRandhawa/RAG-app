import re

def clean_text(pages_data):

    for page in pages_data:
        text = page["text"]
        text = re.sub(r"\s+", " ", text)
        page["text"] = text.strip()

    return pages_data
