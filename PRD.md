# PRD — Skill Authoring

## Project Overview

Skill Authoring is the skill-authoring skill that keeps the skill tree clean, correct, and consolidated. It reads agent `SKILL.md` skill directories and runs one of three modes per invocation: `--create` builds a publishable `SKILL.md` plus its `references/` from a described job, `--improve` audits an existing skill against the shared lint standard and applies the repair edit recipe, and `--prune` collapses duplicate or same-purpose skills into one folder and archives the dropped duplicates. Every fact in a skill lives once, in a single authoritative home; every flag and mode term stays in lockstep across `SKILL.md` and its reference files. The skill exists so that AI coding agents (GrokBuild via Orca, Hermes, and others) always work from skill bodies that invoke correctly, carry no dangling refs, and contain no overlapping folders.

## Goals

- Author publishable `SKILL.md` files from a described job (`--create`).
- Audit + repair an existing skill's structure, naming, frontmatter, body shape, and dangling refs in one pass (`--improve`).
- Collapse duplicate or same-purpose skills into one consolidated folder (`--prune`).

## Non-Goals

- Running the skill-lint validator outside of `--improve` (use `sac lint` for that).
- Executing the code that a skill describes (skill-design only shapes skill docs).
- Touching any file outside `skills/<category>/`.
- Human accessibility output modes (`--plain`/`--json` for assistive tech); consumers are agents, so agent-readable text + the exit-code contract is the usability bar.

## Target Users

Persona priority: **Skill Maintainer agent** first (bulk consolidation, prune, catalog rebuild), then **Skill Author agent** (single-skill create/improve). The CLI default flows are optimized for the Maintainer.

| Persona     | Need                                           | Current Pain                                      | Desired Outcome                           |
|-------------|------------------------------------------------|---------------------------------------------------|-------------------------------------------|
| Skill maintainer agent (primary) | Bulk consolidate overlapping skill folders, prune duplicates, keep the catalog drift-free | Duplicate folders with same purpose/tooling; manual catalog rebuilds | One `sac discover` + `sac move`/`sac archive` + `sac catalog` flow |
| Skill author| Publish a new skill body that follows the lint standard | Writing frontmatter/body shape by hand, missing keys | One `SKILL.md` + `references/` that passes `sac lint` |
| Skill owner | Repair an existing skill after a lint audit   | Hunting dangling refs and shape drift by hand     | A single `sac improve` run fixes all |
| Pack maintainer | Consolidate overlapping skill folders      | Duplicate folders with same purpose/tooling       | One folder, duplicates archived to `_archive/` |

## Scope

### In Scope

- The three invocation modes `--create`, `--improve`, `--prune`.
- Mandatory frontmatter keys `name`, `description`, `when-to-use`, `argument-hint`.
- The body shape: exactly one `# Title`, one `## Rules`, one `## Routing`.
- Reference files under `references/` and optional `scripts/<file>`.
- The safety model: `--dry-run` report-only, destructive actions to `_archive/`, rollback via snapshot SHA.

### Out of Scope

- The `sac lint` validator itself (owned by the lint-arwaky layer).
- The trace-pipeline (`skill-traces`) and its `usage.json`/`phrases.json`.
- Any runtime agent execution of skill content.

---

## Project Requirements

### PR-SKILLDESIGN-001: cli
<!-- Tier P0: entry -001 is always P0. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | Describe a job and get a complete `SKILL.md` | I don't write frontmatter or body shape by hand | `sac lint` passes on first run |

#### Proposed Solution

The `--create` path copies `template/skill.md` (registered in `template/template.md`), fills the four mandatory frontmatter keys, writes exactly three body sections (`# Title`, `## Rules`, `## Routing`), and creates each reference file from its canonical template. A completion grep on the body shape plus `sac lint` confirms publication readiness.

#### Main User Flow

1. User invokes `--create <skills path> [--dry-run]`.
2. Skill-design reads `template/template.md` and `template/skill.md`.
3. It writes the new `SKILL.md` + `references/` under `<category>/<skill>/`.
4. It runs `sac lint` on the new folder and reports pass/fail.

### PR-SKILLDESIGN-002: design
<!-- Tier P1: the first P1 entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill owner | Run audit + repair in one pass | I don't hunt dangling refs manually | The skill passes every validator rule |

#### Proposed Solution

`--improve` runs the full audit-then-improve sequence against `references/improve/step-4-validator-catalog.md`: checks structure, naming, frontmatter, body shape, and dangling refs to the lint standard, then applies the edit recipe. Every flagged issue is fixed; a snapshot SHA is recorded in the commit message for rollback.

#### Main User Flow

1. User invokes `--improve <skills path> [--dry-run]`.
2. Skill-design audits the skill against the validator rule catalog.
3. It applies every fix and records the snapshot SHA.
4. It re-runs `sac lint` and reports the result.

