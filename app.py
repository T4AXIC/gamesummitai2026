"""Pərdə web demo. Run: streamlit run app.py"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import streamlit as st

from perde.gateway import AUDIT_PATH, PROVIDERS, LeakBlocked, run
from perde.recognizers import ALL_ENTITIES
from perde.shield import leaked_values, mask

ROOT = Path(__file__).parent

COLORS = {
    "PERSON": "#f4a261", "FIN": "#e76f51", "ID_CARD": "#e76f51", "PASSPORT": "#e76f51",
    "DRIVER_LICENSE": "#e76f51", "VOEN": "#2a9d8f", "PHONE": "#8ab17d", "EMAIL": "#8ab17d",
    "IBAN": "#2a9d8f", "CARD": "#4ea8de", "ADDRESS": "#b5838d", "DATE": "#6d6875",
    "CAR_PLATE": "#6d6875",
}

SECTORS = {
    "Bank": {
        "entities": ALL_ENTITIES,
        "task": "Bu müştəri şikayətini 2 cümlə ilə xülasə et və cavab layihəsi yaz.",
        "sample": (
            "Salam, mən Nərmin Quliyeva. Dünən kartımdan 2 dəfə 150 AZN çıxılıb, kart 4111 1111 1111 1111. "
            "FIN kodum 6TR9K2L, hesabım AZ21NABZ00000000137010001944. "
            "Zəhmət olmasa 055 412 33 90 nömrəsinə zəng edin və ya nermin.q@mail.az ünvanına yazın."
        ),
    },
    "Telecom": {
        "entities": ALL_ENTITIES,
        "task": "Classify this ticket (billing / internet / tariff / other), set urgency, and draft a short reply.",
        "sample": (
            "Abonent Мамедов Эльчин жалуется: интернет не работает 3 дня. Номер 050 321 77 88, "
            "FIN kod 4PL8N3X, ünvan Azadlıq prospekti 33, mənzil 12. Хочет компенсацию за тариф."
        ),
    },
    "Government": {
        "entities": ALL_ENTITIES,
        "task": "Bu müraciəti emal et: nə tələb olunur, hansı sənədlər çatışmır, növbəti addım nədir?",
        "sample": (
            "Müraciətçi: Şahin Novruzov Elman oğlu, doğum tarixi 21.06.1985, şəxsiyyət vəsiqəsi AA7712093, "
            "FİN 9KM4T7R. Ünvan: Sumqayıt, Sülh küçəsi 12. Tel: +994 70 900 11 22. "
            "Şirkətin VÖEN-i 1503947221. Avtomobil 90-JK-412 üçün texniki baxış vaxtı istəyir."
        ),
    },
    "Custom": {"entities": ALL_ENTITIES, "task": "Summarize this text.", "sample": ""},
}


def highlight(text: str, spans) -> str:
    out, cur = [], 0
    for s in spans:
        out.append(html.escape(text[cur:s.start]))
        c = COLORS.get(s.entity, "#999")
        out.append(
            f'<span style="background:{c}33;border-bottom:2px solid {c};padding:1px 3px;border-radius:3px" '
            f'title="{s.entity} · {s.detector} · {s.score:.2f}">{html.escape(text[s.start:s.end])}'
            f'<sup style="color:{c};font-weight:600;font-size:0.65em"> {s.entity}</sup></span>'
        )
        cur = s.end
    out.append(html.escape(text[cur:]))
    return "".join(out).replace("\n", "<br>")


def tagged(text: str) -> str:
    esc = html.escape(text)
    return re.sub(
        r"\[([A-Z_]+)_(\d+)\]",
        lambda m: f'<code style="background:{COLORS.get(m.group(1), "#999")}22;color:{COLORS.get(m.group(1), "#555")}">[{m.group(1)}_{m.group(2)}]</code>',
        esc,
    ).replace("\n", "<br>")


def box(content: str) -> None:
    st.markdown(
        f'<div style="border:1px solid #8884;border-radius:8px;padding:12px;min-height:180px;line-height:1.7">{content}</div>',
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Pərdə · Safe AI for Azerbaijani data", page_icon="🛡️", layout="wide")

with st.sidebar:
    st.header("Settings")
    sector = st.selectbox("Sector", list(SECTORS), help="Loads a sample text and a typical task.")
    in_browser = sys.platform == "emscripten"  # static web build (stlite / Pyodide)
    providers = ["mock"] if in_browser else list(PROVIDERS)
    provider = st.selectbox(
        "AI provider", providers, index=providers.index("mock"),
        help="Any OpenAI-compatible API. 'mock' runs offline. Keys come from environment variables.",
    )
    if in_browser:
        st.info(
            "Web demo: runs entirely in your browser with the offline model. "
            "To use OpenAI, Grok, Gemini or Ollama, run the app locally (run.bat) or with Docker."
        )
    model = st.text_input("Model (optional)", value="", placeholder=PROVIDERS[provider]["model"])
    enabled = st.multiselect("Data types to protect", ALL_ENTITIES, default=list(SECTORS[sector]["entities"]))
    st.caption("Personal data is masked on this machine. Only tags like [PERSON_1] reach the AI provider.")

st.title("🛡️ Pərdə")
st.markdown(
    "**Use ChatGPT, Grok, Gemini or a local model on Azerbaijani customer data — without sending the personal data.** "
    "Names, FIN, ID cards, VÖEN, IBAN, cards and +994 numbers are replaced with tags before the request leaves, "
    "then put back into the answer locally."
)

tab_demo, tab_evidence, tab_audit = st.tabs(["Demo", "Evidence", "Audit log"])

with tab_demo:
    cfg = SECTORS[sector]
    text = st.text_area("Customer text (AZ / RU / EN)", value=cfg["sample"], height=130, key=f"text_{sector}")
    task = st.text_input("Instruction for the AI", value=cfg["task"], key=f"task_{sector}")
    go = st.button("Protect and send", type="primary")

    preview = mask(text, tuple(enabled))
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("##### 1 · Detected on your side")
        box(highlight(text, preview.spans) or "<i>Paste text above</i>")
    with c2:
        st.markdown("##### 2 · What the AI provider sees")
        box(tagged(preview.masked) or "<i>—</i>")
    with c3:
        st.markdown("##### 3 · Answer, restored locally")
        if go and text.strip():
            try:
                with st.spinner("Calling model…"):
                    res = run(text, task, provider, enabled, model or None)
                box(html.escape(res.restored_answer).replace("\n", "<br>"))
                st.session_state["last"] = res
            except LeakBlocked as e:
                st.error(f"Blocked: {e}")
            except Exception as e:  # provider/network errors shown, never swallowed
                st.error(f"{type(e).__name__}: {e}")
        else:
            box("<i>Press “Protect and send”.</i>")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Personal values masked", len(preview.spans))
    m2.metric("Data types found", len(preview.counts()))
    m3.metric("Leak check", "passed" if not leaked_values(preview.masked, preview.mapping) else "BLOCKED")
    last = st.session_state.get("last")
    m4.metric("Model latency", f"{last.latency_ms} ms" if last else "—")

    with st.expander("Raw model output (still masked)"):
        if last:
            st.code(last.model_answer)
    with st.expander("Mapping kept on this machine"):
        st.json(preview.mapping)

with tab_evidence:
    st.markdown(
        "Measured on **1,000 held-out texts** from the public "
        "[LocalDoc/pii_ner_azerbaijani](https://huggingface.co/datasets/LocalDoc/pii_ner_azerbaijani) "
        "dataset (CC BY 4.0) and on 20 hand-written messy AZ/RU/EN cases. "
        "The test split was never used for tuning. Reproduce with `python eval/evaluate.py`."
    )
    res_path = ROOT / "eval" / "results.json"
    if res_path.exists():
        results = json.loads(res_path.read_text(encoding="utf-8"))
        for dname, systems in results.items():
            st.subheader(dname)
            rows = [
                {"System": s, "Protected": f"{v['ALL']['protected']:.1%}",
                 "Leak rate": f"{1 - v['ALL']['protected']:.1%}", "Precision": f"{v['ALL']['precision']:.1%}"}
                for s, v in systems.items()
            ]
            st.table(rows)
    else:
        st.info("Run `python eval/evaluate.py` to produce results.")
    st.markdown("See **TESTING.md** for failures and limitations.")

with tab_audit:
    st.caption("Append-only log. Stores counts and SHA-256 hashes, never raw personal data.")
    if AUDIT_PATH.exists():
        recs = [json.loads(l) for l in AUDIT_PATH.read_text(encoding="utf-8").splitlines()[-20:]]
        st.dataframe(list(reversed(recs)), use_container_width=True)
    else:
        st.info("No requests yet.")
