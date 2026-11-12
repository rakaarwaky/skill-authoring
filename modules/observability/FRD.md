# FRD — observability

## Feature Overview

The observability feature sits in the agent layer and answers the audit and
telemetry questions about the skill pack: who changed what, how often each
skill is viewed, and which phrases repeat across sessions. It owns three
capabilities — SkillsLedger, SkillsTelemetry, and SkillsPhraseScan — and one
merged agent: ObservabilityAgent dispatches ledger/usage/traces behind
IObservabilityAggregate. The agent performs no filesystem I/O itself; all I/O
is delegated to the capabilities.

## Functional Requirements

### FR-observability-001: Append and read the audit ledger

**Description:** ObservabilityAgent.execute(request) with op=LEDGER shall route
to SkillsLedger.ledger_append to append one content-addressed entry to the
append-only JSONL audit ledger, and to ledger_read to return up to limit most
recent entries.

#### Business Logic

- ledger_append sets a UUID id, ISO timestamp, actor (from lifecycle config or a default actor), and defaults for action, skill, before, after, and evidence.
- Content-addressed blobs are copied into the blob store keyed by sha256 when a valid digest references a readable source file.
- ledger_read parses the JSONL file line by line, skipping blank or corrupt lines, and returns up to limit entries in insertion order.
- A SkillsError raised by the ledger is caught by the agent and mapped to an ObservabilityResult carrying the error's exit code and message.

#### Edge Cases

- Missing ledger file → ledger_read returns an empty tuple.
- Invalid sha256 digest in a manifest entry → SkillsUsageError raised at append time.
- Blob store copy failure → logged warning, append still proceeds.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | SkillsRequest(op=LEDGER, flags, root?) |
| **Output** | SkillsResult(ok, op, exit_code, message, root?) |
| **Protocol** | ISkillsLedgerProtocol |
| **Method** | ledger_append / ledger_read |
| **Event** | none |
| **Error** | CLEAN 0, ISSUES_FOUND 1, USAGE_ERROR 2 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| ledger_append valid entry | The caller invokes LEDGER append | ok=True; defaults stored |
| ledger_read existing ledger | The caller invokes LEDGER read | Up to limit entries in order |
| ledger_read missing ledger | The caller invokes LEDGER read | Empty tuple returned |
| Invalid sha256 digest | The caller invokes LEDGER append | SkillsUsageError; mapped to USAGE_ERROR |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Append Latency | < 10ms |
| Read Accuracy | 100% |

### FR-observability-002: Bump and report per-skill telemetry

**Description:** ObservabilityAgent.execute(request) with op=USAGE shall route
to SkillsTelemetry to seed a baseline record if missing, reanchor the clock,
emit the curated per-skill report, and bump the views counter.

#### Business Logic

- seed_record_if_missing writes a baseline record only when none exists for the skill; otherwise returns without writing.
- reanchor_clock resets last_activity_at and activity_window_start to now.
- curated_report returns one telemetry row per skill, sorted by skill name.
- view bumps the views counter for a skill.
- A missing skill directory results in a no-op (no write).

#### Edge Cases

- Skill directory not found → no-op, no error propagated.
- Corrupt sidecar JSON → treated as missing; baseline written.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | SkillsRequest(op=USAGE, flags, root?) |
| **Output** | SkillsResult(ok, op, exit_code, message) |
| **Protocol** | ISkillsTelemetryProtocol |
| **Method** | seed_record_if_missing, reanchor_clock, curated_report, view |
| **Event** | none |
| **Error** | CLEAN 0, ISSUES_FOUND 1, USAGE_ERROR 2 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Seed for a skill with no record | The caller invokes USAGE | Baseline record written |
| Seed for a skill with existing record | The caller invokes USAGE | No write; record unchanged |
| Curated report | The caller invokes USAGE | One telemetry row per skill, sorted |
| View bump | The caller invokes USAGE | Views counter incremented by 1 |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Report Latency | < 50ms |
| Row Accuracy | 100% |

### FR-observability-003: Scan sessions and mine repeated phrases

**Description:** ObservabilityAgent.execute(request) with op=TRACES and
flags['traces_action']='phrases' shall route to SkillsPhraseScan to scan
$GROK_HOME/sessions, build session records, and mine repeated exact prompts,
stems, and instruction lines.

#### Business Logic

- scan_sessions walks $GROK_HOME/sessions, skips excluded cwds and smoke-test sessions, and writes session records plus a manifest.json into run_dir.
- build_phrases reads session records from run_dir and groups repeated exact prompts (>=2 sessions), stems (>=3 sessions), and instruction lines (>=3 sessions).
- Single-turn prompts repeated >=3 times are dropped as noise.

#### Edge Cases

- Missing chat_history.jsonl in a session → session skipped.
- Empty or below min_turns sessions → dropped from kept records.
- run_dir missing → created with tempfile.mkdtemp.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | SkillsRequest(op=TRACES, flags) |
| **Output** | SkillsResult(ok, op, exit_code, message, phrases, summary) |
| **Protocol** | ISkillsTracesProtocol |
| **Method** | scan_sessions, build_phrases |
| **Event** | none |
| **Error** | CLEAN 0, ISSUES_FOUND 1, USAGE_ERROR 2 |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Valid phrase scan | The caller invokes TRACES with phrases action | ok=True; prompts/stems/lines populated |
| Unknown traces action | The caller invokes TRACES with unknown action | ok=False; exit code USAGE_ERROR |
| Missing chat_history.jsonl | The caller invokes TRACES | Session skipped, no crash |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Scan Latency | < 500ms |
| Phrase Accuracy | 100% |

## Public Interface

| Aspect | Detail |
|--------|--------|
| Agent | ObservabilityAgent |
| Aggregate | IObservabilityAggregate |
| Method | execute |
| Request | SkillsRequest |
| Response | SkillsResult |

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | Business goals and scope | [PRD.md](../../PRD.md) |
| Backlog | Task tracking and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap | Timeline, phasing, and dependencies | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../../ARCHITECTURE.md) |
