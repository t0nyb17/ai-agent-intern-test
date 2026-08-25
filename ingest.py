from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent

KNOWLEDGE_BASE = BASE_DIR / "knowledge-base"
FAISS_DIR = BASE_DIR / "storage" / "faiss"


def create_embeddings():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )


def load_documents():

    documents = []

    for file in KNOWLEDGE_BASE.glob("*.md"):

        loader = TextLoader(
            str(file),
            encoding="utf-8"
        )

        documents.extend(
            loader.load()
        )

    return documents


def create_vector_database():

    print("Loading documents...")

    documents = load_documents()

    print(
        f"Loaded {len(documents)} documents."
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(
        documents
    )

    print(
        f"Created {len(chunks)} chunks."
    )

    embeddings = create_embeddings()

    vectorstore = FAISS.from_documents(
        chunks,
        embeddings
    )

    FAISS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    vectorstore.save_local(
        str(FAISS_DIR)
    )

    print("FAISS index created successfully.")


if __name__ == "__main__":
    create_vector_database()