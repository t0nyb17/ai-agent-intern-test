from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


BASE_DIR = Path(__file__).resolve().parent

FAISS_DIR = BASE_DIR / "storage" / "faiss"


def get_retriever():

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.load_local(
        str(FAISS_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore.as_retriever(
        search_kwargs={
            "k": 5
        }
    )


def search_knowledge_base(question):

    retriever = get_retriever()

    return retriever.invoke(
        question
    )