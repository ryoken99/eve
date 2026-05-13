# Eve 17-Point Operational Capability Contract

This contract defines the external evidence required before Eve can claim a
score of 8.6/10 or higher for Sandro's 17 capability goals.

## Global 8.6 Rule

A point is not mature because a module exists. A point is mature only when it
has executable behavior, audit evidence, failure handling, and tests.

Each capability point must provide:

- at least 3 capability tests;
- at least 1 integration or simulation test;
- an audit log or metrics output;
- a runtime verifier or deterministic simulator;
- known limitations recorded explicitly.

## Scoring Inputs

Scores are computed from evidence:

- `tests`: unit and integration coverage for the point;
- `runtime_verified`: live state check or deterministic simulation;
- `audit_logs`: action/result evidence;
- `safety`: explicit refusal paths for risky actions;
- `limitations`: documented remaining gaps.

## Point 16 ARSI Rule

Point 16 is ARSI: Autonomous Recursive Self Improvement. ARSI means Eve may
autonomously propose, test, measure, and apply safe low-risk improvements while
medium/high-risk changes require approval, backups, tests, and rollback.

## Computer Use v2 Rule

Computer use must prefer structured interfaces before pixels:

1. Browser DOM / Playwright
2. Windows UI Automation
3. OCR
4. Coordinates / pyautogui

OCR is a fallback, not the primary strategy when DOM or UIA data is available.
Sensitive submit-like actions require confirmation and app permission.
