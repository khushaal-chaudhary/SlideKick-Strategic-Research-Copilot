"""Split document text into extraction chunks and vector chunks.

Mirrors the demo-corpus parameters (scripts/ingest_corpus.py) so BYOD
documents behave like the built-in shareholder letters.
"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

EXTRACTION_CHUNK_SIZE = 2000
EXTRACTION_CHUNK_OVERLAP = 200
VECTOR_CHUNK_SIZE = 1000
VECTOR_CHUNK_OVERLAP = 100

# Free-tier guardrail: caps LLM extraction calls per upload
MAX_EXTRACTION_CHUNKS = 60


class DocumentTooLargeError(ValueError):
    pass


def extraction_chunks(text: str, source: str) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=EXTRACTION_CHUNK_SIZE, chunk_overlap=EXTRACTION_CHUNK_OVERLAP
    )
    docs = splitter.split_documents([Document(page_content=text, metadata={"source": source})])
    if len(docs) > MAX_EXTRACTION_CHUNKS:
        raise DocumentTooLargeError(
            f"Document produces {len(docs)} extraction chunks; the demo caps uploads at "
            f"{MAX_EXTRACTION_CHUNKS} (~{MAX_EXTRACTION_CHUNKS * EXTRACTION_CHUNK_SIZE // 1000}k characters). "
            "Try a shorter document or an excerpt."
        )
    return docs


def vector_chunks(text: str, source: str) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=VECTOR_CHUNK_SIZE,
        chunk_overlap=VECTOR_CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents([Document(page_content=text, metadata={"source": source})])
