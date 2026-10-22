---
name: session-retrospective
description: Use at the close of any session that produced commits or diffs (plan execution, bug fixes, deliverable builds), before declaring done. Skip read-only or planning-only sessions.
---

# Session Retrospective

## When to invoke

Trigger this skill **proactively** at session-close, before declaring "all done" — don't wait to be asked.

**Run it when** the session involved plan execution, bug fixes that touched code, a deliverable build, or any work that produced commits or diffs.

**Skip it when** the session was research-only, planning-only (wrote a plan but did not execute), or a pure review with no edits.

## Position in session-close

`verify → retrospective → CLAUDE.md update → commit/push/PR`

Produce the report without asking. After presenting it, wait for user approval before applying any proposed changes.

## Report format

### 1. Command Audit

Table of every Bash command run during the session:

| Command                                  | Action  | Context | Permission    | Count |
| ---------------------------------------- | ------- | ------- | ------------- | ----- |
| `make test`                              | execute | project | auto          | 3     |
| `python -m pytest -q tests/test_bank.py` | execute | project | auto          | 5     |
| `docker build -t tech-resolver .`        | execute | project | user-approved | 1     |

- **Action type:** `read` | `create` | `modify` | `execute`
- **Context:** `project` (belongs to this repo's workflow) | `system` (general tooling, one-off)
- **Permission:** `auto-approved` | `user-approved` | `denied`
- Deduplicate identical commands — show count instead.

### 2. Make-target candidates

Commands that appeared 2+ times OR are project-bound `execute`/`modify` commands not already a `Makefile` target. For each: the raw command, the proposed target name and recipe, why.

### 3. Test Gaps

Code paths touched during the session with no test coverage. For each: file/function, what a test should verify, proposed test file under `tests/`.

### 4. Code Agent Misconceptions & Mistakes

Capture only the gaps a future agent would repeat. For each item:

- **What happened** — the concrete misstep (one line).
- **Why it happened** — the missing context or signal.
- **Correction** — the rule, file, or check that would have prevented it.
- **Where it belongs** — root `CLAUDE.md`, a `.claude/skills/_shared/*.md` fragment, or `handoff-deliverables.md`.

Skip cosmetic slips. Include only items worth teaching the next session.

### 5. Proposed Changes

Grouped by:

- `Makefile` target additions
- **CLAUDE.md updates** — `{path}: {one-line edit}`. Do **not** edit inline; after approval, delegate to `claude-md-management:revise-claude-md`.
- `_shared/` fragment updates (a gate that was wrong, a ladder step that was missing)
- Memory updates
- Test file stubs
- Permission optimization suggestions (`.claude/settings.local.json` allow rules for commands that were user-approved repeatedly)
- **Map findings** — any V3 node or D-xx the session found wrong or missing, as a list for Ofek to apply in `ex.mmap`. Never edit the map.

## After the report

Present the full report and wait for explicit user approval before applying any proposed changes.

## Persist (always, no approval needed)

Append the report as a `## Session <YYYY-MM-DD>` block to `challange/docs/plans/retrospective.md` (create the file if missing). The next `work-kickoff` on this challenge reads it first.
