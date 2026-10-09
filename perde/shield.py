"""Mask personal data, send only masked text out, restore the answer locally."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .recognizers import ALL_ENTITIES, Span, detect_names, detect_patterns

# Higher wins when two detections overlap.
PRIORITY = {
    "EMAIL": 12, "IBAN": 11, "ID_CARD": 10, "PASSPORT": 10, "CARD": 9, "PHONE": 8,
    "VOEN": 7, "FIN": 6, "DRIVER_LICENSE": 6, "ADDRESS": 5, "PERSON": 4, "CAR_PLATE": 3, "DATE": 2,
}

TAG_RE = re.compile(r"\[\s*([A-Z_]+?)_(\d+)\s*\]", re.IGNORECASE)


@dataclass
class MaskResult:
    original: str
    masked: str
    spans: list[Span]
    mapping: dict[str, str] = field(default_factory=dict)  # tag -> original value

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for s in self.spans:
            out[s.entity] = out.get(s.entity, 0) + 1
        return out


def detect(text: str, entities: tuple[str, ...] = ALL_ENTITIES, min_score: float = 0.5) -> list[Span]:
    """Run all detectors and keep one non-overlapping span per region."""
    candidates = [
        s for s in detect_patterns(text) + detect_names(text)
        if s.entity in entities and s.score >= min_score
    ]
    candidates.sort(key=lambda s: (-PRIORITY.get(s.entity, 0), -s.score, -(s.end - s.start)))
    chosen: list[Span] = []
    for c in candidates:
        if all(c.end <= k.start or c.start >= k.end for k in chosen):
            chosen.append(c)
    return sorted(chosen, key=lambda s: s.start)


def mask(text: str, entities: tuple[str, ...] = ALL_ENTITIES, min_score: float = 0.5) -> MaskResult:
    spans = detect(text, entities, min_score)
    value_to_tag: dict[tuple[str, str], str] = {}
    counters: dict[str, int] = {}
    parts: list[str] = []
    cursor = 0
    for s in spans:
        key = (s.entity, _normalize(s.text))
        tag = value_to_tag.get(key)
        if tag is None:
            counters[s.entity] = counters.get(s.entity, 0) + 1
            tag = f"[{s.entity}_{counters[s.entity]}]"
            value_to_tag[key] = tag
        parts.append(text[cursor:s.start])
        parts.append(tag)
        cursor = s.end
    parts.append(text[cursor:])
    result = MaskResult(text, "".join(parts), spans)
    seen: set[str] = set()
    for s in spans:
        tag = value_to_tag[(s.entity, _normalize(s.text))]
        if tag not in seen:
            result.mapping[tag] = s.text
            seen.add(tag)
    return result


def restore(answer: str, mapping: dict[str, str]) -> str:
    """Put original values back. Tolerates case and spacing changes made by the model."""
    lookup = {k.upper(): v for k, v in mapping.items()}

    def sub(m: re.Match) -> str:
        tag = f"[{m.group(1).upper()}_{m.group(2)}]"
        return lookup.get(tag, m.group(0))

    return TAG_RE.sub(sub, answer)


def leaked_values(outgoing: str, mapping: dict[str, str]) -> list[str]:
    """Return original values that still appear in text about to leave the machine."""
    out_norm = _normalize(outgoing)
    # digits of each separate number in the outgoing text, so unrelated numbers never join up
    out_numbers = [re.sub(r"\D", "", n) for n in re.findall(r"\+?\d[\d\s\-().]*\d", outgoing)]
    leaks = []
    for value in mapping.values():
        v = _normalize(value)
        digits = re.sub(r"\D", "", value)
        # Compare the last 9 digits so "+994 55..." and "055..." count as the same number.
        core = digits[-9:]
        if v and re.search(rf"(?<!\w){re.escape(v)}(?!\w)", out_norm):
            leaks.append(value)
        elif len(core) >= 7 and any(core in n for n in out_numbers):
            leaks.append(value)
    return leaks


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()
