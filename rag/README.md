
# RAG Ingestion

This folder contains scripts to build a **vector index** in **Azure AI Search** and upload content (e.g., standards, runbooks) for retrieval by agents (PR Review, Log Analyst, etc.).

## Layout
- `ingest/ingest_kb.py` – CLI script to create index, embed content with Azure OpenAI, and upload documents.
- Source docs: put Markdown/PDF/TXT under `docs/standards/` (or pass `--src`).

## Quick Start
```bash
python rag/ingest/ingest_kb.py   --search-endpoint https://<your-search>.search.windows.net   --search-key <admin-key>   --index kb-index   --aoai-endpoint https://<your-endpoint>.openai.azure.com/   --embedding-deployment text-embedding-3-small   --src docs/standards
```

The agent can then query Azure AI Search for relevant snippets and cite them in PR comments.
