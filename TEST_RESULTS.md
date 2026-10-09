# Test Results

Run date: 2026-10-09T10:48:27Z

## Environment

- Python: `Python 3.14.7`
- Local model endpoint: `http://127.0.0.1:8080/v1`
- Local provider: `llamacpp`
- Local model: `gemma-4-E4B`

## Unit tests

Command:

```bash
.venv/bin/pytest -q
```

Result:

```text
...........                                                              [100%]
11 passed in 0.03s
```

## Local Gemma gateway test

Command:

```bash
.venv/bin/python - <<'PY'
from perde.gateway import run

text = "Salam, mən Nərmin Quliyeva. Kartım 4111 1111 1111 1111, FIN 6TR9K2L. Tel 055 412 33 90."
task = "Bu müraciəti bir cümlə ilə xülasə et və qısa cavab yaz. Tagləri eyni saxla."
res = run(text, task, provider="llamacpp", model="gemma-4-E4B")
print(res.outgoing)
print(res.model_answer)
print(res.restored_answer)
PY
```

Result:

```text
provider: llamacpp
model: gemma-4-E4B
latency_ms: 6732
masked_values: 4
entity_counts: {'PERSON': 1, 'CARD': 1, 'FIN': 1, 'PHONE': 1}
outgoing:
Bu müraciəti bir cümlə ilə xülasə et və qısa cavab yaz. Tagləri eyni saxla.

---
Salam, mən [PERSON_1]. Kartım [CARD_1], FIN [FIN_1]. Tel [PHONE_1].
model_answer:
**Xülasə:** Müraciət sahibi [PERSON_1] öz şəxsi məlumatlarını (kart [CARD_1], FIN [FIN_1] və telefon [PHONE_1]) təqdim edir.

**Cavab:** Məlumatınız qeydə alındı.
restored_answer:
**Xülasə:** Müraciət sahibi Nərmin Quliyeva öz şəxsi məlumatlarını (kart 4111 1111 1111 1111, FIN 6TR9K2L və telefon 055 412 33 90) təqdim edir.

**Cavab:** Məlumatınız qeydə alındı.
```

## Streamlit smoke test

Command:

```bash
.venv/bin/streamlit run app.py --server.headless true --server.port 8501
curl -fsS http://127.0.0.1:8501/_stcore/health
```

Result:

```text
ok
```
