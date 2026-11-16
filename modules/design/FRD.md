# FRD — design

## Feature Overview

```
[Surface CLI] --> [SkillsDesignAgent]
[MCP Surface] --> [SkillsDesignAgent]
[Root CLI] --> [SkillsDesignAgent]
[SkillsDesignAgent] --> [SkillsCreator]
[SkillsDesignAgent] --> [SkillsLinter]
```

The **design** feature sits in the agent layer and is called by the surface CLI,
MCP surface, and root CLI through the `ISkillsDesignAggregate` contract. It
sequences two capabilities — `SkillsCreator` (creates skills and categories)
and `SkillsLinter` (runs the 13-rule validator plus the weed report) — and
exposes them through a single `execute` entry point that translates a
`SkillsRequest` into the matching capability call and back into a
`SkillsResult`. The agent performs no filesystem I/O; every write and every
scan is delegated to a capability. The lifecycle verbs `run`, `pause`, and
`resume` belong to the [maintenance module](../maintenance/FRD.md) via
`ISkillsRunnerProtocol`; the design agent does not own them.

## Functional Requirements

### FR-DESIGN-001: Creator

**Description:** `SkillsCreator` shall implement `ISkillsCreatorProtocol` and
expose `create_skill` and `create_category`. The capability plans (dry-run) or
applies creation of a new skill SKILL.md or category folder under the skills
root, and the design agent routes the `create` `SkillsOp` to it through
`execute`.

#### Business Logic

- `create_skill` with `apply=False` shall return a `SkillCreatePlan` without
writing.
- `create_skill` with `apply=True` shall write the SKILL.md file under the
skills root.
- `create_category` with `apply=False` shall return a `NewCategoryPlan`
without writing.
- `create_category` with `apply=True` shall create the directory and the
category DESCRIPTION.md.
- `execute` with `op=create` and `flags[kind]=skill` shall require
`flags[category]`; a missing category shall raise `SkillsUsageError` and
return `SkillsResult` with `USAGE_ERROR` exit code.
- `execute` with `op=create` and `flags[kind]=category` shall call
`create_category` with `flags[force]` and the request `description`.
- On `apply=False` the agent shall return `SkillsResult` with the plan in
`create_plan` (skill) or `new_category` (category) and no catalog rebuild.
- On `apply=True` the agent shall rebuild the catalog through the discovery
catalog capability and return `SkillsResult` with both the plan and
`catalog` populated.
- An `execute` call whose `op` is not a `SkillsOp` member, or is an op this
aggregate does not own (for example `run`, `pause`, `resume`, `prune`),
shall return `USAGE_ERROR` before any capability runs.

#### Edge Cases

- A computed destination outside the skills root at apply time shall fail
closed and produce no write.
- A missing skill name shall raise an error the agent maps to a `SkillsResult`
with `ISSUES_FOUND` exit code.
- A `create` request with an unrecognized `flags[kind]` value shall be treated
as `kind=skill`.

#### Technical Specification


| Aspect       | Detail                                                        |
| ------------ | ------------------------------------------------------------- |
| **Input**    | `create_skill` / `create_category` arguments per protocol     |
| **Output**   | `SkillCreatePlan` / `NewCategoryPlan`                         |
| **Protocol** | `ISkillsCreatorProtocol`                                      |
| **Method**   | `create_skill`, `create_category`                             |
| **Event**    | none                                                          |
| **Error**    | `OSError`, `SkillsError` subclasses; agent maps to exit codes |


#### Test


| Context                         | When Action                       | Then Observable Result                                 |
| ------------------------------- | --------------------------------- | ------------------------------------------------------ |
| Creator plan with `apply=False` | `create_skill` with `apply=False` | `SkillCreatePlan` returned; no filesystem write occurs |
| Creator plan with `apply=True`  | `create_skill` with `apply=True`  | SKILL.md written under the skills root                 |


#### Metric


| Target Metric            | Value |
| ------------------------ | ----- |
| Out-of-root write rate   | 0 %   |
| Capability contract pass | 100 % |


### FR-DESIGN-002: Linter

**Description:** `SkillsLinter` shall implement `ISkillsLinterProtocol` and
expose `lint`, running the combined 13-rule validator plus weed report in one
pass, and the design agent routes the `lint` `SkillsOp` to it through
`execute`.

#### Business Logic

- `lint` shall run the full lint over the root; optionally filter by category.
- `lint` shall return a single `LintReport` carrying both issues and weed lines.
- `execute` with `op=lint` shall read `flags[category]` as the optional
category filter and call `lint` with the resolved root.
- The agent shall set `exit_code=CLEAN` (0) when `report.issue_count == 0`
and `exit_code=ISSUES_FOUND` (1) otherwise.
- `execute` with `op=lint` shall return `SkillsResult` with `lint_report`
and `root` populated.

#### Edge Cases

- A lint request with no `flags[category]` shall run the full-pack lint with
no category filter.
- A capability raising `SkillsError` shall be caught by `execute` and returned
as `SkillsResult` with the capability's exit code.
- An empty pack shall return an empty report with no issues.

#### Technical Specification


| Aspect       | Detail                                             |
| ------------ | -------------------------------------------------- |
| **Input**    | `lint(root, category?)`                            |
| **Output**   | `LintReport`                                       |
| **Protocol** | `ISkillsLinterProtocol`                            |
| **Method**   | `lint`                                             |
| **Event**    | none                                               |
| **Error**    | `SkillsError` subclasses; agent maps to exit codes |


#### Test


| Context            | When Action  | Then Observable Result      |
| ------------------ | ------------ | --------------------------- |
| Lint a valid root  | `lint(root)` | `LintReport` with `issues`, |
|                    |              | `weed_lines`, `skills`,     |
|                    |              | `categories` populated      |
| Lint an empty pack | `lint(root)` | Empty report with no issues |


#### Metric


| Target Metric            | Value |
| ------------------------ | ----- |
| Capability contract pass | 100 % |


## Public Interface


| Aspect    | Detail                                                           |
| --------- | ---------------------------------------------------------------- |
| Agent     | `SkillsDesignAgent`                                              |
| Aggregate | `ISkillsDesignAggregate`                                         |
| Method    | `execute`                                                        |
| Request   | `SkillsRequest` (op, query, flags, apply, root)                  |
| Response  | `SkillsResult` (ok, op, exit\_code, message, op-specific fields) |


## Reference


| Artifact     | Purpose                           | Link                                              |
| ------------ | --------------------------------- | ------------------------------------------------- |
| PRD          | Business goals and scope          | [PRD.md](../../../../../PRD.md)                   |
| Backlog      | Task tracking and implementation  | [BACKLOG.md](BACKLOG.md)                          |
| Roadmap      | Timeline, phasing, and dependencies | [ROADMAP.md](../../../../../ROADMAP.md)           |
| Architecture | System boundaries, tech stack, infra | [ARCHITECTURE.md](../../../../../ARCHITECTURE.md) |
