import os
from dotenv import load_dotenv


load_dotenv()

DATASET_PATH = os.getenv(
    "DATASET_PATH",
    "/home/dino/Desktop/mdn-rag/output/mdn_dataset_20260416_204418.jsonl"
)

QA_PAIRS_PATH = os.getenv(
    "QA_PAIRS_PATH",
    "/home/dino/praksa/mdnscraper/output/qa_pairs.json"
)

#PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "mdn_rag")
DB_USER = os.getenv("DB_USER", "rag_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "rag_password")


CONNECTION_STRING = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

EMBEDDING_DIMENSION = 384

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

LLM_MODEL = "llama3.2"

RETRIEVER_K = 5