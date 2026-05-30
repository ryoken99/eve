# Codex Coordination Integration Contract

## Branch Rules

Codex 1 works on:

`codex1/eve-metabolism-core`

Codex 2 works on:

`codex2/eve-research-lab-personality`

Neither Codex should work directly on `main`.

## Primary Ownership

Codex 1 owns:

- `autonomy/eve_daily_loop.py`
- `autonomy/eve_daily_loop_report.py`
- `core/evolution_metrics.py`
- `docs/EVE_METABOLISM_PLAN.md`
- `docs/codex_coordination/integration_contract.md`
- `tests/test_eve_daily_loop.py`
- `tests/test_evolution_metrics.py`

Codex 2 owns:

- `research/research_inbox.py`
- `research/daily_research_runner.py`
- `memory/errors/error_review.py`
- `lab/autonomous_lab.py`
- `core/personality_engine.py` only if necessary and carefully
- `tests/test_research_inbox.py`
- `tests/test_personality_evolution.py`
- `tests/test_error_review.py`
- `tests/test_autonomous_lab.py`
- `tests/test_daily_research_runner.py`

## Shared Sensitive File

`core/eve_tool_registry.py`

Before editing it, each Codex must:

1. Run `git pull`.
2. Check whether the other Codex changed the file.
3. Make the smallest possible additive change.
4. If conflict risk is high, write a patch note instead of overwriting.

Codex 1 may add:

- `eve_daily_loop`
- `evolution_metrics_report`

Codex 2 may add:

- `research_inbox_add`
- `research_inbox_process`
- `preference_candidate_record`
- `preference_mature`
- `error_review`
- `lab_review`
- `daily_research_collection`

Conflict patch files:

- `docs/codex_coordination/pc1_tool_registry_patch.md`
- `docs/codex_coordination/pc2_tool_registry_patch.md`

## Progress Logs

Codex 1 writes progress in:

- `docs/codex_coordination/pc1_status.md`

Codex 2 writes progress in:

- `docs/codex_coordination/pc2_status.md`

Each status entry should include:

- date/time;
- branch;
- files changed;
- tests run;
- tests failed;
- remaining work;
- blockers;
- request to the other Codex.

## Request Format

```markdown
## Pedido ao outro Codex

Preciso que faças:
...

Ficheiros envolvidos:
...

Contrato esperado:
...

Exemplo de chamada:
...

Critérios de aceitação:
...
```

## Integration Order

1. Codex 1 creates this contract and the daily loop skeleton.
2. Codex 2 creates research inbox, personality evolution, error review, and lab.
3. Codex 1 links Codex 2 modules into the daily loop through optional imports.
4. Both update the tool registry carefully.
5. Both run their own tests.
6. Codex 1 runs integration tests with `python -m pytest`.
7. Create `docs/codex_coordination/final_integration_report.md`.

## Failure Rules

If an imported module does not exist:

- Do not delete code.
- Use a fallback.
- Record the missing module in reports.

If a test fails:

- Do not hide it.
- Record exact error.
- Propose correction.

If there is a Git conflict:

- Stop.
- Record status.
- Do not run destructive reset.
- Resolve manually with care.

If the daily loop breaks:

- It must continue in degraded mode.
- The failed stage must appear in `steps` with `ok=false`.

## Final Success Criteria

The integrated project is ready when:

```powershell
python -m pytest
```

works, and this command returns a dict with the expected daily loop sections:

```powershell
python -c "from autonomy.eve_daily_loop import run_eve_daily_loop; print(run_eve_daily_loop(dry_run=True))"
```

Expected sections:

- awareness;
- transcripts;
- diary consolidation;
- dream/memory review;
- error review;
- research inbox;
- lab candidates;
- improvement plan;
- metrics;
- report path.
