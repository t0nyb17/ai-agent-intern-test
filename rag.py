from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


ROOT = Path(__file__).resolve().parent
DB = ROOT / "storage" / "chroma"

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)


def search_knowledge_base(question, k=6):

    db = Chroma(
        persist_directory=str(DB),
        collection_name="aster_row",
        embedding_function=embeddings
    )

    documents = db.similarity_search(
        question,
        k=k
    )

    documents = [
        doc for doc in documents
        if "02-returns-policy-legacy.md"
        not in doc.metadata.get("source", "")
        and
        "14-internal-content-migration-notes.md"
        not in doc.metadata.get("source", "")
    ]

    return documents