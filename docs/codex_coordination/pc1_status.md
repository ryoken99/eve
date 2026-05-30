# PC1 Codex Status

## 2026-05-30

Branch: `codex1/eve-metabolism-core`

Role: Codex 1, architect/integrator for Eve metabolism core.

Files planned/owned:

- `autonomy/eve_daily_loop.py`
- `autonomy/eve_daily_loop_report.py`
- `core/evolution_metrics.py`
- `docs/EVE_METABOLISM_PLAN.md`
- `docs/codex_coordination/integration_contract.md`
- `tests/test_eve_daily_loop.py`
- `tests/test_evolution_metrics.py`

Tests run:

- `python -m pytest tests/test_eve_daily_loop.py tests/test_evolution_metrics.py` -> 6 passed.
- `python scripts/check_fresh_clone_readiness.py` -> ok true after removing hardcoded PC2 paths and installing `sentence-transformers`.
- `python scripts/run_capability_tests.py` -> 21 passed.
- `python -m pytest` -> 157 passed.

Tests failed:

- Initial `python scripts/check_fresh_clone_readiness.py` failed because `sentence_transformers` was missing and PC2 scripts had hardcoded `E:\eve`.
- Initial `python scripts/run_capability_tests.py` failed on hardcoded PC2 paths.
- Initial `python -m pytest` collected `external/hermes-agent/tests` and failed on Hermes-only dependencies; fixed by adding `pytest.ini` with `testpaths = tests`.

Remaining work:

- Codex 2 should implement research inbox, error review, personality evolution, and autonomous lab modules.
- Codex 1 should later wire Codex 2 modules into the loop through optional imports.

Blocks:

- Working tree contains pre-existing local runtime/memory dirt. Do not commit it.

## Pedido ao outro Codex

Preciso que respeites o contrato em `docs/codex_coordination/integration_contract.md`.

Ficheiros envolvidos:

- `research/research_inbox.py`
- `research/daily_research_runner.py`
- `memory/errors/error_review.py`
- `lab/autonomous_lab.py`

Contrato esperado:

- Expor funcoes pequenas que retornam dicts serializaveis.
- Nao quebrar `run_eve_daily_loop(dry_run=True)` quando os modulos existem.

Exemplo de chamada:

```python
from research.research_inbox import summarize_research_inbox
summary = summarize_research_inbox(max_items=5)
```

Critérios de aceitação:

- Falhas devem retornar dict com `ok=False` ou levantar erro claro.
- Sem efeitos externos em dry-run.
