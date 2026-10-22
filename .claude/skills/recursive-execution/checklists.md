# recursive-execution — Self-review checklists and red flags

> Detail for [SKILL.md](SKILL.md). On conflict, SKILL.md §Hard rules wins.

## Self-review checklists

### Leaf checklist (run before declaring a leaf complete)

- [ ] Implementer prompt's first action was `Invoke the Skill tool with skill='<name>' before doing anything else.`?
- [ ] Prompt inlined the commit rule, the code conventions, the map rule and the question ladder?
- [ ] Greenness gate ran in this turn AND output pasted (`N passed`)?
- [ ] Subagent (not controller) authored the commit, after the gate went green?
- [ ] `git add` listed explicit paths?
- [ ] Commit message matched the plan's prewritten line verbatim?
- [ ] Shape check ran: every file in the task's Files list is in `git show --stat HEAD`, no unlisted file unexplained, subject matches?
- [ ] TaskCreate entry marked completed?
- [ ] Task's checkboxes ticked in the plan file (uncommitted)?
- [ ] Mode-appropriate approval gate honored?

### Internal-node checklist (run before declaring a deliverable complete)

- [ ] All children's leaf checklists ✅?
- [ ] Shared-contract check ran with evidence (producing + consuming commits)?
- [ ] Duplicate-abstraction check ran with grep evidence?
- [ ] Shared-model-consistency check ran with `git diff` evidence?
- [ ] Merge-order check ran per sibling commit?
- [ ] **The deliverable's review task ran AND recorded `review: ✅`?**
- [ ] The deliverable's extra gate ran (DESIGN.md `wc -w`, diagram files, `docker build`, CLI behaviours)?
- [ ] Hebrew `done / next / blocked` status emitted?
- [ ] TaskCreate entry for the internal node marked completed?
- [ ] Mode-appropriate approval gate honored?

## Red flags — STOP

- "I'll review per leaf to catch issues early" — reviews run once per deliverable, in the plan's review task.
- "Skip approval gate, it's the same kind of task" — mode dictates gating, not task type.
- "I'll skim the diff while I'm checking the stat" — the shape check reads paths and the subject only.
- "Verification looks fine from the previous run" — re-run in this turn.
- "Cross-task review can wait until everything ships" — it runs at each deliverable node.
- "Parallel subagents on sibling leaves are faster" — they invent duplicates; one leaf at a time.
- "The plan's commit message is awkward, I'll improve it" — halt and amend the plan first.
- "Depth 3 is fine" — depth > 2 requires explicit approval.
- "The added task is small, the earlier verification still holds" — untick, re-open, re-verify.
- "The map node is obviously a typo, I'll fix it" — never; report it to Ofek.
- "One more hour and eval would be production-grade" — the time box is 4 h; stub and move on.
