# BACKLOG — observability

FRD: [FRD.md](FRD.md)
Architecture: [ARCHITECTURE.md](../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-09

## Progress Overview

The observability feature owns the per-skill telemetry side:
`SkillsTelemetry` (seed, reanchor, curated report, views bump), and
`SkillsPhraseScan` (session scan + phrase mining). `ObservabilityAgent`
dispatches `usage`/`traces` behind `IObservabilityAggregate`. Every
requirement in [FRD.md](FRD.md) is implemented and wired into
`modules/root_skills_container.py` and
`modules/observability/src/root_observability_container.py`; nothing is
in progress.

## Backlog Status

### FR-observability-002: Bump and report per-skill telemetry

| Aspect        | Detail     |
| ------------- | ---------- |
| State         | Done       |
| Done          | Wired      |
| In Progress   | None       |
| Risk          | None       |
| Updated       | 2026-11-09 |

`SkillsTelemetry.seed_record_if_missing`, `reanchor_clock`,
`curated_report`, and `view` manage the per-skill `.usage.json` sidecar.
The agent routes `SkillsOp.USAGE` to it via `_execute_usage`.

### FR-observability-003: Scan sessions and mine repeated phrases

| Aspect        | Detail     |
| ------------- | ---------- |
| State         | Done       |
| Done          | Wired      |
| In Progress   | None       |
| Risk          | None       |
| Updated       | 2026-11-09 |

`SkillsPhraseScan.scan_sessions` walks `$GROK_HOME/sessions` with a
hardcoded weekly (7-day) window — only sessions updated within the last
7 days are kept — and `build_phrases` mines repeated exact prompts,
stems, and instruction lines. No day window, `since_last`, minimum-turn
filter, limit, or `min_sessions` flag is exposed to the caller — every
tunable is hardcoded inside the capability. The agent routes
`SkillsOp.TRACES` to it via `_execute_phrases`.

## Reference

| Artifact     | Purpose                        |
| ------------ | ------------------------------ |
| PRD          | Business goals and scope       |
| FRD          | Feature requirements           |
| ROADMAP      | Timeline and dependencies      |
| Architecture | Boundaries, stack, and infra   |

Links: [PRD.md](../../PRD.md), [FRD.md](FRD.md),
[ROADMAP.md](../../ROADMAP.md), [ARCHITECTURE.md](../../../ARCHITECTURE.md)
