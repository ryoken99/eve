# Point 12 Research To Lab Runtime

Generated: 2026-05-15T16:24:46.823977Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: high confidence useful research goes to lab
  - evidence: `{"title": "Agent memory benchmark", "summary": "tool browser automation and memory evaluation", "confidence": 0.9, "matched_terms": ["agent", "memory", "browser", "tool", "evaluation", "benchmark", "automation"], "decision": "test_in_lab", "candidate": "E:\\eve\\lab\\candidate_improvements\\research_agent_memory_benchmark.json"}`
- **PASS** critical: medium confidence useful research goes to watch
  - evidence: `{"title": "RAG browser agent", "summary": "agent memory tool", "confidence": 0.65, "matched_terms": ["agent", "memory", "browser", "tool", "rag"], "decision": "watch", "candidate": null}`
- **PASS** critical: irrelevant research is ignored
  - evidence: `{"title": "Garden furniture", "summary": "chairs and tables", "confidence": 0.9, "matched_terms": [], "decision": "ignore", "candidate": null}`
- **PASS** critical: security rollback is apply_after_review
  - evidence: `{"title": "Security rollback method", "summary": "rollback and security", "confidence": 0.4, "matched_terms": [], "decision": "apply_after_review", "candidate": "E:\\eve\\lab\\candidate_improvements\\research_security_rollback_method.json"}`
- **PASS** critical: lab candidate file exists for test_in_lab
  - evidence: `"E:\\eve\\lab\\candidate_improvements\\research_agent_memory_benchmark.json"`
