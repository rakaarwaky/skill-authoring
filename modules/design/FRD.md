# FRD — design

## Feature Overview

The design feature sits in the agent layer and is called by the surface and root
CLI through the design aggregate contract. It orchestrates four capabilities —
creator, adopter, linter, runner — and routes each design-side verb to the
matching capability protocol. The agent performs no filesystem I/O; all I/O is
delegated to the capabilities.

## Functional Requirements

### FR-DESIGN-001: Creator capability contract

**Description:** `SkillsCreator` shall implement `ISkillsCreatorProtocol` and
expose `create_skill` and `create_category`. The capability plans (dry-run) or
applies creation of a new skill SKILL.md or category folder under the skills
root.

#### Business Logic

- `create_skill` with `apply=False` returns a `SkillCreatePlan` without writing;
  with `apply=True` it writes the SKILL.md file.
- `create_category` with `apply=False` returns a `NewCategoryPlan` without
  writing; with `apply=True` it creates the directory and DESCRIPTION.md.
- Every computed destination is asserted to remain inside the skills root at
  plan time and re-checked at apply time, so a symlink created between the two
  phases fails closed instead of writing outside the pack.
- The creator never imports a sibling capability; data crossing capability
  boundaries flows through shared kernel protocols or shared kernel utilities.

#### Edge Cases

- A computed destination outside the skills root at apply time shall fail closed
  and produce no write.
- A missing skill name shall raise an error the agent maps to a `SkillsResult`
  with `ISSUES_FOUND` exit code.

#### Technical Specification

| Aspect         | Detail                                                      |
| -------------- | ----------------------------------------------------------- |
| **Input**      | `create_skill` / `create_category` arguments per protocol   |
| **Output**     | `SkillCreatePlan` / `NewCategoryPlan`                       |
| **Protocol**   | `ISkillsCreatorProtocol`                                    |
| **Method**     | `create_skill`, `create_category`                           |
| **Event**      | none                                                        |
| **Error**      | `OSError`, `SkillsError` subclasses; agent maps to exit     |
|                | codes                                                       |

#### Test

| Context                 | When Action             | Then Observable Result   |
| ----------------------- | ----------------------- | ------------------------ |
| Creator plan with       | `create_skill(apply=F   | `SkillCreatePlan` with   |
| apply=False             | alse)`                  | `apply=False`; no        |
|                         |                         | filesystem write         |
|                         |                         | occurs                   |
| Creator plan with       | `create_skill(apply=T   | SKILL.md file is         |
| apply=True              | rue)`                   | written under the        |
|                         |                         | skills root              |

#### Metric

| Target Metric              | Value   |
| -------------------------- | ------- |
| Out-of-root write rate     | 0 %     |
| Capability contract pass   | 100 %   |

### FR-DESIGN-002: Adopter capability contract

**Description:** `SkillsAdopter` shall implement `ISkillsAdopterProtocol` and
expose `adopt`, marking a skill as agent-managed (`created_by="agent"`).

#### Business Logic (2)

- `adopt` marks the named skill as agent-managed in its sidecar record.
- A missing or empty skill name shall produce a `SkillsResult` with
  `ISSUES_FOUND` exit code and message "Skill name required".
- The adopter never imports a sibling capability.

#### Edge Cases (2)

- An empty or absent skill name on `adopt` shall raise an error the agent maps
  to `ISSUES_FOUND` with "Skill name required".

#### Technical Specification (2)

| Aspect         | Detail                                               |
| -------------- | ---------------------------------------------------- |
| **Input**      | `adopt(skill, root)`                                 |
| **Output**     | `MutationOutcome`                                    |
| **Protocol**   | `ISkillsAdopterProtocol`                             |
| **Method**     | `adopt`                                              |
| **Event**      | none                                                 |
| **Error**      | `SkillsError` subclasses; agent maps to exit codes   |

#### Test (2)

| Context                     | When Action      | Then Observable Result      |
| --------------------------- | ---------------- | --------------------------- |
| Adopt a valid skill         | `adopt(skill)`   | Skill marked                |
|                             |                  | `created_by="agent"`        |
| Adopt with empty skill      | `adopt("")`      | `ISSUES_FOUND` with         |
| name                        |                  | "Skill name required"       |

#### Metric (2)

| Target Metric              | Value   |
| -------------------------- | ------- |
| Capability contract pass   | 100 %   |

### FR-DESIGN-003: Linter capability contract

