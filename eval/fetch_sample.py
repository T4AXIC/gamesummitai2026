"""Download fixed, reproducible, non-overlapping splits of LocalDoc/pii_ner_azerbaijani (CC BY 4.0).

Usage: python eval/fetch_sample.py
Output:
  data/localdoc_test.jsonl  1,000 rows, used only for reported results
  data/localdoc_dev.jsonl   2,000 rows, used for tuning and to build the name lexicon
"""
from __future__ import annotations

import json
import random
import urllib.request
from pathlib import Path

API = "https://datasets-server.huggingface.co/rows?dataset=LocalDoc/pii_ner_azerbaijani&config=default&split=train&offset={offset}&length=100"
TOTAL_ROWS = 120_634
SEED = 2026
DATA = Path(__file__).resolve().parents[1] / "data"


def write(offsets: list[int], path: Path) -> None:
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for off in sorted(offsets):
            with urllib.request.urlopen(API.format(offset=off), timeout=60) as r:
                rows = json.load(r)["rows"]
            for row in rows:
                d = row["row"]
                f.write(json.dumps({
                    "uid": d["uid"],
                    "text": d["translated_text"],
                    "labels": json.loads(d["privacy_mask"]),
                }, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {n} rows to {path.name}")


def main() -> None:
    rng = random.Random(SEED)
    pages = rng.sample(range(0, TOTAL_ROWS - 100, 100), 30)  # 30 distinct pages, no overlap
    DATA.mkdir(exist_ok=True)
    write(pages[:10], DATA / "localdoc_test.jsonl")
    write(pages[10:], DATA / "localdoc_dev.jsonl")


if __name__ == "__main__":
    main()
