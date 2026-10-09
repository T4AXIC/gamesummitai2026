"""Measure detection quality on the held-out LocalDoc split and on hand-written cases.

Usage: python eval/evaluate.py [--split test|dev] [--show-failures N]
Writes eval/results.json and prints a Markdown table.

Metrics, per entity group:
  recall      gold values masked by a detection of the right type (>=50% of characters)
  protected   gold values masked by any detection (>=90% of characters); 1 - protected = leak rate
  precision   detections that overlap any labelled personal value
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from perde.shield import detect  # noqa: E402

GOLD_GROUP = {
    "GIVENNAME": "PERSON", "SURNAME": "PERSON",
    "TELEPHONENUM": "PHONE", "EMAIL": "EMAIL",
    "IDCARDNUM": "ID_NUMBER", "PASSPORTNUM": "ID_NUMBER", "TAXNUM": "ID_NUMBER",
    "DRIVERLICENSENUM": "ID_NUMBER", "CREDITCARDNUMBER": "CARD",
    "DATE": "DATE", "STREET": "ADDRESS", "BUILDINGNUM": "ADDRESS",
}
OUT_OF_SCOPE = {"TIME", "CITY", "AGE", "ZIPCODE"}
PRED_GROUP = {
    "PERSON": "PERSON", "PHONE": "PHONE", "EMAIL": "EMAIL", "FIN": "ID_NUMBER",
    "ID_CARD": "ID_NUMBER", "PASSPORT": "ID_NUMBER", "VOEN": "ID_NUMBER",
    "IBAN": "ID_NUMBER", "DRIVER_LICENSE": "ID_NUMBER", "CAR_PLATE": "ID_NUMBER", "CARD": "CARD",
    "DATE": "DATE", "ADDRESS": "ADDRESS",
}
GROUPS = ["PERSON", "PHONE", "EMAIL", "ID_NUMBER", "CARD", "DATE", "ADDRESS"]


# --- systems under test -----------------------------------------------------

def system_perde(text):
    return [(s.start, s.end, PRED_GROUP[s.entity]) for s in detect(text)]


_GEN_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_GEN_PHONE = re.compile(r"(?<!\w)\+?\d[\d\s\-().]{7,}\d(?!\w)")
_GEN_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b")


def system_generic(text):
    """Language-agnostic regex baseline: what a default, non-localised filter catches."""
    out = [(m.start(), m.end(), "EMAIL") for m in _GEN_EMAIL.finditer(text)]
    out += [(m.start(), m.end(), "PHONE") for m in _GEN_PHONE.finditer(text)]
    out += [(m.start(), m.end(), "DATE") for m in _GEN_DATE.finditer(text)]
    return out


def system_no_names(text):
    return [p for p in system_perde(text) if p[2] != "PERSON"]


SYSTEMS = {"Pərdə": system_perde, "Pərdə without name detector": system_no_names,
           "Generic regex baseline": system_generic}


# --- scoring ----------------------------------------------------------------

def coverage(gs, ge, preds, group=None):
    covered = set()
    for ps, pe, pg in preds:
        if group is None or pg == group:
            covered.update(range(max(gs, ps), min(ge, pe)))
    span_chars = [i for i in range(gs, ge)]
    return len(covered) / max(1, len(span_chars))


def score(rows, system):
    stats = defaultdict(lambda: {"gold": 0, "typed": 0, "protected": 0, "pred": 0, "pred_ok": 0})
    failures = []
    for row in rows:
        text, labels = row["text"], row["labels"]
        preds = system(text)
        for lab in labels:
            g = GOLD_GROUP.get(lab["label"])
            if g is None:
                continue
            st = stats[g]
            st["gold"] += 1
            if coverage(lab["start"], lab["end"], preds, g) >= 0.5:
                st["typed"] += 1
            if coverage(lab["start"], lab["end"], preds) >= 0.9:
                st["protected"] += 1
            else:
                failures.append({"uid": row.get("uid"), "missed": lab["value"], "label": lab["label"], "text": text})
        for ps, pe, pg in preds:
            st = stats[pg]
            st["pred"] += 1
            if any(ps < l["end"] and pe > l["start"] for l in labels):
                st["pred_ok"] += 1
    return stats, failures


def summarize(stats):
    out = {}
    tot = {"gold": 0, "typed": 0, "protected": 0, "pred": 0, "pred_ok": 0}
    for g in GROUPS:
        st = stats.get(g, {"gold": 0, "typed": 0, "protected": 0, "pred": 0, "pred_ok": 0})
        for k in tot:
            tot[k] += st[k]
        out[g] = _ratios(st)
    out["ALL"] = _ratios(tot)
    return out


def _ratios(st):
    return {
        "n_gold": st["gold"],
        "recall": round(st["typed"] / st["gold"], 3) if st["gold"] else None,
        "protected": round(st["protected"] / st["gold"], 3) if st["gold"] else None,
        "precision": round(st["pred_ok"] / st["pred"], 3) if st["pred"] else None,
        "n_pred": st["pred"],
    }


def load_rows(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_handwritten(path):
    """Hand-written cases list values, not offsets; locate each value in the text."""
    rows = []
    for case in load_rows(path):
        labels = []
        for lab, value in case["pii"]:
            i = case["text"].find(value)
            assert i >= 0, (case["id"], value)
            labels.append({"label": lab, "start": i, "end": i + len(value), "value": value})
        rows.append({"uid": case["id"], "text": case["text"], "labels": labels})
    return rows


def fmt(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test", choices=["test", "dev"])
    ap.add_argument("--show-failures", type=int, default=0)
    args = ap.parse_args()

    datasets = {
        f"LocalDoc {args.split} (held-out)" if args.split == "test" else "LocalDoc dev": load_rows(ROOT / "data" / f"localdoc_{args.split}.jsonl"),
        "Hand-written AZ/RU/EN cases": load_handwritten(ROOT / "data" / "handwritten.jsonl"),
    }
    results = {}
    for dname, rows in datasets.items():
        results[dname] = {}
        print(f"\n### {dname} ({len(rows)} texts)\n")
        print("| System | Protected (all PII) | Leak rate | Precision |")
        print("|---|---|---|---|")
        for sname, fn in SYSTEMS.items():
            stats, failures = score(rows, fn)
            summ = summarize(stats)
            results[dname][sname] = summ
            a = summ["ALL"]
            print(f"| {sname} | {fmt(a['protected'])} | {fmt(1 - a['protected'])} | {fmt(a['precision'])} |")
            if sname == "Pərdə" and args.show_failures:
                for f in failures[: args.show_failures]:
                    print(f"  MISS {f['label']}: {f['missed']!r} :: {f['text'][:120]}")
        print(f"\nPer entity (Pərdə):\n")
        print("| Entity | Gold | Recall (right type) | Protected | Precision |")
        print("|---|---|---|---|---|")
        for g in GROUPS:
            s = results[dname]["Pərdə"][g]
            if s["n_gold"]:
                print(f"| {g} | {s['n_gold']} | {fmt(s['recall'])} | {fmt(s['protected'])} | {fmt(s['precision'])} |")
    (ROOT / "eval" / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
