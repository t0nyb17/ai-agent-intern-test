from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


ROOT = Path(__file__).resolve().parent

KB = ROOT / "knowledge-base"
DB = ROOT / "storage" / "chroma"


documents = []

for path in KB.glob("*.md"):

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp1252", errors="replace")

    documents.append(
        Document(
            page_content=text,
            metadata={
                "source": path.name
            }
        )
    )


splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

chunks = splitter.split_documents(documents)


embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)


Chroma.from_documents(
    chunks,
    embeddings,
    persist_directory=str(DB),
    collection_name="aster_row"
)

print(f"Indexed {len(chunks)} chunks.")