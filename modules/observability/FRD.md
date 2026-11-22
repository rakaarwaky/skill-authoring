# FRD — observability

## Feature Overview

The observability feature sits in the agent layer and answers the audit and
telemetry questions about the skill pack: who changed what, how often each
skill is viewed, and which phrases repeat across sessions. It owns three
capabilities — SkillsLedger, SkillsTelemetry, and SkillsPhraseScan — and one
merged agent: `ObservabilityAgent` dispatches the `LEDGER`, `USAGE`, and
`TRACES` ops behind `IObservabilityAggregate`. The agent performs no filesystem
I/O itself; all I/O is delegated to the capabilities.

## Functional Requirements

### FR-observability-001: Append and read the audit ledger

**Description:** `ObservabilityAgent.execute(request)` with `op=LEDGER` shall
route to the ledger capability to append one content-addressed entry to the
append-only JSONL audit ledger and return the stored entry to the caller.

#### Business Logic

- `ledger_append` sets a UUID id, ISO timestamp, actor (from lifecycle config or
  a default actor), and defaults for action, skill, before, after, and evidence.
- Content-addressed blobs are copied into the blob store keyed by sha256 when a
  valid digest references a readable source file.
- A blob store copy failure is logged as a warning; the append still proceeds.
- `ledger_read` parses the JSONL file line by line, skipping blank or corrupt
  lines, and returns up to `limit` entries in insertion order.
- A `SkillsError` raised by the ledger is caught by the agent and mapped to a
  `SkillsResult` carrying the error's exit code and message.

#### Edge Cases

- Missing ledger file → `ledger_read` returns an empty tuple.
- Invalid sha256 digest in a manifest entry → `SkillsUsageError` raised at
  append time.
- A blob store copy failure → logged warning, append still proceeds.

#### Technical Specification

| Aspect       | Detail                                                    |
| ------------ | --------------------------------------------------------- |
| **Input**    | `SkillsRequest(op=LEDGER, query, flags, root?)`. Source: surface / root CLI. |
| **Output**   | `SkillsResult(ok, op, exit_code, message, root?)`. Destination: surface / root CLI. |
| **Protocol** | `ISkillsLedgerProtocol`                                   |
| **Method**   | `ledger_append`                                           |
| **Event**    | None                                                      |
| **Error**    | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2              |

#### Test

| Context                              | When Action                          | Then Observable Result                            |
| ------------------------------------ | ------------------------------------ | ------------------------------------------------- |
| A valid entry is appended            | The caller invokes `LEDGER` append   | `ok=True`; entry stored with defaults filled      |
| The ledger file has existing entries | The caller invokes `LEDGER` append   | The new entry is appended after the existing ones |
| The ledger file does not exist       | The caller invokes `LEDGER` append   | A new ledger file is created                      |
| An invalid sha256 digest is supplied | The caller invokes `LEDGER` append   | `SkillsUsageError` raised; `USAGE_ERROR` returned |

#### Metric

| Target Metric       | Value |
| ------------------- | ----- |
| Append p95 latency  | 10 ms |
| Append accuracy     | 100 % |

### FR-observability-002: Bump and report per-skill telemetry

**Description:** `ObservabilityAgent.execute(request)` with `op=USAGE` shall
route to the telemetry capability to seed a baseline record if missing, reanchor
the activity clock, emit the curated per-skill report, and bump the views
counter.

#### Business Logic

- `seed_record_if_missing` writes a baseline record only when none exists for
  the skill; otherwise returns without writing.
- `reanchor_clock` resets `last_activity_at` and `activity_window_start` to now.
- `curated_report` returns one telemetry row per skill, sorted by state.
- `view` bumps the `views` counter for a skill by 1.
- A missing skill directory results in a no-op (no write).

#### Edge Cases

- Skill directory not found → no-op, no error propagated.
- Corrupt sidecar JSON → treated as missing; baseline written.

#### Technical Specification

| Aspect       | Detail                                                    |
| ------------ | --------------------------------------------------------- |
| **Input**    | `SkillsRequest(op=USAGE, flags, root?)`. Source: surface / root CLI. |
| **Output**   | `SkillsResult(ok, op, exit_code, message, records, root?)`. Destination: surface / root CLI. |
| **Protocol** | `ISkillsTelemetryProtocol`                                |
| **Method**   | `seed_record_if_missing`, `reanchor_clock`, `curated_report`, `view` |
| **Event**    | None                                                      |
| **Error**    | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2              |

