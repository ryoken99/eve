# PC2 Error Review Limit Report

Data/hora: 2026-05-30
Branch: `codex2/error-review-limits`

## O Que Foi Alterado

`memory/errors/error_review.py` foi limitado para impedir que um unico ciclo real crie dezenas de licoes e candidatos.

`run_error_review()` agora aceita:

- `limit: int = 50`
- `dry_run: bool = False`
- `max_lessons: int = 10`
- `max_candidates: int = 5`
- `deduplicate: bool = True`

## Comportamento Novo

- Pode rever ate `limit` erros.
- Cria no maximo `max_lessons` licoes por ciclo.
- Cria no maximo `max_candidates` candidatos por ciclo.
- Deduplica por assinatura SHA-256 curta baseada em:
  - `source`
  - `task`
  - `error_type`
  - `error_text/message`
- Se uma assinatura ja apareceu no ficheiro de licoes ou candidatos, nao cria duplicado.
- O retorno inclui:
  - `errors_reviewed`
  - `lessons_created`
  - `candidates_created`
  - `duplicates_skipped`
  - `limits`
  - `dry_run`

Campos antigos (`reviewed_count`, `lessons_count`, `candidates_count`) foram mantidos para compatibilidade.

## Testes Corridos

```text
python -m pytest tests/test_error_review.py
5 passed
```

```text
python -m pytest
178 passed
```

```text
python scripts/run_capability_tests.py
21 passed
```

## Testes Cobertos

- `run_error_review(dry_run=True, max_lessons=2, max_candidates=1)` respeita limites.
- Deduplicacao impede duplicados no mesmo lote.
- O retorno contem `duplicates_skipped`.
- O modo `dry_run=True` nao escreve ficheiros definitivos.
- O modo real local escreve no maximo os limites definidos.

## Ficheiros Runtime/Memoria Gerados

Nao foi executado ciclo real.

Os testes usam `tmp_path` para escrita isolada. A suite completa pode tocar caches/test artifacts normais do ambiente, mas esta alteracao nao cria memoria operacional real fora dos testes.

## Recomendacao Para Segundo Ciclo Real Manual

Repetir o segundo ciclo real manual com limites baixos e chamar explicitamente:

```python
run_error_review(limit=50, dry_run=False, max_lessons=10, max_candidates=5, deduplicate=True)
```

Se o daily loop ainda chamar `run_error_review(dry_run=False)` sem parametros novos, os defaults ja aplicam a reducao para 10 licoes e 5 candidatos por ciclo.

## Garantias

- Nao foi executado ciclo real.
- Nao houve self-update.
- Nao houve promocao de candidatos de lab.
- Nao houve alteracao de cron jobs.
- Nao houve browser/email/X/admin/secrets.
- Nao houve commit/push antes dos testes passarem.
