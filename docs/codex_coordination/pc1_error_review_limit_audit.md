# PC1 Audit: Error Review Limits

Generated: 2026-05-30

## Scope

PC1 audited the PC2 branch that limits `error_review` output per cycle.

No real Eve cycle was executed. No cron jobs were changed.

## Branch And Commit

- Audited branch: `codex2/error-review-limits`
- Audited commit: `a6dbf7a`
- Local audit branch: `audit/error-review-limits`

## Files Changed In Audited Commit

Only the expected files were present:

- `docs/codex_coordination/pc2_error_review_limit_report.md`
- `memory/errors/error_review.py`
- `tests/test_error_review.py`

No logs, state, secrets, workspace files, private memory dumps, vector DB files, or runtime artifacts were found in the audited commit.

## Direct Function Test

Command:

```powershell
python -c "from memory.errors.error_review import run_error_review; r = run_error_review(limit=50, dry_run=True, max_lessons=2, max_candidates=1, deduplicate=True); print(r); assert 'errors_reviewed' in r; assert 'lessons_created' in r; assert 'candidates_created' in r; assert 'duplicates_skipped' in r; assert 'limits' in r; assert r['dry_run'] is True; assert r['lessons_created'] <= 2; assert r['candidates_created'] <= 1; print('error_review limits ok')"
```

Result:

- `errors_reviewed`: 45
- `lessons_created`: 2
- `candidates_created`: 1
- `duplicates_skipped`: 38
- `limits`: present
- `dry_run`: true
- Result: passed

## Test Results

- `python -m pytest tests/test_error_review.py`: 5 passed
- `python -m pytest`: 178 passed
- `python scripts/run_capability_tests.py`: 21 passed
- `python scripts/check_fresh_clone_readiness.py`: ok true

Environment note:

- `tesseract_executable_on_path`: false
- This is an optional OCR fallback dependency and does not block the audited patch.

## Deduplication

Deduplication is present and visible through `duplicates_skipped`.

The direct test found 38 duplicate skips, which confirms that repeated errors are not blindly converted into new lessons/candidates during dry-run.

## Limits

Limits are confirmed:

- `max_lessons=2` was respected.
- `max_candidates=1` was respected.
- Returned `limits` includes `limit`, `max_lessons`, `max_candidates`, and `deduplicate`.

Backward compatibility is preserved through:

- `reviewed_count`
- `lessons_count`
- `candidates_count`

## Recommendation

Approved for merge into `main`.

After merge, PC1 recommends Phase 2.4:

- Repeat the second real manual controlled cycle.
- Use `max_lessons=10`.
- Use `max_candidates=5`.
- Keep real recurrence disabled.
- Keep dry-run recurrence active.
- Do not promote lab candidates automatically.
- Do not apply self-update.
- Observe whether duplicates remain controlled.
