# FRD — storage

## Feature Overview

The storage feature sits in the agent layer and is called by the surface
and root CLI through the storage aggregate contract. It orchestrates three
capabilities — archiver, exporter, restore — and routes each storage op to
the matching capability. The agent performs no filesystem I/O; all I/O is
delegated to the capabilities.

## Functional Requirements

### FR-storage-001: Archive a live skill

**Description:**
The feature shall move a live skill from its category directory into the
archive directory under `_archive/`, resolving the skill's source
directory and placing it at `_archive/<category>/<skill>/`. No filesystem
state is held by the agent; the archiver capability performs the move.

#### Business Logic

- The archiver shall resolve the skill's source directory under the pack
  root.
- The archive destination shall be `_archive/<category>/<skill>/`.
- The archiver shall reject an archive whose destination already exists.
- Every computed destination shall be asserted to remain inside the pack
  root before any write, and re-checked at apply time.

#### Edge Cases

- An archive destination that already exists shall produce a conflict
  error and overwrite nothing.
- A computed destination that escapes the pack root shall fail closed
  before writing.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | skill, root |
| **Output** | Archive destination path |
| **Protocol** | ISkillsArchiverProtocol |
| **Method** | plan_archive, apply_archive |
| **Event** | None |
| **Error** | MutationConflictError, SkillsUsageError |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| An existing skill | The archiver is invoked | The skill is moved under `_archive/<category>/<skill>/` |
| The archive destination already exists | The archiver is invoked | A conflict error is raised and nothing is overwritten |
| The computed destination escapes the pack root | The archiver is invoked | The operation fails closed with a containment error |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Archive containment violation rate | 0 % |

### FR-storage-002: Restore an archived skill

**Description:**
The feature shall move an archived skill from
`_archive/<category>/<skill>/` back to its live category directory,
re-anchoring the skill after the move.

#### Business Logic

- Restore shall move an archived skill from `_archive/<category>/<skill>/`
  back to its live category directory.
- Restore shall re-anchor the skill after moving it.

#### Edge Cases

- A skill that is not archived shall produce a not-found error.
- A restore destination that already exists shall produce a conflict error
  and overwrite nothing.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | skill, root |
| **Output** | Restore result |
| **Protocol** | ISkillsRestoreProtocol |
| **Method** | restore |
| **Event** | None |
| **Error** | SkillNotFoundError, MutationConflictError |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| An archived skill exists | Restore is invoked | The skill is restored to its live category directory |
| The skill is not archived | Restore is invoked | A not-found error is raised |
| The restore destination already exists | Restore is invoked | A conflict error is raised and nothing is overwritten |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Restore success rate | 100 % |

### FR-storage-003: Export a skill pack to a single Markdown document

**Description:**
The feature shall export a skill folder into a single Markdown document
saved at `.export/<namaskill>.md` under the pack root, concatenating the
skill's key files (`SKILL.md`, `reference/`, `template/`, `scripts/`,
`README.md`) separated by relative path headings.

#### Business Logic

- The exporter shall resolve the skill directory under the pack root.
- The exporter shall read `SKILL.md`, files under `reference/`, `template/`,
  `scripts/`, and `README.md` if present.
- Each file section shall begin with `## <relative-path>` heading.
- The output shall be written to `.export/<namaskill>.md` under the pack
  root.
- Containment inside the pack root shall be asserted before writing.

#### Edge Cases

- A nonexistent skill shall raise `SkillNotFoundError`.
- Missing optional subdirectories or README.md shall be skipped gracefully.
- Destination outside the pack root shall fail closed with a containment
  error.

#### Technical Specification

| Aspect | Detail |
|--------|--------|
| **Input** | skill, root |
| **Output** | Path of exported Markdown file |
| **Protocol** | ISkillsExportProtocol |
| **Method** | export |
| **Event** | None |
| **Error** | SkillNotFoundError, SkillsUsageError, OSError |

#### Test

| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| A valid skill exists | Exporter is invoked | A single concatenated `.md` is written to `.export/<skill>.md` |
| The skill does not exist | Exporter is invoked | `SkillNotFoundError` is raised |
| A computed path escapes the pack root | Exporter is invoked | `SkillsUsageError` containment error is raised |

#### Metric

| Target Metric | Value |
|---------------|-------|
| Export success rate | 100 % |

## Public Interface

| Aspect    | Detail                  |
| --------- | ----------------------- |
| Agent     | SkillsStorageAgent      |
| Aggregate | ISkillsStorageAggregate |
| Method    | execute                 |
| Request   | StorageRequest          |
| Response  | StorageResponse         |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals and scope                        | [PRD.md](../../../../../PRD.md) |
| Backlog      | Task tracking and implementation status         | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../../../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |