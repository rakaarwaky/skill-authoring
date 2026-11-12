# README — Skill Authoring

## Project Overview

Skill Authoring is the skill-authoring skill that keeps the skill tree clean, correct, and consolidated. It reads agent `SKILL.md` skill directories and runs one of three modes per invocation: `--create` builds a publishable `SKILL.md` plus its `references/` from a described job, `--improve` audits an existing skill against the shared lint standard and applies the repair edit recipe, and `--prune` collapses duplicate or same-purpose skills into one folder and archives the dropped duplicates. Every fact in a skill lives once, in a single authoritative home; every flag and mode term stays in lockstep across `SKILL.md` and its reference files.

## Prerequisites

- The skill-design pack at `skills/skill-authoring/skill-design/`
- `uv` (Python package manager)
- `sac` launcher on `PATH` (`sac help` lists every command)

## Quick Start

| Step | Action | Command |
|------|--------|---------|
| 1 | Inspect the skill tree | `sac lint` |
| 2 | Create a new skill from a described job | `sac create skill <name> [--category CAT] [--description DESC] [--apply]` |
| 3 | Audit + repair an existing skill | `sac lint [--category NAME]`, then `sac read <name>`, edit, then `sac catalog` |
| 4 | Collapse overlapping skill folders | `sac discover <query>` → `sac move <name> <category> [--apply]` or `sac archive <name> [--apply]` |
| 5 | Dry-run (report only, no changes) | Omit `--apply` (mutations are dry-run by default); append `--apply` to write |

### Discovery — read-only

| Command | Purpose |
|---------|---------|
| `sac list` | List all skills in the pack |
| `sac read <name>` | Print a skill's `SKILL.md` |
| `sac lint [--category NAME]` | Lint scan all skills, optionally filter by category |
| `sac catalog [--build] [--read] [--check]` | Build and/or read `catalog.json`; `--check` verifies drift |
| `sac discover <query>` | Search the catalog |

### Observation

| Command | Purpose |
|---------|---------|
| `sac phrases [--grok-home DIR] [--run-dir DIR] [--days N] [--since-last] [--min-turns N] [--limit N] [--min-sessions N] [--json]` | Mine repeated user prompts from session traces |

### Mutations

| Command | Purpose |
|---------|---------|
| `sac move <name> <category> [--apply]` | Move a skill to a category (dry-run by default) |
| `sac archive <name> [--apply]` | Archive a skill into `_archive/` (dry-run by default) |

### Create

| Command | Purpose |
|---------|---------|
| `sac create skill <name> [--category CAT] [--description DESC] [--apply]` | Create a skill |
| `sac create category <name> [--force] [--apply]` | Create a category |

### Lifecycle

| Command | Purpose |
|---------|---------|
| `sac status` | Show per-skill lifecycle states |
| `sac usage` | Show usage telemetry rows |
| `sac run` | Run automated state transitions |
| `sac pause` | Pause automatic transitions |
| `sac resume` | Resume automatic transitions |
| `sac pin <skill>` | Pin a skill in active state |
| `sac unpin <skill>` | Unpin a skill |
| `sac lock <skill>` | Lock a skill from mutation |
| `sac unlock <skill>` | Unlock a skill |
| `sac adopt <skill>` | Mark skill as agent-managed |

### Archive & Restore

| Command | Purpose |
|---------|---------|
| `sac restore <skill>` | Restore an archived skill |
| `sac list-unmanaged` | List skills without telemetry |
| `sac list-archived` | List archived skills |
| `sac prune [--days N] [--apply]` | Bulk archive idle skills |
| `sac purge [--days N] [--apply]` | Permanently remove archived skills |

### Backup & Rollback

| Command | Purpose |
|---------|---------|
| `sac backup` | Create a snapshot of skills pack |
| `sac rollback [--id ID]` | Restore from snapshot |
| `sac ledger` | View or compact audit ledger |

Every command is a plain `sac <verb> [flags]` subcommand; run `sac` with no args for the usage banner. Exit codes: `0` clean, `1` issues found, `2` usage error, `3` catalog drift.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| AGENTS.md | Agent operational guide (runtime, structure, commands) | [AGENTS.md](AGENTS.md) |
| PRD.md | What the product does and why | [PRD.md](PRD.md) |
| ROADMAP.md | What ships next, in order | [ROADMAP.md](ROADMAP.md) |
| ARCHITECTURE.md | Layer contract and linter rule catalog | [ARCHITECTURE.md](ARCHITECTURE.md) |
