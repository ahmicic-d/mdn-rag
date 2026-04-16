import argparse
from src.ingest import run_ingestion
from src.rag_chain import create_rag_chain, ask
from src.validate import run_validation

def interactive_mode():
    print("\nMDN RAG Chat - upiši 'quit' za izlaz")
    chain = create_rag_chain()

    while True:
        question = input("Ti: ").strip()

        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        response = ask(chain, question)
        print(f"\nRAG: {response['answer']}")

        if response['sources']:
            print("\nIzvori: ")
            for src in response['sources']:
                print(f"  ->  {src['url']}")
        
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MDN RAG Sustav")
    parser.add_argument(
        "mode",
        choices=["ingest", "chat", "validate"],
        help = "ingest | chat | validate",
    )

    args = parser.parse_args()

    if args.mode == "ingest":
        run_ingestion()
    elif args.mode == "chat":
        interactive_mode()
    elif args.mode == "validate":
        run_validation()