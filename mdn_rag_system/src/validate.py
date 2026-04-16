import json
import os
import time

from src.rag_chain import create_rag_chain, ask
from src.config import QA_PAIRS_PATH

def load_qa_pairs(path:str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    

def run_validation():
    print("=" * 60)
    print("MDN RAG - Validacija sustava")
    print("=" * 60)

    qa_pairs = load_qa_pairs(QA_PAIRS_PATH)
    print(f"Učitano {len(qa_pairs)} Q&A parova\n")

    print("Inicijalizacija Rag chain...")
    chain = create_rag_chain()
    print("Rag chain spreman\n")

    results = []

    for i, qa in enumerate(qa_pairs, 1):
        print(f"\n{'=' * 60}")
        print(f"Pitanje {i}/{len(qa_pairs)}")
        print(f"{'=' * 60}")
        print(f"Pitanje:\n{qa['question']}\n")


        start = time.time()
        response = ask(chain, qa["question"])
        elapsed = time.time() - start

        print(f"RAG ODGOVOR ({elapsed:.1f}s):\n{response['answer']}\n")
        print(f"OČEKIVANI ODGOVOR:\n{qa['answer']}\n")

        if response["sources"]:
            print("IZVORI:")
            for src in response["sources"]:
                print(f"    -  {src['title']}: {src['url']}")
        
        print(f"\nOcijeni odgovor (1 = Loš, 3 = Djelomičan, 5 = Odličan)", end="")
        try:
            score = max(1, min(5, int(input().strip())))
        except ValueError:
            score = 3

        results.append({
            "question": qa["question"],
            "expected": qa["answer"],
            "got": response["answer"],
            "sources": response["sources"],
            "score": score,
            "response_time": elapsed
        })

    _print_report(results)

    os.makedirs("output", exist_ok=True)
    out = "output/validation_results.json"
    with open(out, "w", encoding = 'utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent = 2)
    print(f"\nRezultati spremljeni u {out}")


def _print_report(results: list[dict]):
    scores = [r["score"] for r in results]
    times = [r["response_time"] for r in results]

    avg_score = sum(scores) / len(scores)
    avg_time = sum(times) / len(times)
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for s in scores:
        dist[s] += 1

    print(f"\n{'='*60}")
    print("IZVJEŠTAJ VALIDACIJE")
    print(f"{'='*60}")
    print(f"Ukupno pitanja:    {len(results)}")
    print(f"Prosječna ocjena:  {avg_score:.2f}/5.00")
    print(f"Prosječno vrijeme: {avg_time:.1f}s po pitanju")
    print(f"\nDistribucija ocjena:")

    for score, count in dist.items():
        print(f" {score}/5: {"+" * count} ({count})")

    print("\interpretacija")
    if avg_score >= 4.0:
        print("Rezultat odličan!")
    elif avg_score >= 3.0:
        print("Rezultat OK")
    else:
        print("Rezultat loš")