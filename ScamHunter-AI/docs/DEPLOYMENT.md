# Deployment guide (Streamlit Community Cloud)

## 1. Push the project
Upload this folder to a GitHub repository. `.streamlit/secrets.toml` and `data/` are
git-ignored, so keys and visitor chats are never committed.

## 2. Create the app
1. Go to share.streamlit.io and choose **Create app**.
2. Repository: your repo. Branch: `main`. Main file path: `app.py`.
3. **Advanced settings → Python version: 3.11.**
4. **Advanced settings → Secrets**, paste:

```toml
GROQ_API_KEY = "..."
GEMINI_API_KEY = "..."
```

At least one key is required for full investigations. Without a key the app still starts
and shows the instant scan, with a banner explaining what is missing.

## 3. First start
The first start downloads the embedding model (about 90 MB) and can take a minute.
The FAISS index is already committed in `knowledge_base/faiss`; if it is missing the app
builds it automatically.

## Likely reasons the old version failed to deploy
(Found by reading the code and requirements; no deploy log was available, so check *Manage app → Logs* if anything still fails.)

| Cause | Fix in this version |
|---|---|
| `sentence-transformers` pulls in PyTorch, a very large install | Replaced by `fastembed` (ONNX). Same model, same 384 dimensions, so the existing index still works |
| `crewai` was listed but never imported (huge dependency tree, frequent conflicts) | Removed |
| All versions were `>=` with no upper bound | Bounded `streamlit>=1.43,<2`; test tools moved to `requirements-dev.txt` |
| `use_container_width` is deprecated in new Streamlit | `ui/compat.py` picks the keyword the installed version supports |
| `st.chat_input(max_upload_size=...)` does not exist in older Streamlit | Falls back automatically |
| Gemini model names that do not exist slowed every call | Missing models are skipped for the rest of the session |
| `python scripts/build_knowledge_base.py` failed from the repo root | Scripts add the project root to `sys.path` |

## Troubleshooting
- **Build fails on a package**: open *Manage app → Logs*, copy the failing line, and check the Python version is 3.11.
- **"No AI key found" banner**: add the secrets in step 2, then *Reboot app*.
- **Out-of-memory restarts**: Community Cloud has a small memory limit. Avoid loading extra models and do not add PyTorch back.
- **Chat history disappears**: Community Cloud storage is temporary. History survives only until the app restarts.
- **Web evidence is empty**: DuckDuckGo may rate-limit shared cloud IPs. The investigation still completes from the knowledge base.
- **Screenshot upload says it needs a key**: image reading uses Gemini; add `GEMINI_API_KEY`.

## Rebuilding the index in GitHub Actions
`.github/workflows/build-knowledge-base.yml` rebuilds and commits the index when files under
`knowledge_base/documents`, `rag`, `config` or the build script change. Pull before you push
after it runs.
