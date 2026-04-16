from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_ollama import OllamaLLM
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

from src.config import (
    CONNECTION_STRING, EMBEDDING_MODEL, LLM_MODEL, RETRIEVER_K
)

COLLECTION_NAME = "mdn_html_docs"

def create_rag_chain() -> RetrievalQA:
    
    embeddings = HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL,
        model_kwargs = {"device": "cuda"},
    )
    
    vectorstore = PGVector(
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        embeddings=embeddings
    )

    retriever = vectorstore.as_retriever(
        search_type = "similarity",
        search_kwargs = {"k": RETRIEVER_K}
    )

    llm = OllamaLLM(model = LLM_MODEL)

    prompt = PromptTemplate(
        template="""You are a helpful assistant specializing in web development documentation from MDN Web Docs.

                    Use ONLY the following context to answer the question.
                    If the answer is not in the context, say "I don't have enough information to answer this question."
                    Do not use any prior knowledge outside of the provided context.

                    Context:
                    {context}

                    Question: {question}

                    Answer:""",
        input_variables=["context", "question"],
    )

    chain = RetrievalQA.from_chain_type(
        llm = llm,
        chain_type = "stuff",
        retriever = retriever,
        return_source_documents = True,
        chain_type_kwargs = {"prompt": prompt}
    )
    return chain

def ask(chain: RetrievalQA, question: str) -> dict:
    result = chain.invoke({"query": question})

    sources = []
    for doc in result.get("source_documents", []):
        url = doc.metadata.get("url", "unknown")
        title = doc.metadata.get("title", "unknown")

        if url not in [s["url"] for s in sources]:
            sources.append({"url": url, "title": title})
    
    return {
        "question": question,
        "answer": result["result"],
        "sources": sources,
    }