**Description:** `SkillsLinter` shall implement `ISkillsLinterProtocol` and
expose `lint`, running the combined 13-rule validator plus weed report in one
pass.

#### Business Logic (3)

- `lint` runs the full lint over the root; optionally filters by category.
- Returns a single `LintReport` carrying both issues and weed lines.
- The linter never imports a sibling capability.

#### Edge Cases (3)

- An empty pack returns an empty report with no issues.

#### Technical Specification (3)

| Aspect         | Detail                                               |
| -------------- | ---------------------------------------------------- |
| **Input**      | `lint(root, category?)`                              |
| **Output**     | `LintReport`                                         |
| **Protocol**   | `ISkillsLinterProtocol`                              |
| **Method**     | `lint`                                               |
| **Event**      | none                                                 |
| **Error**      | `SkillsError` subclasses; agent maps to exit codes   |

#### Test (3)

| Context              | When Action    | Then Observable Result               |
| -------------------- | -------------- | ------------------------------------ |
| Lint a valid root    | `lint(root)`   | `LintReport` with `issues`,          |
|                      |                | `weed_lines`, `skills`,              |
|                      |                | `categories` populated               |
| Lint an empty pack   | `lint(root)`   | Empty report with no issues          |

#### Metric (3)

| Target Metric              | Value   |
| -------------------------- | ------- |
| Capability contract pass   | 100 %   |

### FR-DESIGN-004: Runner capability contract

**Description:** `SkillsRunner` shall implement `ISkillsRunnerProtocol` and
expose `apply_automatic_transitions`, `pause`, and `resume` for lifecycle verbs.

#### Business Logic (4)

- `apply_automatic_transitions` applies automatic lifecycle transitions across
  the pack.
- `pause` pauses lifecycle transitions; `resume` resumes them.
- An `OSError` from the runner is caught by the agent and returned as a
  `SkillsResult` with `ISSUES_FOUND` exit code.
- The runner never imports a sibling capability.

#### Edge Cases (4)

- On `RUN`, `PAUSE`, or `RESUME`, an `OSError` from the runner shall be caught
  and returned as `ISSUES_FOUND`.

#### Technical Specification (4)

| Aspect         | Detail                                                      |
| -------------- | ----------------------------------------------------------- |
| **Input**      | `apply_automatic_transitions(root?)` / `pause(root)` /      |
|                | `resume(root)`                                              |
| **Output**     | `MutationOutcome`                                           |
| **Protocol**   | `ISkillsRunnerProtocol`                                     |
| **Method**     | `apply_automatic_transitions`, `pause`, `resume`            |
| **Event**      | none                                                        |
| **Error**      | `OSError`, `SkillsError` subclasses; agent maps to exit     |
|                | codes                                                       |

#### Test (4)

| Context                 | When Action             | Then Observable Result   |
| ----------------------- | ----------------------- | ------------------------ |
| Runner with lifecycle   | `apply_automatic_tran   | Result with              |
| paused                  | sitions()`              | `paused=True` and        |
|                         |                         | empty `applied` list     |
| Runner pause/resume     | `pause(root)` /         | Lifecycle transitions    |
|                         | `resume(root)`          | paused then resumed      |

#### Metric (4)

| Target Metric              | Value   |
| -------------------------- | ------- |
| Capability contract pass   | 100 %   |

## Public Interface

| Aspect      | Detail                                                         |
| ----------- | -------------------------------------------------------------- |
| Agent       | `SkillsDesignAgent`                                            |
| Aggregate   | `ISkillsDesignAggregate`                                       |
| Method      | `execute`                                                      |
| Request     | `SkillsRequest` (op, query, flags, apply, root)                |
| Response    | `SkillsResult` (ok, op, exit_code, message, op-specific        |
|             | fields)                                                        |

## Reference

| Artifact       | Purpose                      | Link                         |
| -------------- | ---------------------------- | ---------------------------- |
| PRD            | Business goals and scope     | [PRD.md](../../../../../PR   |
|                |                              | D.md)                        |
| Backlog        | Task tracking and            | [BACKLOG.md](BACKLOG.md)     |
|                | implementation status        |                              |
| Roadmap        | Timeline, phasing, and       | [ROADMAP.md](../../../../.   |
|                | dependencies                 | ./ROADMAP.md)                |
| Architecture   | System boundaries, tech      | [ARCHITECTURE.md](../../..   |
|                | stack, and infra             | /../../ARCHITECTURE.md)      |
