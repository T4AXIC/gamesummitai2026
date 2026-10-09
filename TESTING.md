# Quality testing

## What we measure

- **Protected:** the share of labelled personal values in which at least 90% of the characters were masked, by any detector. **Leak rate = 1 − protected.** This is the number that matters for privacy.
- **Recall (right type):** the share of labelled values masked by a detector of the correct type (at least 50% of characters).
- **Precision:** the share of our detections that overlap a labelled personal value. A false alarm masks harmless text; it does not leak anything.

## Data

| Set | Size | Source | Used for |
|---|---|---|---|
| Test | 1,000 texts, 2,065 in-scope values | [LocalDoc/pii_ner_azerbaijani](https://huggingface.co/datasets/LocalDoc/pii_ner_azerbaijani), 10 random pages, seed 2026 | **Reported results only** |
| Dev | 2,000 texts | Same dataset, 20 other pages, no overlap with test | Tuning patterns; building the name lexicon |
| Hand-written | 20 texts | Written by the team: messy AZ/RU/EN, lower case, no diacritics, mixed scripts | Realistic support-ticket stress test |

Labels in scope: given name, surname, phone, e-mail, ID card, passport, tax number, driver licence, credit card, date, street, building number.
Out of scope: city, time, age and zip code. These are not personal data on their own, so they are not counted either way.

## Baselines

1. **Generic regex baseline.** E-mail, any long digit sequence as a phone number, and ISO and slash dates. This is roughly what a default, non-localised filter catches.
2. **Pərdə without the name detector.** An ablation that shows what the Azerbaijani name handling adds.

## Results: held-out test (1,000 texts)

| System | Protected | Leak rate | Precision |
|---|---|---|---|
| **Pərdə** | **94.9%** | **5.1%** | 93.0% |
| Pərdə without name detector | 41.1% | 58.9% | 96.0% |
| Generic regex baseline | 23.9% | 76.1% | 96.4% |

| Entity | Values | Recall (right type) | Protected | Precision |
|---|---|---|---|---|
| PERSON | 1,144 | 97.2% | 97.4% | 90.6% |
| PHONE | 184 | 100.0% | 100.0% | 100.0% |
| EMAIL | 132 | 100.0% | 100.0% | 99.2% |
| ID_NUMBER | 165 | 100.0% | 100.0% | 100.0% |
| CARD | 25 | 100.0% | 100.0% | 100.0% |
| DATE | 117 | 80.3% | 80.3% | 78.5% |
| ADDRESS | 298 | 74.8% | 82.2% | 97.1% |

## Results: hand-written cases (20 texts)

| System | Protected | Leak rate | Precision |
|---|---|---|---|
| **Pərdə** | **98.7%** | 1.3% | 96.6% |
| Pərdə without name detector | 56.6% | 43.4% | 100.0% |
| Generic regex baseline | 28.9% | 71.1% | 100.0% |

## Real failures (held-out test and hand-written set)

| Missed value | Text (shortened) | Why |
|---|---|---|
| `Ульвия` | "zəng: 0705552211 - **Ульвия**, deyir ki…" | A Cyrillic spelling of an Azerbaijani name that isn't in the lexicon, and there is no surname next to it. |
| `Ələsgər` | "22:48:43 **Ələsgər**: Mənim nömrəm…" | A rare given name, not in the dev-built lexicon. |
| `İsmayılqızı` | "Mənim adım Ceyla **İsmayılqızıdır**" | A patronymic fused with a suffix (`-qızı` + `-dır`), which isn't handled yet. |
| `Callan's Lane, 8` | "…materialları **Callan's Lane, 8**…" | A non-Azerbaijani street format. |
| `S.S. AXUNDOV pr.` | "Diplomunuzu 1 **S.S. AXUNDOV pr.**-dən…" | Two initials with a space between them. |
| `1987/01/01` | "Yubileyimiz: **1987/01/01**" | The `yyyy/mm/dd` format isn't supported yet. We didn't add it after seeing the test set, so the score stays honest. |
| `0` / `5` (building numbers) | "…**5** ilə doldurun" | Bare single digits labelled as building numbers in the dataset. We don't mask lone digits on purpose. |

What changed during development (on dev only), and what each change did to leak rate on dev:
- Names: added the lexicon, case-ending stripping and greeting/title context. Leak rate went from 52.9% to 12.2%.
- IDs: allowed `I`/`O` in FIN, added `AZE`+7 digits and the driver-licence pattern. Leak rate went from 12.2% to 5.5%.

## Limitations (stated honestly)

- **The dataset is machine-translated** from an English PII corpus, so some contexts are unnatural. That's why we added the hand-written set. The team wrote those cases itself and could see them during development, so treat that set as a smoke test, not an independent benchmark.
- **Names that aren't in the lexicon,** appear without a surname, and don't follow a title or greeting can be missed. The planned fix is a local Azerbaijani NER model as a second detector.
- **Dates and addresses** are the weakest types (about 80%). Free-form addresses vary a lot.
- **Precision is 93%.** Some capitalised words that are also given names (`Ümid`, `Ulduz`, `Bahar`) get masked. This is the safe direction: harmless text is hidden, and no data leaks.
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
