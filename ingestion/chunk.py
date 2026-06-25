from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(pages_data):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks_data = []
    for page in pages_data:
        chunks = splitter.split_text(page["text"])
        for chunk in chunks:
            chunks_data.append({
                "text": chunk,
                "page": page["page"],
                "section": page["section"],
                "source": page["source"]
            })

    return chunks_data