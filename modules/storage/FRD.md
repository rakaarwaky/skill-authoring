# FRD — storage

## Feature Overview

The storage feature sits in the agent layer and is called by the surface
and root CLI through the `ISkillsStorageAggregate` contract. It orchestrates
three capabilities — archiver, exporter, restore — and routes each storage op
to the matching capability. The agent performs no filesystem I/O; all I/O is
delegated to the capabilities.

## Functional Requirements

### FR-storage-001: Archive a live skill

**Description:** `SkillsStorageAgent.execute(request)` with `verb=ARCHIVE`
shall route to the archiver capability to move a live skill from its category
directory into the home-based archive tree at
`~/.agents/skills/.archive/<category>/<skill>/`. The archiver resolves the
skill's source directory, plans the move, and applies it on confirmation. No
filesystem state is held by the agent; the archiver capability performs the
move.

#### Business Logic

- The archiver shall resolve the skill's source directory under the pack root.
- The archive destination shall be
  `~/.agents/skills/.archive/<category>/<skill>/`.
- The archiver shall reject an archive whose destination already exists.
- Every computed destination shall be asserted to remain inside the archive
  root before any write, and re-checked at apply time.

#### Edge Cases

- An archive destination that already exists shall produce a
  `MutationConflictError` and overwrite nothing.
- A computed destination that escapes the archive root shall fail closed
  before writing.

#### Technical Specification

| Aspect       | Detail                                                    |
| ------------ | --------------------------------------------------------- |
| **Input**    | `StorageRequest(verb=ARCHIVE, query, root?)`. Source: surface / root CLI. |
| **Output**   | `StorageResponse(ok, verb, exit_code, message, root?)`. Destination: surface / root CLI. |
| **Protocol** | `ISkillsArchiverProtocol`                                 |
| **Method**   | `plan_archive`, `apply_archive`                           |
| **Event**    | None                                                      |
| **Error**    | `MutationConflictError` 1, `SkillsUsageError` 2           |

#### Test

| Context                               | When Action                        | Then Observable Result                                              |
| ------------------------------------- | ---------------------------------- | ------------------------------------------------------------------ |
| An existing skill                     | The archiver is invoked            | The skill is moved under `~/.agents/skills/.archive/<category>/<skill>/` |
| The archive destination already exists | The archiver is invoked           | A `MutationConflictError` is raised and nothing is overwritten     |
| The computed destination escapes the archive root | The archiver is invoked | The operation fails closed with a containment error                |

#### Metric

| Target Metric                        | Value |
| ------------------------------------ | ----- |
| Archive containment violation rate   | 0 %   |

### FR-storage-002: Restore an archived skill

**Description:** `SkillsStorageAgent.execute(request)` with `verb=RESTORE`
shall route to the restore capability to move an archived skill from
`~/.agents/skills/.archive/<category>/<skill>/` back to its live category
directory, re-anchoring the skill after the move.

#### Business Logic

- Restore shall move an archived skill from
  `~/.agents/skills/.archive/<category>/<skill>/` back to its live category
  directory.
- Restore shall re-anchor the skill after moving it.

#### Edge Cases

- A skill that is not archived shall produce a `SkillNotFoundError`.
- A restore destination that already exists shall produce a
  `MutationConflictError` and overwrite nothing.

#### Technical Specification

| Aspect       | Detail                                                    |
| ------------ | --------------------------------------------------------- |
| **Input**    | `StorageRequest(verb=RESTORE, query, root?)`. Source: surface / root CLI. |
| **Output**   | `StorageResponse(ok, verb, exit_code, message, root?)`. Destination: surface / root CLI. |
| **Protocol** | `ISkillsRestoreProtocol`                                  |
| **Method**   | `restore`                                                 |
| **Event**    | None                                                      |
| **Error**    | `SkillNotFoundError` 2, `MutationConflictError` 1         |

#### Test

| Context                              | When Action            | Then Observable Result                                   |
| ------------------------------------ | ---------------------- | -------------------------------------------------------- |
| An archived skill exists             | Restore is invoked     | The skill is restored to its live category directory     |
| The skill is not archived            | Restore is invoked     | A `SkillNotFoundError` is raised                         |
| The restore destination already exists | Restore is invoked   | A `MutationConflictError` is raised and nothing is overwritten |

#### Metric

| Target Metric         | Value |
| --------------------- | ----- |
| Restore success rate  | 100 % |

### FR-storage-003: Export a skill pack to a single Markdown document

**Description:** `SkillsStorageAgent.execute(request)` with `verb=EXPORT`
shall route to the exporter capability to export a skill folder into a single
Markdown document saved at `~/.agents/skills/.export/<skill-name>.md`,
concatenating the skill's key files (`SKILL.md`, `references/`, `templates/`,
`scripts/`, `README.md`) separated by relative-path headings.

#### Business Logic

- The exporter shall resolve the skill directory under the pack root.
- The exporter shall read `SKILL.md`, files under `references/`, `templates/`,
  `scripts/`, and `README.md` if present.
- Each file section shall begin with a `## <relative-path>` heading.
- The output shall be written to `~/.agents/skills/.export/<skill-name>.md`.
- The export directory shall be created if it does not exist.

#### Edge Cases

- A nonexistent skill shall raise `SkillNotFoundError`.
- Missing optional subdirectories or `README.md` shall be skipped gracefully.
- A skill directory that exists but has no `SKILL.md` shall raise
  `SkillNotFoundError`.

#### Technical Specification

| Aspect       | Detail                                                    |
| ------------ | --------------------------------------------------------- |
| **Input**    | `StorageRequest(verb=EXPORT, query, root?)`. Source: surface / root CLI. |
| **Output**   | `StorageResponse(ok, verb, exit_code, message, root?)`. Destination: surface / root CLI. |
| **Protocol** | `ISkillsExportProtocol`                                   |
| **Method**   | `export`                                                  |
| **Event**    | None                                                      |
| **Error**    | `SkillNotFoundError` 2, `OSError` 1                       |

#### Test

| Context                              | When Action            | Then Observable Result                                          |
| ------------------------------------ | ---------------------- | -------------------------------------------------------------- |
| A valid skill exists                 | Exporter is invoked    | A single concatenated `.md` is written to `~/.agents/skills/.export/<skill-name>.md` |
| The skill does not exist             | Exporter is invoked    | `SkillNotFoundError` is raised                                 |
| Optional subdirectories are missing  | Exporter is invoked    | Export succeeds; only present files are included                |

#### Metric

| Target Metric         | Value |
| --------------------- | ----- |
| Export success rate   | 100 % |

## Public Interface

| Aspect      | Detail                  |
| ----------- | ----------------------- |
| Agent       | `SkillsStorageAgent`    |
| Aggregate   | `ISkillsStorageAggregate` |
| Method      | `execute`               |
| Request     | `StorageRequest`        |
| Response    | `StorageResponse`       |

## Reference

| Artifact       | Purpose                               | Link                                                |
| -------------- | ------------------------------------- | --------------------------------------------------- |
| PRD            | Business goals and scope              | [PRD.md](../../PRD.md)                              |
| Backlog        | Task tracking and implementation status | [BACKLOG.md](BACKLOG.md)                          |
| Roadmap        | Timeline, phasing, and dependencies   | [ROADMAP.md](../../ROADMAP.md)                      |
| Architecture   | System boundaries, tech stack, and infra | [ARCHITECTURE.md](../../ARCHITECTURE.md)      |