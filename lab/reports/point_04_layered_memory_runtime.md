# Point 04 Layered Memory Runtime

Generated: 2026-05-15T16:04:23.468999Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: route_memory_item writes all samples
  - evidence: `[{"decision": {"layer": "short_term", "target_file": "current_session.md", "description": "Contexto imediato usado para a tarefa atual.", "reason": "metadata marks temporary/current context", "metadata": {"temporary": true}}, "path": "E:\\eve\\memory\\short_term\\current_session.md", "log_path": "E:\\eve\\logs\\autonomy\\memory_layering.jsonl", "vector_index": "E:\\eve\\memory\\semantic_vector\\index.json"}, {"decision": {"layer": "medium_term", "target_file": "layered_observations.md", "description": "Projetos, decisoes recentes e padroes que ainda podem mudar.", "reason": "matched 2 rule keyword(s)", "metadata": {}}, "path": "E:\\eve\\memory\\medium_term\\layered_observations.md", "log_path": "E:\\eve\\logs\\autonomy\\memory_layering.jsonl", "vector_index": "E:\\eve\\memory\\semantic_vector\\index.json"}, {"decision": {"layer": "long_term", "target_file": "stable_memories.md", "description": "Factos estaveis, preferencias persistentes, regras centrais e correcoes importantes.", "reason": "metadata stable=true", "metadata": {"stable": true}}, "path": "E:\\eve\\memory\\long_term\\stable_memories.md", "log_path": "E:\\eve\\logs\\autonomy\\memory_layering.jsonl", "vector_index": "E:\...(truncated)`
- **PASS** critical: classification covers short term
  - evidence: `{"decision": {"layer": "short_term", "target_file": "current_session.md", "description": "Contexto imediato usado para a tarefa atual.", "reason": "metadata marks temporary/current context", "metadata": {"temporary": true}}, "path": "E:\\eve\\memory\\short_term\\current_session.md", "log_path": "E:\\eve\\logs\\autonomy\\memory_layering.jsonl", "vector_index": "E:\\eve\\memory\\semantic_vector\\index.json"}`
- **PASS** critical: promotion moves memory upward
  - evidence: `{"id": "mem-000113", "text": "runtime memory 0", "layer": "medium_term", "confidence": 0.8, "source": "runtime", "created_at": "2026-05-15T16:04:23.301814Z", "last_seen": "2026-05-15T16:04:23.400003Z", "expiry": null, "promotion_score": 1, "contradicts": [], "status": "active"}`
- **PASS** critical: expiry archives memory
  - evidence: `{"id": "mem-000114", "text": "runtime memory 1", "layer": "archive_only", "confidence": 0.8, "source": "runtime", "created_at": "2026-05-15T16:04:23.319814Z", "last_seen": "2026-05-15T16:04:23.417998Z", "expiry": null, "promotion_score": 0, "contradicts": [], "status": "archived"}`
- **PASS**: conflict marks memory IDs
  - evidence: `{"conflicted": ["mem-000115", "mem-000116"]}`
- **PASS**: context bundle can be read
  - evidence: `{"chars": 4000}`