#### Test

| Context                                  | When Action                     | Then Observable Result                          |
| ---------------------------------------- | ------------------------------- | ----------------------------------------------- |
| A skill has no telemetry record            | The caller invokes `USAGE` seed | Baseline record written                         |
| A skill already has a telemetry record     | The caller invokes `USAGE` seed | No write; record unchanged                      |
| The caller requests the curated report     | The caller invokes `USAGE` report | One row per skill, sorted by state            |
| The caller requests a view bump            | The caller invokes `USAGE` view | `views` counter incremented by 1                |
| The skill directory does not exist         | The caller invokes `USAGE` seed | No write; no error raised                       |

#### Metric

| Target Metric       | Value  |
| ------------------- | ------ |
| Report p95 latency  | 50 ms  |
| Row accuracy        | 100 %  |

### FR-observability-003: Scan sessions and mine repeated phrases

**Description:** `ObservabilityAgent.execute(request)` with `op=TRACES` and
`flags['traces_action']='phrases'` shall route to the phrase-scan capability to
scan `$GROK_HOME/sessions`, build session records, and mine repeated exact
prompts, stems, and instruction lines.

#### Business Logic

- `scan_sessions` walks `$GROK_HOME/sessions` with a hardcoded weekly (7-day)
  window — only sessions updated within the last 7 days are kept — skips
  excluded cwds, smoke-test and below-1-turn sessions, and writes session
  records plus a `manifest.json` into `run_dir`. No day window override,
  minimum-turn filter, limit, or watermark is exposed to the caller — every
  tunable is hardcoded inside the capability.
- `build_phrases` reads session records from `run_dir` and groups repeated
  exact prompts (>=2 sessions, hardcoded), stems (>=3 sessions), and
  instruction lines (>=3 sessions).
- Single-turn prompts repeated >=3 times are dropped as noise.

#### Edge Cases

- Missing `chat_history.jsonl` in a session → session skipped.
- Sessions with no human turns → dropped from kept records.
- `run_dir` missing → created with `tempfile.mkdtemp`.

#### Technical Specification

| Aspect       | Detail                                                    |
| ------------ | --------------------------------------------------------- |
| **Input**    | `SkillsRequest(op=TRACES, flags: grok_home?, run_dir?)`. Source: surface / root CLI. |
| **Output**   | `SkillsResult(ok, op, exit_code, message, phrases_exact, phrases_stems, phrases_lines, scan_summary, root?)`. Destination: surface / root CLI. |
| **Protocol** | `ISkillsTracesProtocol`                                   |
| **Method**   | `scan_sessions`, `build_phrases`                          |
| **Event**    | None                                                      |
| **Error**    | `CLEAN` 0, `ISSUES_FOUND` 1, `USAGE_ERROR` 2              |

#### Test

| Context                                | When Action                                      | Then Observable Result                       |
| -------------------------------------- | ------------------------------------------------ | -------------------------------------------- |
| Sessions exist with repeated prompts   | The caller invokes `TRACES` with phrases action  | `ok=True`; exact/stem/line rows populated    |
| An unknown traces action is supplied   | The caller invokes `TRACES` with unknown action  | `ok=False`; exit code `USAGE_ERROR`          |
| A session has no `chat_history.jsonl`  | The caller invokes `TRACES`                      | Session skipped; no crash                    |

#### Metric

| Target Metric       | Value  |
| ------------------- | ------ |
| Scan p95 latency    | 500 ms |
| Phrase accuracy     | 100 %  |

## Public Interface

| Aspect      | Detail               |
| ----------- | -------------------- |
| Agent       | `ObservabilityAgent` |
| Aggregate   | `IObservabilityAggregate` |
| Method      | `execute`            |
| Request     | `SkillsRequest`      |
| Response    | `SkillsResult`       |

## Reference

| Artifact       | Purpose                               | Link                                                |
| -------------- | ------------------------------------- | --------------------------------------------------- |
| PRD            | Business goals and scope              | [PRD.md](../../PRD.md)                              |
| Backlog        | Task tracking and implementation status | [BACKLOG.md](BACKLOG.md)                          |
| Roadmap        | Timeline, phasing, and dependencies   | [ROADMAP.md](../../ROADMAP.md)                      |
| Architecture   | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../ARCHITECTURE.md)      |