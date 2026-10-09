# Pərdə 🛡️ — use AI on Azerbaijani customer data without sending the personal data

> *Pərdə* means "curtain" in Azerbaijani.

**For** banks, telecom operators and government service centres in Azerbaijan, **who today** can't paste customer messages into ChatGPT, Grok or Gemini because the text contains names, FIN codes, ID cards, IBANs and phone numbers, **we built** a local privacy layer. It replaces that data with tags *before* the request leaves the organisation and puts the real values back into the AI's answer locally.

**Result on 1,000 held-out Azerbaijani texts: 94.9% of personal values protected vs 23.9% for a generic regex filter. Masking takes 0.14 ms per text, on CPU, offline.**

```
Customer text (stays inside)                     What the AI provider receives
──────────────────────────────                   ──────────────────────────────────────────
Salam, mən Nərmin Quliyeva. Kart                 Salam, mən [PERSON_1]. Kart [CARD_1].
4111 1111 1111 1111. FIN 6TR9K2L,        ──►     FIN [FIN_1], hesabım [IBAN_1].
hesabım AZ21NABZ00000000137010001944.            Tel [PHONE_1].
Tel 055 412 33 90.
                                                           │ AI answer, with tags kept
Hörmətli Nərmin Quliyeva, müraciətiniz   ◄──     Hörmətli [PERSON_1], müraciətiniz
qeydə alındı… 055 412 33 90                      qeydə alındı… [PHONE_1]
```

---

## 1. Value for the user

- **The user:** an operator who handles customer requests at a bank, a mobile operator, or a public service centre (complaints, applications, tickets).
- **Today:** these teams either don't use AI at all, or staff copy customer data into public chatbots. Neither is acceptable. Azerbaijan's Law on Personal Data (2010) restricts handing personal data to third parties.
- **With Pərdə:** the same staff use any AI model for summaries, replies, classification and translation. The provider only ever sees tags.
- **The metric that matters:** the **leak rate**, meaning the share of personal values that reach the AI provider. It falls from 76.1% with a generic filter to 5.1% with Pərdə (held-out test, details in [TESTING.md](TESTING.md)). A second, exact-match check then **blocks** any request where a detected value would still leave unmasked.

## 2. Prototype and use of AI

The working core scenario is to paste a customer text, pick a sector and a task, then press **Protect and send**. The screen shows three panels:

1. What was detected locally, highlighted by type
2. The exact text the AI provider receives
3. The provider's answer, with the real values restored

**Where AI does the work:** the external LLM (OpenAI, xAI Grok, Gemini, or a local Ollama model) does the actual task: summarising, drafting a reply in Azerbaijani or Russian, classifying the ticket. Pərdə is what makes it *permissible* to use that model on real data.

**Why detection is not an LLM:** sending text to an LLM to find the personal data would leak it to that LLM, which defeats the purpose. So detection is local, deterministic and auditable. It combines:
- validated patterns for Azerbaijani identifiers (FIN, ID card `AZE…`/`AA…`, passport, driver licence, VÖEN, AZ IBAN with a mod-97 checksum, card numbers with a Luhn check, +994 mobile and landline formats, car plates, dates)
- a name detector built for Azerbaijani: a name lexicon, surname morphology (`-ov/-ova`, `-li/-lı`, `-zadə`, `-oğlu`), patronymics (`oğlu`/`qızı`), stripping of Azerbaijani case endings (`Rənanın` → `[PERSON_1]nın`), and Cyrillic and ASCII spellings
- street patterns (`küçəsi`, `prospekti`, `ул.`) with house and flat numbers

**Other parts:**
- **Provider-neutral gateway:** any OpenAI-compatible API, switched by one setting ([perde/gateway.py](perde/gateway.py)).
- **Restore:** tags are restored even if the model changes their case or spacing (`[ phone_1 ]`).
- **Audit log:** an append-only JSONL file with counts and SHA-256 hashes only. It never stores raw personal data.

