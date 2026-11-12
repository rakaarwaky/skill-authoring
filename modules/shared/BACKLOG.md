# BACKLOG — skills design shared

FRD: none
Architecture: [ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
State: root § State Definitions
Health: root § State Definitions
Last Updated: 2026-11-04

## Progress Overview

`skills/skill-authoring/skill-design/modules/shared` holds the
skill-design shared kernel: taxonomy value objects, skill
request/response envelopes, trace VOs, taxonomy constants, and
trace-collection defaults. Both required doc files (DATA.md +
BACKLOG.md) are present and current.

## Backlog Status

### DT-SHARED-001: Skill value objects

| Aspect      | Detail      |
| ----------- | ----------- |
| State       | Done        |
| Done        | Implemented |
| In Progress | None        |
| Risk        | None        |
| Updated     | 2026-11-04  |

`SkillContent`, `SkillDescription`, `ErrorMessage`, `DiffLines`,
`SkillsJsonPayload`, `SkillRecord` defined in `taxonomy_design_vo.py`;
verified by shared tests at `767b18672a0c0abd92f7225f267478db8271c334`.

### DT-SHARED-002: Trace value objects

| Aspect      | Detail      |
| ----------- | ----------- |
| State       | Done        |
| Done        | Implemented |
| In Progress | None        |
| Risk        | None        |
| Updated     | 2026-11-04  |

`GrokHome`, `TraceRunDir`, `TraceRunName`, `TraceStateStatus`,
`TraceSessionRecord`, `SkillUsageItem`, `PhraseRow`, `TraceDecision`,
`ScanResult`, `TraceStateDispatchResult` defined in
`taxonomy_design_vo.py`; verified by shared tests.

### DT-SHARED-003: Skill request and response envelopes

| Aspect      | Detail      |
| ----------- | ----------- |
| State       | Done        |
| Done        | Implemented |
| In Progress | None        |
| Risk        | None        |
| Updated     | 2026-11-04  |

`SkillQuery`, `SkillsRoot`, `SkillsOp`, `SkillsRequest`,
`SkillsExitCode`, `SkillsResult` defined in
`taxonomy_design_request.py` and `taxonomy_design_response.py`; verified
by shared tests.

### DT-SHARED-004: Skill taxonomy constants

| Aspect      | Detail      |
| ----------- | ----------- |
| State       | Done        |
| Done        | Implemented |
| In Progress | None        |
| Risk        | None        |
| Updated     | 2026-11-04  |

`NAME_RE`, `MAX_DESCRIPTION_LEN`, `IGNORED_CATEGORY_DIRS`,
`ARCHIVE_DIRNAME`, `CATALOG_FILENAME` defined in
`taxonomy_design_constant.py`; verified by shared tests.

### DT-SHARED-005: Trace collection defaults

| Aspect      | Detail      |
| ----------- | ----------- |
| State       | Done        |
| Done        | Implemented |
| In Progress | None        |
| Risk        | None        |
| Updated     | 2026-11-04  |

`TRACE_COLLECT_SINCE_LAST`, `TRACE_COLLECT_MIN_TURNS`,
`TRACE_COLLECT_LIMIT_UNLIMITED`, `TRACE_COLLECT_WRITE_JSON_ALWAYS`,
`TRACE_COLLECT_RUN_DIR_PATTERN` defined in
`taxonomy_design_constant.py`; verified by shared tests.

## Reference

| Artifact     | Purpose                                    |
| ------------ | ------------------------------------------ |
| PRD          | Business goals and scope                   |
| FRD          | Functional requirements                    |
| Data         | Data requirements and shared value objects |
| Roadmap      | Timeline, phasing, and dependencies        |
| Architecture | System boundaries, tech stack, and infra   |

Links: [PRD.md](../../../../../PRD.md), [FRD.md](FRD.md),
[DATA.md](DATA.md), [ROADMAP.md](../../../../../ROADMAP.md),
[ARCHITECTURE.md](../../../../../ARCHITECTURE.md)
