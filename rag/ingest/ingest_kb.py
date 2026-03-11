
#!/usr/bin/env python3
"""Ingest local documents into Azure AI Search with vector embeddings (RAG setup).

- Creates/updates an index with a vector field.
- Chunks Markdown/TXT files.
- Generates embeddings using Azure OpenAI.
- Uploads documents (id, title, path, content, embedding).

Requirements:
  pip install azure-search-documents azure-identity azure-ai-openai tiktoken
"""
import os
import re
import json
import glob
import argparse
from typing import List, Dict

# Azure Search
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile, SearchSuggester, SemanticSettings, SemanticConfiguration, SemanticField, SearchFieldDataType
)
from azure.search.documents import SearchClient

# Azure OpenAI (embeddings)
from azure.ai.openai import OpenAIClient

# Optional tokenization
try:
    import tiktoken
except Exception:
    tiktoken = None


def chunk_text(text: str, max_tokens: int = 600, overlap: int = 60) -> List[str]:
    # Simple tokenizer fallback if tiktoken is not available
    words = text.split()
    chunk_size = 250 if tiktoken is None else max_tokens  # crude fallback
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i+chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
        if i < 0:
            break
    return chunks


def load_files(src: str) -> List[Dict]:
    paths = glob.glob(os.path.join(src, '**', '*.*'), recursive=True)
    docs = []
    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        if ext not in {'.md', '.txt'}:
            continue
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        title = os.path.basename(p)
        docs.append({"path": p, "title": title, "content": content})
    return docs


def ensure_index(index_client: SearchIndexClient, index_name: str, vector_dim: int) -> None:
    try:
        index = index_client.get_index(index_name)
        return
    except Exception:
        pass

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String, sortable=True, filterable=True, facetable=False),
        SearchableField(name="path", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        SearchField(name="embedding", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=vector_dim, vector_search_profile_name="vdb")
    ]

    vector_search = VectorSearch(algorithm_configurations=[HnswAlgorithmConfiguration(name="hnsw")],
                                 profiles=[VectorSearchProfile(name="vdb", algorithm_configuration_name="hnsw")])

    semantic = SemanticSettings(configurations=[
        SemanticConfiguration(name="sem-default", prioritized_fields={
            "titleField": SemanticField(field_name="title"),
            "contentFields": [SemanticField(field_name="content")]
        })
    ])

    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, semantic_settings=semantic,
                        suggesters=[SearchSuggester(name="sg", source_fields=["title"])])
    index_client.create_index(index)


def embed_texts(client: OpenAIClient, deployment: str, texts: List[str]) -> List[List[float]]:
    embeddings = []
    # Batch call to reduce overhead
    for t in texts:
        resp = client.embeddings.create(model=deployment, input=t)
        embeddings.append(resp.data[0].embedding)
    return embeddings


def upsert_docs(search_client: SearchClient, docs: List[Dict]):
    # azure-search-documents expects a list of actions
    actions = [{"@search.action": "mergeOrUpload", **d} for d in docs]
    search_client.upload_documents(actions)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--search-endpoint', required=True)
    ap.add_argument('--search-key', required=True)
    ap.add_argument('--index', default='kb-index')
    ap.add_argument('--aoai-endpoint', required=True)
    ap.add_argument('--aoai-key', default=os.getenv('AOAI_API_KEY'))
    ap.add_argument('--embedding-deployment', required=True)
    ap.add_argument('--src', default='docs/standards')
    args = ap.parse_args()

    # Load and chunk docs
    raw_docs = load_files(args.src)
    if not raw_docs:
        print(f"No documents found under: {args.src}")
        return

    # Init clients
    index_client = SearchIndexClient(endpoint=args.search-endpoint, credential=AzureKeyCredential(args.search_key))
    search_client = SearchClient(endpoint=args.search-endpoint, index_name=args.index, credential=AzureKeyCredential(args.search_key))
    aoai = OpenAIClient(args.aoai_endpoint, args.aoai_key)

    # Determine dimension: embed one sample
    sample_emb = aoai.embeddings.create(model=args.embedding_deployment, input="dimension probe").data[0].embedding
    vector_dim = len(sample_emb)

    ensure_index(index_client, args.index, vector_dim)

    # Prepare docs
    out_docs = []
    doc_id = 0
    for d in raw_docs:
        chunks = chunk_text(d['content'])
        chunk_embeddings = embed_texts(aoai, args.embedding_deployment, chunks)
        for i, (chunk, emb) in enumerate(zip(chunks, chunk_embeddings)):
            doc_id += 1
            out_docs.append({
                "id": f"{doc_id}",
                "title": d['title'],
                "path": d['path'],
                "content": chunk,
                "embedding": emb,
            })

    print(f"Uploading {len(out_docs)} chunks to index '{args.index}' ...")
    upsert_docs(search_client, out_docs)
    print("Done.")

if __name__ == '__main__':
    main()
