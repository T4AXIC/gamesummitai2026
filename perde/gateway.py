"""Provider-neutral AI gateway: mask, check for leaks, call the model, restore, log."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

from .shield import MaskResult, leaked_values, mask, restore

# Any OpenAI-compatible endpoint works. Model names change often, so set
# PERDE_MODEL to the one your account has.
PROVIDERS = {
    "openai": {"base_url": "https://api.openai.com/v1", "key_env": "OPENAI_API_KEY", "model": "gpt-4o-mini"},
    "grok": {"base_url": "https://api.x.ai/v1", "key_env": "XAI_API_KEY", "model": "grok-3-mini"},
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "model": "gemini-2.5-flash",
    },
    "ollama": {"base_url": "http://localhost:11434/v1", "key_env": None, "model": "gemma3"},
    "mock": {"base_url": None, "key_env": None, "model": "mock"},
}

SYSTEM_PROMPT = (
    "Some personal data in the user's text was replaced with tags such as [PERSON_1], "
    "[PHONE_1], [FIN_1]. Keep every tag exactly as written, including brackets and number. "
    "Never guess or invent the hidden values. Answer in the language of the user's text."
)

AUDIT_PATH = Path(os.environ.get("PERDE_AUDIT", Path(__file__).resolve().parents[1] / "audit_log.jsonl"))


class LeakBlocked(RuntimeError):
    pass


@dataclass
class GatewayResult:
    mask: MaskResult
    outgoing: str
    model_answer: str
    restored_answer: str
    provider: str
    model: str
    latency_ms: int


def _mock_answer(masked: str) -> str:
    """Offline stand-in for a model: writes a reply that uses the tags, as a real model would."""
    tags = list(dict.fromkeys(re.findall(r"\[[A-Z_]+_\d+\]", masked)))
    person = next((t for t in tags if t.startswith("[PERSON")), "müştəri")
    contact = [t for t in tags if t.startswith(("[PHONE", "[EMAIL"))]
    lines = [
        "[Offline demo model, no external API call]",
        f"Received {len(tags)} masked value(s); no real personal data.",
        "",
        f"Cavab layihəsi: Hörmətli {person}, müraciətiniz qeydə alındı və 1 iş günü ərzində baxılacaq.",
    ]
    if contact:
        lines.append(f"Nəticə barədə sizinlə {' / '.join(contact)} vasitəsilə əlaqə saxlayacağıq.")
    return "\n".join(lines)


def call_model(provider: str, prompt: str, model: str | None = None) -> tuple[str, str]:
    cfg = PROVIDERS[provider]
    model = model or os.environ.get("PERDE_MODEL") or cfg["model"]
    if provider == "mock":
        return _mock_answer(prompt), model
    from openai import OpenAI

    key = os.environ.get(cfg["key_env"]) if cfg["key_env"] else "ollama"
    if not key:
        raise RuntimeError(f"Set {cfg['key_env']} to use provider '{provider}'.")
    client = OpenAI(base_url=cfg["base_url"], api_key=key, timeout=60)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content or "", model


def run(text: str, task: str, provider: str = "mock", entities=None, model: str | None = None) -> GatewayResult:
    """Mask `text`, block if anything leaks, send task + masked text, restore the answer."""
    m = mask(text) if entities is None else mask(text, tuple(entities))
    outgoing = f"{task.strip()}\n\n---\n{m.masked}" if task.strip() else m.masked
    leaks = leaked_values(outgoing, m.mapping)
    if leaks:
        raise LeakBlocked(f"{len(leaks)} value(s) would leave unmasked; request blocked.")
    t0 = time.perf_counter()
    answer, used_model = call_model(provider, outgoing, model)
    latency = int((time.perf_counter() - t0) * 1000)
    restored = restore(answer, m.mapping)
    _audit(m, outgoing, provider, used_model, latency)
    return GatewayResult(m, outgoing, answer, restored, provider, used_model, latency)


def _audit(m: MaskResult, outgoing: str, provider: str, model: str, latency_ms: int) -> None:
    """Append-only log. Stores hashes and counts, never raw personal data."""
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "provider": provider,
        "model": model,
        "entities_masked": m.counts(),
        "input_sha256": hashlib.sha256(m.original.encode()).hexdigest(),
        "outgoing_sha256": hashlib.sha256(outgoing.encode()).hexdigest(),
        "leak_check": "passed",
        "latency_ms": latency_ms,
    }
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
