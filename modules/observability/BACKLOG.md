# BACKLOG — observability

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-09

## Progress Overview

The observability feature owns the audit-ledger and per-skill telemetry side:
`SkillsLedger` (append/read/compact/rollback), `SkillsTelemetry` (seed,
reanchor, curated report, views bump), and `SkillsPhraseScan`
(session scan + phrase mining). `SkillsObservabilityAgent` dispatches
`ledger`/`usage` behind `ISkillsObservabilityAggregate`, and
`SkillsPhraseAgent` dispatches `traces`/`phrases` behind
`ISkillsTracesAggregate`. Every requirement in [FRD.md](FRD.md) is
implemented and wired into `modules/root_skills_container.py` and
`modules/observability/src/root_observability_container.py`; nothing is in progress.

## Backlog Status

### FR-observability-001: Append and read the audit ledger

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsLedger.ledger_append` appends one content-addressed entry to the audit ledger; `ledger_read` returns up to `limit` most recent entries. The agent routes `ObservabilityOp.LEDGER` to it via `_execute_ledger`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-observability-002: Bump and report per-skill telemetry

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsTelemetry.seed_record_if_missing`, `reanchor_clock`, `curated_report`, and `view` manage the per-skill `.usage.json` sidecar. The agent routes `ObservabilityOp.USAGE` to it via `_execute_usage`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

### FR-observability-003: Scan sessions and mine repeated phrases

| Aspect       | Detail                                                       |
|--------------|--------------------------------------------------------------|
| State        | Done                                                         |
| Done         | `SkillsPhraseScan.scan_sessions` walks `$GROK_HOME/sessions` and `build_phrases` mines repeated exact prompts, stems, and instruction lines. The agent routes `traces`/`phrases` to it via `_execute_phrases`. |
| In Progress  | None                                                         |
| Risk         | None                                                         |
| Updated      | 2026-11-09                                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| PRD          | Business goals and scope                   | [PRD.md](../../PRD.md) |
| FRD          | Feature requirements and public interface  | [FRD.md](FRD.md) |
| ROADMAP      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../../ARCHITECTURE.md) |
