# Point 13 Learning Separation Runtime

Generated: 2026-05-15T16:24:46.950028Z
EVE_ROOT: `E:\eve`
Runtime score: **10.0/10**

## Checks

- **PASS**: world classified correctly
  - evidence: `{"text": "Noticia mundial sobre ciencia e sociedade", "got": "world"}`
- **PASS** critical: technology classified correctly
  - evidence: `{"text": "OpenAI publicou paper sobre agent memory benchmark", "got": "technology"}`
- **PASS** critical: sandro classified correctly
  - evidence: `{"text": "Sandro prefere anime e treino", "got": "sandro"}`
- **PASS** critical: personality classified correctly
  - evidence: `{"text": "Eu gosto de narrativa procedural", "got": "personality"}`
- **PASS**: project classified correctly
  - evidence: `{"text": "Projeto RPG Maker no repo da Eve", "got": "project"}`
- **PASS** critical: validator detects misfiled technology/personality mix
  - evidence: `[{"text": "OpenAI publicou paper sobre agent memory benchmark", "target": "personality", "suggested_target": "technology", "misfiled": true}]`
- **PASS**: validate_target_folder accepts correct target
  - evidence: `"OpenAI publicou paper sobre agent memory benchmark"`
