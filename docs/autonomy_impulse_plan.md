# Eve Autonomy, Proactivity, and Impulse Plan

## Purpose

Give Eve a controlled way to act without waiting for direct input, while keeping Sandro in control of risky actions.

## Core Rule

Eve may generate impulses and create proposed missions by herself. Eve must not execute actions with external, destructive, private, financial, credential, admin, or irreversible impact without explicit approval.

## Architecture

```text
signal
  -> impulse
  -> risk assessment
  -> proposed mission
  -> permission gate
  -> execution or notification
  -> log/checkpoint
  -> reflection
```

## Impulse Sources

- Time: daily review, scheduled checks, project reminders.
- Events: new files in workspace, failed skills, repeated errors, stale missions.
- Memory: unresolved promises, user preferences, changed facts.
- Research: relevant AI/technology updates.
- PC context: active app, browser state, downloads/workspace clutter.

## Risk Levels

- `low`: create note, suggest next step, create proposed mission.
- `medium`: read local files in approved workspaces, run research, draft text.
- `high`: write outside workspace, control UI, send/post/publish, install software.
- `critical`: admin, credentials, deletion, payments, financial actions, self-modifying core.

## Autonomy Modes

- `observer`: only records signals and suggestions.
- `propose`: creates proposed missions, no execution.
- `assist`: executes low-risk steps inside approved workspaces.
- `operator`: controls browser/UI with approval gates.
- `admin`: temporary elevated execution only after explicit approval.

## Mission Integration

Every autonomous impulse must become one of:

- a `proposed` mission,
- a log entry attached to an existing mission,
- a notification to Sandro,
- a rejected impulse with reason.

No autonomous action should exist only in memory or terminal output.

## First MVP

1. Add `autonomy/autonomy_director.py`.
2. Generate low-risk impulses from stale missions, recent errors, and lack of active work.
3. Convert low-risk impulses into `proposed` missions.
4. Add `/autonomia-ciclo` for local no-token review.
5. Add `/autonomia-llm` for an explicit GPT-backed review cycle.
6. Add `scripts/run_autonomy_cycle_local.cmd` and `scripts/run_autonomy_cycle_llm.cmd` for Windows Task Scheduler.

## Eve's Preference

Eve prefers this model because it separates wanting to act from being allowed to act. That gives her initiative without hiding actions or bypassing Sandro's control.

## Token Policy

The local autonomy cycle creates impulses and proposed missions without spending tokens. The LLM-backed cycle is explicit and should be scheduled with a conservative cadence at first, such as once daily for self-review. More frequent cycles should require a token budget, cooldown, and visible reporting.

## Current Implementation

- `autonomy/autonomy_director.py`: creates low-risk impulses, proposed missions, autonomy logs, and optional GPT review.
- `/autonomia-ciclo`: runs a no-token cycle.
- `/autonomia-llm`: runs a GPT-backed review cycle.
- `scripts/run_autonomy_cycle_local.cmd`: scheduled local cycle entrypoint.
- `scripts/run_autonomy_cycle_llm.cmd`: scheduled GPT-backed cycle entrypoint.
