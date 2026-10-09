"""Build the name lexicon from the DEV split only (never from the test split).

Usage: python eval/build_lexicon.py
Output: perde/lexicon.txt  (one lower-case name per line, prefixed "G " given or "S " surname)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from perde.names import az_lower  # noqa: E402

DEV = ROOT / "data" / "localdoc_dev.jsonl"
OUT = ROOT / "perde" / "lexicon.txt"


def main() -> None:
    given, surnames = set(), set()
    for line in DEV.read_text(encoding="utf-8").splitlines():
        for lab in json.loads(line)["labels"]:
            v = lab["value"].strip()
            if " " in v or len(v) < 3 or not v[0].isalpha():
                continue
            if lab["label"] == "GIVENNAME":
                given.add(az_lower(v))
            elif lab["label"] == "SURNAME":
                surnames.add(az_lower(v))
    lines = [f"G {g}" for g in sorted(given)] + [f"S {s}" for s in sorted(surnames)]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(given)} given names, {len(surnames)} surnames -> {OUT.name}")


if __name__ == "__main__":
    main()