### PR-SKILLDESIGN-003: discovery
<!-- Tier P2: the first P2 entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Pack maintainer | Merge duplicate or same-purpose skill folders | The tree stops growing redundant skills | One canonical folder per purpose |

#### Proposed Solution

`--prune` reads every skill's `description:` and `body`, merges skills that duplicate, share a bounded purpose, or share tooling into one consolidated folder, and archives the dropped duplicates into `_archive/` first (permanent delete only with `--hard-delete`).

#### Main User Flow

1. User invokes `--prune <category or whole tree> [--dry-run]`.
2. Skill-design reads every `SKILL.md` description and body.
3. It identifies overlap and consolidates into one folder.
4. Dropped duplicates move to `_archive/`; the report lists every merge.

### PR-SKILLDESIGN-004: governance
<!-- Tier P2: governance entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill owner | Lock, pin, and move skills | Skills can be protected and relocated | Governance capability keeps the tree stable |

#### Proposed Solution

The locker/piner/mover capabilities expose lock, pin, and move verbs for skill directories. The governance feature implements `ISkillsGovernanceAggregate` and wires them into `root_governance_container.py`.

#### Main User Flow

1. User invokes `--governance <lock|pin|move>`.
2. Skill-design reads the skill's sidecar record.
3. It applies the requested mutation and records the new state.

### PR-SKILLDESIGN-005: maintenance
<!-- Tier P2: maintenance entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill owner | Prune idle skills past a TTL | The pack stops retaining dead skills | Maintenance feature auto-archives idle skills |

#### Proposed Solution

The prune/purge capabilities archive idle skills past `archive_after_days` and purge archived skills past `archive_ttl_days`. The maintenance feature implements `ISkillsMaintenanceAggregate` and wires them into `root_maintenance_container.py`.

#### Main User Flow

1. User invokes `--maintenance prune [--days N]`.
2. Skill-design reads each skill's sidecar record and compares last activity.
3. It archives idle skills and reports pruned/kept lists.

### PR-SKILLDESIGN-006: mcp
<!-- Tier P2: mcp entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Surface operator | Expose skill ops over MCP | Clients can discover and call skills | The mcp surface provides the command router |

#### Proposed Solution

The mcp surface exposes `surface_mcp_command.py` as the command router over the Model Context Protocol. The mcp feature carries DESIGN.md and BACKLOG.md and implements `ISkillsMcpSurface`.

#### Main User Flow

1. Client sends an MCP tool call naming a skill op.
2. The surface router dispatches to the matching aggregate capability.
3. The result returns to the client over MCP.

### PR-SKILLDESIGN-007: observability
<!-- Tier P2: observability entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill owner | Scan sessions and mine phrases | Repeated usage patterns surface | Observability feature traces and telemetry |

#### Proposed Solution

The observability feature implements ledger, telemetry, and traces capabilities behind `IObservabilityAggregate`, wired into `root_observability_container.py`. It imports `taxonomy_observability_constant` and `taxonomy_observability_error` for domain types.

#### Main User Flow

1. User invokes `--observability scan [--days N]`.
2. Skill-design walks `$GROK_HOME/sessions` and returns a compact scan outcome.
3. It mines repeated phrases and writes them to the report.

### PR-SKILLDESIGN-008: shared
<!-- Tier P2: shared entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Pack maintainer | Keep shared domain types in one place | Every feature imports from shared | The shared kernel holds contract+taxonomy+utility |

#### Proposed Solution

The shared folder carries `contract_*`, `taxonomy_*`, and `utility_*` files per domain (design, discovery, governance, maintenance, observability, storage), plus DATA.md and BACKLOG.md. Every crate folder carries its taxonomy types.

#### Main User Flow

1. Feature capability imports its domain taxonomy from `shared.src.<domain>`.
2. The shared module exposes only stateless pure functions and domain types.
3. No cross-domain imports leak into shared.

### PR-SKILLDESIGN-009: storage
<!-- Tier P2: storage entry. -->

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill owner | Archive, backup, restore, rollback skills | Skill state survives destructive ops | Storage feature implements persistence verbs |

#### Proposed Solution

The storage feature implements archiver, backup, bootstrap, restore, and rollback capabilities behind `ISkillsStorageAggregate`, wired into `root_storage_container.py`. Each capability carries an FRD.md and BACKLOG.md.

#### Main User Flow

1. User invokes `--storage archive <skill>`.
2. Skill-design moves the skill to the archive tree with a manifest record.
3. It verifies blob digests and reports success.

## Reference

| Artifact     | Purpose                                          | Link |
|--------------|--------------------------------------------------|------|
| PRD          | Business goals and scope                         | [PRD.md](PRD.md) |
| Backlog      | What is true now, with evidence                  | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies              | [ROADMAP.md](ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra         | [ARCHITECTURE.md](ARCHITECTURE.md) |
