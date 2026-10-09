# Disclosure: models, data and components

## Written during the hackathon
All code in `perde/`, `app.py`, `eval/` and `tests/`: the detectors, masking and restoration, gateway, UI, evaluation and tests.
Pərdə does not depend on any third-party PII library. The general approach (pattern recognisers plus anonymise/restore) is a well-known one, used for example by Microsoft Presidio. We built our own implementation for Azerbaijani formats.

## Data
| Item | Source | Licence | Use |
|---|---|---|---|
| `data/localdoc_test.jsonl`, `data/localdoc_dev.jsonl` | [LocalDoc/pii_ner_azerbaijani](https://huggingface.co/datasets/LocalDoc/pii_ner_azerbaijani) (subset of about 3,000 rows) | CC BY 4.0 | Evaluation; the dev split builds the name lexicon |
| `perde/lexicon.txt` | Derived from the dev split above | CC BY 4.0 (attribution: LocalDoc) | Given-name and surname lexicon |
| `data/handwritten.jsonl` | Written by the team | Ours | Stress test. All people and numbers are fictional |
| Sample texts in `app.py` | Written by the team | Ours | Demo. Fictional |

## AI models
- **No model is used for detection.** Detection is rules and a lexicon, and runs locally.
- **For the user's task:** any OpenAI-compatible chat model, chosen at runtime. Supported providers are OpenAI, xAI (Grok), Google Gemini, and local Ollama (for example `gemma3`). The default is `mock`, an offline stand-in with no external call, which is used in the demo video unless stated otherwise.

## Libraries
| Library | Licence | Use |
|---|---|---|
| streamlit | Apache-2.0 | Web UI |
| openai (Python SDK) | Apache-2.0 | Client for OpenAI-compatible APIs |
| pytest | MIT | Unit tests (dev only) |
| python:3.12-slim Docker base image | PSF and Debian licences | Container build |

## Assistance
The code and documentation were written with the help of an AI coding assistant (Claude).

## Mocks and caches
- The `mock` provider returns a templated reply built from the tags. It is labelled "[Offline demo model, no external API call]" in its output.
- No results are cached. The evaluation numbers come from `eval/evaluate.py` and are stored in `eval/results.json`.
