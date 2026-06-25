from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(pages_data):

    full_text = " ".join(
        page["text"]
        for page in pages_data
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    return splitter.split_text(full_text)