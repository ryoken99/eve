# Codex 2 Runtime Scope

Codex 2 validates Eve in the real PC runtime.

## Expected From Codex 2

- admin/elevation proof on Windows;
- startup and shortcut behaviour;
- browser profile Eve opening on the correct monitor;
- X posting and scheduling verification;
- closing browser pages after tasks;
- single-tab research navigation;
- Windows UI Automation provider implementation;
- DOM/accessibility validation in live browser;
- Task Scheduler to Eve cron prompt bridge;
- daemon runtime and token gate validation;
- `eve.ps1` startup on PC 1 and PC 2;
- full health check evidence.

## Integration Contract

Runtime code should consume Codex 1 schemas instead of inventing incompatible payloads.

Important contracts:

- `core.world_state_schema.WorldState`
- `computer.computer_use_observation.ComputerUseObservation`
- `computer.interface_tree_provider.FALLBACK_ORDER`
- `memory.transcript_schema.TranscriptEvent`
- `autonomy.autonomous_intent.AutonomousIntent`
- `lab.lab_schema.LabCandidate`
- `self_improvement.arsi_cycle`