## 3. Quality testing

Full report with failures: **[TESTING.md](TESTING.md)**. Summary:

| Test set | Pərdə: protected | Generic regex baseline | Pərdə precision |
|---|---|---|---|
| LocalDoc Azerbaijani PII, **1,000 held-out texts** | **94.9%** | 23.9% | 93.0% |
| 20 hand-written messy AZ/RU/EN cases | 98.7% | 28.9% | 96.6% |

| Entity (held-out) | Values | Protected |
|---|---|---|
| Person names | 1,144 | 97.4% |
| Phone numbers | 184 | 100% |
| E-mail | 132 | 100% |
| ID numbers (FIN, ID card, passport, licence, VÖEN) | 165 | 100% |
| Card numbers | 25 | 100% |
| Addresses | 298 | 82.2% |
| Dates | 117 | 80.3% |

- The test split was fixed by seed and never used for tuning. The name lexicon was built from a separate 2,000-row dev split.
- Reproduce with `python eval/fetch_sample.py && python eval/evaluate.py`.
- There are 11 unit tests covering checksums, phone formats, tag consistency, restoration and the leak blocker (`pytest`).

## 4. Feasibility

- **Data needed:** none to start. It runs on rules and a lexicon, and each organisation can extend the lexicon and patterns.
- **Running cost:** masking is free, takes about 0.14 ms per message on one CPU core, and needs no GPU. The LLM cost is unchanged, because the masked text is the same length.
- **Deployment:** a Python package and a web UI. It runs on-premises, next to an existing API gateway, or as a proxy.
- **Next step (4 weeks):**
  1. Pilot on one support queue.
  2. Add a small Azerbaijani NER model as a second detector, run locally.
  3. Integrate the audit log with the organisation's SIEM.
  4. Measure leak rate and staff time per ticket against the current process.

## 5. Originality

Generic PII filters are built for English. Azerbaijani personal data has its own formats (FIN, VÖEN, AZ IBAN, `+994`) and its own grammar: names take case endings, patronymics use `oğlu`/`qızı`, and texts mix Latin, Cyrillic and ASCII spelling. Pərdə is built specifically for that, and it reports its own leak rate on a public Azerbaijani benchmark.

---

## Run it

**Live demo (no install, runs in your browser):** https://huggingface.co/spaces/Traxic/perde

**Windows, one click:** download the v1.0 release zip, unzip it and double-click `run.bat`. It needs Python 3.10 or newer. The first run installs the dependencies, then the app opens at http://localhost:8501.

**Docker (any OS, suits on-premises servers):**

```bash
docker build -t perde .
docker run -p 8501:8501 perde
```

**Manual:**

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt   # Windows; use .venv/bin/pip on Linux/macOS
.venv/Scripts/streamlit run app.py
```

- The default provider is **mock**, which works offline with no key.
- For a real model, set one of `OPENAI_API_KEY`, `XAI_API_KEY` (Grok) or `GEMINI_API_KEY`, or run Ollama locally. Then pick the provider in the sidebar. Optionally set `PERDE_MODEL`.
- Use it in code:

```python
from perde.gateway import run
res = run("Salam, mən Rəşad Həsənov, FIN 7XK2M9P…", "Cavab layihəsi yaz", provider="grok")
print(res.outgoing)          # what left the machine
print(res.restored_answer)   # answer with real values
```

## Project layout

| Path | What it is |
|---|---|
| `perde/recognizers.py` | Azerbaijani identifier patterns and the name detector |
| `perde/shield.py` | Masking, overlap resolution, restoration, leak check |
| `perde/gateway.py` | Provider-neutral LLM call, leak blocking, audit log |
| `app.py` | Streamlit demo (Demo / Evidence / Audit log tabs) |
| `eval/` | Dataset download, lexicon builder, evaluation |
| `tests/` | Unit tests |

Models, data and libraries used are listed in [DISCLOSURE.md](DISCLOSURE.md).
