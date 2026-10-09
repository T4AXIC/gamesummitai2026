# Quality testing

## What we measure

- **Protected:** the share of labelled personal values in which at least 90% of the characters were masked, by any detector. **Leak rate = 1 − protected.** This is the number that matters for privacy.
- **Recall (right type):** the share of labelled values masked by a detector of the correct type (at least 50% of characters).
- **Precision:** the share of our detections that hit a labelled in-scope value of the same type. Detections that touch only out-of-scope labels (city, time, age, zip) are left out of the count. A false alarm masks harmless text; it does not leak anything.

## Data

| Set | Size | Source | Used for |
|---|---|---|---|
| Test | 1,000 texts, 2,065 in-scope values | [LocalDoc/pii_ner_azerbaijani](https://huggingface.co/datasets/LocalDoc/pii_ner_azerbaijani), 10 random pages, seed 2026 | **Reported results only** |
| Dev | 2,000 texts | Same dataset, 20 other pages, no overlap with test | Tuning patterns; building the name lexicon |
| Hand-written | 20 texts | Written by the team: messy AZ/RU/EN, lower case, no diacritics, mixed scripts | Realistic support-ticket stress test |

Labels in scope: given name, surname, phone, e-mail, ID card, passport, tax number, driver licence, credit card, date, street, building number.
Out of scope: city, time, age and zip code. These are not personal data on their own, so they are not counted either way.

## Baselines

0. **Today's practice: pasting the raw text into a chatbot.** Nothing is masked, so 100% of the personal values reach the provider. Redacting by hand is the alternative; we did not time it, so we make no claim about its speed.

1. **Generic regex baseline.** E-mail, any long digit sequence as a phone number, and ISO and slash dates. This is roughly what a default, non-localised filter catches.
2. **Pərdə without the name detector.** An ablation that shows what the Azerbaijani name handling adds.

## Results: held-out test (1,000 texts)

| System | Protected | Leak rate | Precision |
|---|---|---|---|
| **Pərdə** | **94.9%** | **5.1%** | 92.8% |
| Pərdə without name detector | 41.2% | 58.8% | 95.8% |
| Generic regex baseline | 23.9% | 76.1% | 72.9% |

| Entity | Values | Recall (right type) | Protected | Precision |
|---|---|---|---|---|
| PERSON | 1,144 | 97.2% | 97.4% | 90.4% |
| PHONE | 184 | 100.0% | 100.0% | 100.0% |
| EMAIL | 132 | 100.0% | 100.0% | 99.2% |
| ID_NUMBER | 165 | 100.0% | 100.0% | 100.0% |
| CARD | 25 | 100.0% | 100.0% | 100.0% |
| DATE | 117 | 80.3% | 80.3% | 77.7% |
| ADDRESS | 298 | 75.2% | 82.6% | 97.1% |

## Results: hand-written cases (20 texts)

| System | Protected | Leak rate | Precision |
|---|---|---|---|
| **Pərdə** | **98.7%** | 1.3% | 96.6% |
| Pərdə without name detector | 56.6% | 43.4% | 100.0% |
| Generic regex baseline | 28.9% | 71.1% | 59.1% |

## Real failures (held-out test and hand-written set)

| Missed value | Text (shortened) | Why |
|---|---|---|
| `Ульвия` | "zəng: 0705552211 - **Ульвия**, deyir ki…" | A Cyrillic spelling of an Azerbaijani name that isn't in the lexicon, and there is no surname next to it. |
| `Ələsgər` | "22:48:43 **Ələsgər**: Mənim nömrəm…" | A rare given name, not in the dev-built lexicon. |
| `İsmayılqızı` | "Mənim adım Ceyla **İsmayılqızıdır**" | A patronymic fused with a suffix (`-qızı` + `-dır`), which isn't handled yet. |
| `8` (building number) | "…materialları Callan's Lane, **8**…" | A building number after a non-Azerbaijani street name. |
| `S.S. AXUNDOV pr.` | "Diplomunuzu 1 **S.S. AXUNDOV pr.**-dən…" | Two initials with a space between them. |
| `1987/01/01` | "Yubileyimiz: **1987/01/01**" | The `yyyy/mm/dd` format isn't supported yet. We didn't add it after seeing the test set, so the score stays honest. |
| `0` / `5` (building numbers) | "…**5** ilə doldurun" | Bare single digits labelled as building numbers in the dataset. We don't mask lone digits on purpose. |

What changed during development (on dev only), and what each change did to leak rate on dev. These numbers come from runs during development (`python eval/evaluate.py --split dev`); the intermediate code versions are not all kept:
- Names: added the lexicon, case-ending stripping and greeting/title context. Leak rate went from 52.9% to 12.2%.
- IDs: allowed `I`/`O` in FIN, added `AZE`+7 digits and the driver-licence pattern. Leak rate went from 12.2% to 5.5%.
- A stricter precision count (same type, in-scope only) and two false-positive fixes tuned on dev (product codes like `ABC1234` as FIN; 10-digit numbers next to "tel" as VÖEN) moved held-out precision from 93.0% to 92.8%; protected stayed at 94.9%. The same count drops the generic baseline's precision from 96.4% to 72.9%.
- After the first held-out run, a code review found two bugs in the Government demo sample: a house number before a full stop, and a bracketed landline. Fixing them moved held-out addresses from 82.2% to 82.6%. Nothing else changed.

## Limitations (stated honestly)

- **The dataset is machine-translated** from an English PII corpus, so some contexts are unnatural. That's why we added the hand-written set. The team wrote those cases itself and could see them during development, so treat that set as a smoke test, not an independent benchmark.
- **Names that aren't in the lexicon,** appear without a surname, and don't follow a title or greeting can be missed. The planned fix is a local Azerbaijani NER model as a second detector.
- **Dates and addresses** are the weakest types (about 80%). Free-form addresses vary a lot.
- **Precision is 92.8%.** Some capitalised words that are also given names (`Ümid`, `Ulduz`, `Bahar`) get masked. This is the safe direction: harmless text is hidden, and no data leaks.
- **The leak blocker** checks exact detected values only. It cannot catch a value the detectors missed.
- **Latency:** 0.14 ms per text (1,000 texts, average 112 characters, one CPU core). The LLM call dominates the total time.

## Reproduce

```bash
python eval/fetch_sample.py         # downloads the dev and test splits (about 3,000 rows)
python eval/build_lexicon.py        # builds perde/lexicon.txt from DEV only
python eval/evaluate.py             # held-out results -> eval/results.json
python eval/evaluate.py --split dev --show-failures 30
pytest -q
```
