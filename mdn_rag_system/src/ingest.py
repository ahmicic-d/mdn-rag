import json
import time

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector

from src.config import(
    DATASET_PATH, CONNECTION_STRING, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
)

COLLECTION_NAME = "mdn_html_docs"

def load_jsonl(path: str) -> list[dict]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    print(f"Učitano {len(docs)} dokumenata iz {path}")
    return docs

def convert_to_langchain_docs(raw_docs: list[dict]) -> list[Document]:
    documents = []
    for doc in raw_docs:
        content = f"# {doc['title']}\n\n{doc['content']}"
        metadata = {
            "url": doc['url'],
            "title": doc["title"],
            "section": doc["section"],
            "breadcrumb": " > ".join(doc.get("breadcrumb", [])),
            "scraped_at": doc["scraped_at"],
        }
        documents.append(Document(page_content = content, metadata = metadata))
    print(f"Kreirano {len(documents)} Langchain dokumenata")
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = CHUNK_SIZE,
        chunk_overlap = CHUNK_OVERLAP,
        length_function = len,
        separators = ["\n\n", "\n", ", ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    avg = sum(len(c.page_content) for c in chunks) // len(chunks)
    print(f"Podijeljeno na {len(chunks)} chunkova (prosječno {avg} znakova)")
    return chunks


def create_embeddings() -> HuggingFaceEmbeddings:
    print(f"Učitavam embedding model: {EMBEDDING_MODEL}")
    print(f"(Pri prvom pokretanju preuzima ~90MB)")
    embeddings = HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL,
        model_kwargs = {"device": "cuda"},
    )
    print("Embedding model je učitan.")
    return embeddings

def ingest_tp_pgvector(chunks: list[Document], embeddings: HuggingFaceEmbeddings):
    print(f"\nSpremam {len(chunks)} chunkova u pgvector...")
    start = time.time()

    vectorstore = PGVector.from_documents(
        documents = chunks,
        embedding = embeddings,
        collection_name = COLLECTION_NAME,
        connection = CONNECTION_STRING,
        pre_delete_collection = True,
    )

    print(f"Gotovo. Trajalo je {time.time() - start:.1f} sekundi")
    return vectorstore

def run_ingestion():
    print("=" * 60)
    print("MDN RAG - Ingestion Pipeline")
    print("" * 60)
    raw_docs = load_jsonl(DATASET_PATH)
    lc_docs = convert_to_langchain_docs(raw_docs)
    chunks = split_documents(lc_docs)
    embeddings = create_embeddings()
    vectorstore = ingest_tp_pgvector(chunks, embeddings)

    print("\nIngestion izvršen")
