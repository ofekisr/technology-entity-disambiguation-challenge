# work-kickoff — SEED contract and pipeline

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## SEED contract

```
SEED = {
  kind:  deliverable | task | bug,
  origin: <path or ref>,          # "ex.md › Deliverable 4", a chat request, a failing test name
  items: [                        # one or more units of work
    { title, context, artifacts:[<files/map nodes already known>] }
  ]
}
```

| Kind | Normalization |
|---|---|
| `deliverable` | `ex.md` › Deliverable N + the matching `handoff-deliverables.md` row + the `V3 › Doc map` nodes that feed it → one item per deliverable |
| `task` | the chat request → one item |
| `bug` | the failing command + output → one item; routes to the bug-fix two-phase shape |

Everything below the SEED line is identical for all kinds.

## The pipeline

```dot
digraph work_kickoff {
    "Normalize seed → SEED" [shape=box];
    "Initial plan: read origin + artifacts, list work units" [shape=box];
    "Bucket each unit (bucket-rubric.md)" [shape=box];
    "bucket?" [shape=diamond];
    "design: report gap, ask Ofek (never edit ex.mmap)" [shape=box];
    "plan: writing-plan → execute" [shape=box];
    "inline: do it directly" [shape=box];
    "TDD + green gate (mandatory)" [shape=box];
    "doc-sync checklist (advisory)" [shape=box];
    "Hebrew status: done / next / blocked" [shape=box];

    "Normalize seed → SEED" -> "Initial plan: read origin + artifacts, list work units";
    "Initial plan: read origin + artifacts, list work units" -> "Bucket each unit (bucket-rubric.md)";
    "Bucket each unit (bucket-rubric.md)" -> "bucket?";
    "bucket?" -> "design: report gap, ask Ofek (never edit ex.mmap)" [label="design"];
    "bucket?" -> "plan: writing-plan → execute" [label="plan"];
    "bucket?" -> "inline: do it directly" [label="inline"];
    "design: report gap, ask Ofek (never edit ex.mmap)" -> "Normalize seed → SEED" [label="answer re-enters as a task seed"];
    "plan: writing-plan → execute" -> "TDD + green gate (mandatory)";
    "inline: do it directly" -> "TDD + green gate (mandatory)";
    "TDD + green gate (mandatory)" -> "doc-sync checklist (advisory)";
    "doc-sync checklist (advisory)" -> "Hebrew status: done / next / blocked";
}
```
