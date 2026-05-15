# Point 05 Vector Memory Core

Goal: Eve must retrieve memory by meaning, not only exact words.

Implemented core:

- `memory/semantic_vector/provider_base.py`
- `VectorProvider`
- `TfidfVectorProvider`
- `LocalEmbeddingProvider` placeholder
- hybrid ranking fields: semantic, recency, importance, confidence
- `semantic_context_prefetch(query)`
- context bundle integration in `memory/memory_manager.py`

8.6 criterion: core architecture met. Embedding provider activation remains runtime/config work.
