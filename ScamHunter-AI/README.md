# 🛡️ ScamHunter AI

Evidence-first scam investigation assistant built with Streamlit, a FAISS knowledge
base (RAG), specialist AI agents, web research, Groq as the primary model and an
automatic Gemini fallback chain.

## Features

**Investigation**
- Quick Check and Deep Investigation modes
- Specialist agents: classifier, RAG, evidence, scam patterns, contradictions, judge, critic, response
- FAISS knowledge base with SHA-256 incremental indexing (PDF / DOCX / TXT / MD)
- Web research (DuckDuckGo) with disk cache and short targeted queries
- Evidence citations, contradiction analysis, prompt-injection defence, upload validation
- Groq primary path, Gemini fallback chain (no manual model picker)

**Added in this version**
- **Instant scan** - works with no API key: finds links, phone numbers, e-mails and crypto
  wallets, flags urgency / OTP requests / upfront fees / fake-bank wording / risky domains,
  and shows a 0-100 signal meter with the quoted evidence. It is a hint, not proof.
- **Screenshot analysis** - upload a PNG/JPG/WEBP; Gemini reads the text, which is then scanned and investigated
- **Attachments are analysed in-session** (previously uploads were saved but never read). They are not added to the shared knowledge base unless `PERSIST_UPLOADS=1`
- **Response language**: English, Urdu, Roman Urdu
- **Response style** (Concise / Balanced / Detailed) now actually controls the answer
- **Verdict badge** (red / yellow / green) is requested from the model explicitly
- **Download report** (Markdown) for every answer
- Example prompts, status cards, setup banner when no key is configured
- Embeddings run on ONNX (`fastembed`), so no PyTorch install; keyword fallback if the model cannot load

## Project layout

```
app.py                  Streamlit entry point
agents/                 Orchestrator and specialist agents
config/                 Settings and model result types
providers/              Groq, Gemini and the router
rag/                    Extraction, chunking, embeddings, FAISS store, retriever
tools/                  Web search, upload validation, indicators scanner, report builder
ui/                     Theme, sidebar, components, verdict, chat history
knowledge_base/         Reference PDFs, FAISS index, manifest
scripts/                build_knowledge_base.py, health_check.py
tests/                  Unit tests (pytest)
docs/DEPLOYMENT.md      Step-by-step deployment and troubleshooting
.streamlit/             config.toml and secrets example
```

## Run locally

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # add your keys
streamlit run app.py
```

Check your setup any time:

```bash
python scripts/health_check.py
```

Rebuild the knowledge base after changing documents:

```bash
python scripts/build_knowledge_base.py
```

Run the tests:

```bash
pip install -r requirements-dev.txt
pytest
```

## Deploy

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). In short: push to GitHub, create the app on
Streamlit Community Cloud with `app.py` as the main file, choose Python 3.11 under
Advanced settings, and paste your keys under Settings → Secrets.

## Important

The included knowledge-base PDFs are synthetic demonstration material for RAG testing.
They are not official legal, financial, banking or law-enforcement guidance.

ScamHunter AI presents evidence and uncertainty for human review. It cannot guarantee
that a message, website, person or offer is safe or fraudulent.
