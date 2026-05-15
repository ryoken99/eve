# Point 09 Lab Runtime

Generated: 2026-05-15T15:27:18.010922Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS** critical: candidate file created
  - evidence: `"E:\\eve\\lab\\candidate_improvements\\runtime_lab_accept.json"`
- **PASS** critical: candidate can be moved to planned
  - evidence: `"E:\\eve\\lab\\candidate_improvements\\runtime_lab_accept.json"`
- **PASS** critical: accepted decision recorded
  - evidence: `{"candidate": "E:\\eve\\lab\\candidate_improvements\\runtime_lab_accept.json", "report": "E:\\eve\\lab\\reports\\candidate_decisions.jsonl", "result": {"recorded_at": "2026-05-15T16:27:17", "metric_value": 0.9, "threshold": 0.8, "decision": "accept", "notes": "runtime accept"}}`
- **PASS** critical: rejected decision recorded
  - evidence: `{"candidate": "E:\\eve\\lab\\candidate_improvements\\runtime_lab_reject.json", "report": "E:\\eve\\lab\\reports\\candidate_decisions.jsonl", "result": {"recorded_at": "2026-05-15T16:27:17", "metric_value": -0.1, "threshold": 0.8, "decision": "reject", "notes": "runtime reject"}}`
- **PASS**: rejected candidate file exists
  - evidence: `"E:\\eve\\lab\\candidate_improvements\\runtime_lab_reject.json"`
