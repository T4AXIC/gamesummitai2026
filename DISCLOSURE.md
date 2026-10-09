# Disclosure: models, data and components

## Written during the hackathon
All code in `perde/`, `app.py`, `index.html`, `eval/`, `tests/`, `tools/video/`, `run.bat` and `Dockerfile`: the detectors, masking and restoration, gateway, UI, evaluation, tests, launchers and video tooling.
Pərdə does not depend on any third-party PII library. The general approach (pattern recognisers plus anonymise/restore) is a well-known one, used for example by Microsoft Presidio. We built our own implementation for Azerbaijani formats.

## Data
| Item | Source | Licence | Use |
|---|---|---|---|
| `data/localdoc_test.jsonl`, `data/localdoc_dev.jsonl` | [LocalDoc/pii_ner_azerbaijani](https://huggingface.co/datasets/LocalDoc/pii_ner_azerbaijani) (subset of about 3,000 rows) | CC BY 4.0 | Evaluation; the dev split builds the name lexicon |
| `perde/lexicon.txt` | Derived from the dev split above | CC BY 4.0 (attribution: LocalDoc) | Given-name and surname lexicon |
| `data/handwritten.jsonl` | Written by the team | Ours | Stress test. All people and numbers are fictional |
| Sample texts in `app.py` | Written by the team | Ours | Demo. Fictional |
| `demo_texts/` (56 scenarios) | Written by the team | Ours | Copy-paste demo inputs; also shown masked in the demo video. Fictional |

## AI models
- **No model is used for detection.** Detection is rules and a lexicon, and runs locally.
- **For the user's task:** any OpenAI-compatible chat model, chosen at runtime. Supported providers, with their default model names: OpenAI (`gpt-4o-mini`), xAI Grok (`grok-3-mini`), Google Gemini (`gemini-2.5-flash`), local Ollama (`gemma3`) and any llama.cpp OpenAI-compatible server (`gemma-4-E4B`). The default is `mock`, an offline stand-in with no external call. The live demo and the demo video use `mock`.
- **Tested end to end with a real model:** Gemma 4 E4B on a local llama.cpp server (see `TEST_RESULTS.md`).

## Libraries
| Library | Licence | Use |
|---|---|---|
| streamlit | Apache-2.0 | Web UI |
| openai (Python SDK) | Apache-2.0 | Client for OpenAI-compatible APIs |
| pytest | MIT | Unit tests (dev only) |
| python:3.12-slim Docker base image | PSF and Debian licences | Container build |
| @stlite/browser 1.9.2 (via jsDelivr CDN) | Apache-2.0 | Runs the Streamlit app in the browser for the live demo |
| Pyodide (loaded by stlite) | MPL-2.0 | Python in WebAssembly for the live demo |
| Hugging Face Spaces (static) | Hosting service | Live demo hosting |
| Pillow, numpy, imageio-ffmpeg (FFmpeg), qrcode | HPND, BSD-3, BSD-2 (FFmpeg: LGPL/GPL), BSD | Demo video rendering only |
| websockets, Google Chrome (headless) | BSD-3, proprietary | Screenshots for the demo video only |
| Segoe UI, Cascadia Mono fonts | Windows system fonts (Cascadia: OFL) | Text in the demo video |

## Assistance
The code and documentation were written with the help of an AI coding assistant (Claude).

## Mocks and caches
- The `mock` provider returns a templated reply built from the tags. It is labelled "[Offline demo model, no external API call]" in its output.
- No results are cached. The evaluation numbers come from `eval/evaluate.py` and are stored in `eval/results.json`.

## Demo video
`media/perde-demo-v2.mp4` (main, 60 s) and `media/perde-demo.mp4` (first cut, 56 s) were rendered by `tools/video/render_v2.py` and `tools/video/render.py` during the hackathon (screenshots by `tools/video/capture.py`). The app footage is real screenshots of the running app, using the offline model. The tags shown come from the real masking engine. The soundtrack is synthesized in code, with no third-party music.
