# Data — skills design shared

## Data Overview

The skill-design shared layer owns the value objects, constants, and
protocol contracts every skill-design feature layer reads. It holds no
state of its own: the shapes below are pure definitions that the
capability and agent layers consume, so they can be imported upward
without pulling in any I/O.

## Data Requirements

### DT-SHARED-001: Skill value objects

| Type                                                             |
| ---------------------------------------------------------------- |
| `SkillContent`, `SkillDescription`, `ErrorMessage`, `DiffLines`, |
| `SkillsJsonPayload`, `SkillRecord`                               |

Description: the read-side VOs for skill records, raw SKILL.md text,
descriptions, formatted errors, diff-line sequences, and pure-data JSON
skill payloads.

### DT-SHARED-002: Trace value objects

| Type                                                                  |
| --------------------------------------------------------------------- |
| `GrokHome`, `TraceRunDir`, `TraceRunName`, `TraceStateStatus`,        |
| `TraceSessionRecord`, `SkillUsageItem`, `PhraseRow`, `TraceDecision`, |
| `ScanResult`, `TraceStateDispatchResult`                              |

Description: the trace-pipeline value objects produced by scan / usage /
phrases / materialize / state, plus the trace-learning lifecycle status
machine.

### DT-SHARED-003: Skill request and response envelopes

| Type                                                     |
| -------------------------------------------------------- |
| `SkillQuery`, `SkillsRoot`, `SkillsOp`, `SkillsRequest`, |
| `SkillsExitCode`, `SkillsResult`                         |

Description: the input envelope (op, query, root, apply gate) and
response envelope (exit code, records, reports) carried between surface,
agent, and contract layers.

### DT-SHARED-004: Skill taxonomy constants

| Type                                                       |
| ---------------------------------------------------------- |
| `NAME_RE`, `MAX_DESCRIPTION_LEN`, `IGNORED_CATEGORY_DIRS`, |
| `ARCHIVE_DIRNAME`, `CATALOG_FILENAME`                      |

Description: naming budget, layout invariants, category skip set,
archive directory name, and catalog file name.

### DT-SHARED-005: Trace collection defaults

| Type                                                                |
| ------------------------------------------------------------------- |
| `TRACE_COLLECT_SINCE_LAST`, `TRACE_COLLECT_MIN_TURNS`,              |
| `TRACE_COLLECT_LIMIT_UNLIMITED`, `TRACE_COLLECT_WRITE_JSON_ALWAYS`, |
| `TRACE_COLLECT_RUN_DIR_PATTERN`                                     |

Description: skill-traces scan defaults: since-last-run window, minimum
turns, unlimited limit, always-write JSON, and run-dir pattern.

## Reference

| Artifact     | Purpose                                         |
| ------------ | ----------------------------------------------- |
| PRD          | Business goals, user stories, and scope         |
| Backlog      | Task tracking, epics, and implementation status |
| Roadmap      | Timeline, phasing, and dependencies             |
| Architecture | System boundaries, tech stack, and infra        |

Links: [PRD.md](../../../../../PRD.md), [BACKLOG.md](BACKLOG.md),
[ROADMAP.md](../../../../../ROADMAP.md),
[ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
