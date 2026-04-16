import json
from collections import Counter

with open("/home/dino/praksa/mdnscraper/output/mdn_dataset_20260409_122603.jsonl") as f:
    docs = [json.loads(line) for line in f]

print(f"Ukupno dokumenata: {len(docs)}")
print(f"Sekcije: {Counter(d['section'] for d in docs)}")
print(f"Prosječna duljina teksta: {sum(len(d['content']) for d in docs) // len(docs)} znakova")
print(f"\n--- Primjer dokumenta ---")
sample = docs[0]
print(f"URL: {sample['url']}")
print(f"Naslov: {sample['title']}")
print(f"Sadržaj:\n{sample['content'][:500]}")