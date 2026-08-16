---
name: implement-ticket
description: Implement a to-tickets ticket (a GitHub issue) end to end. Use when the user wants to start or continue implementing a ticket. Scoped to app work (universal/) — services/deploy work stays on the OpenSpec workflow.
---

# Implement Ticket

Drive one to-tickets ticket from "open" to "ready to squash and PR" by handing it to `tdd`, `commit`, and `code-review` in sequence. This skill only orchestrates — it has no test-writing or review judgement of its own; that judgement belongs to the skills it calls.

Read `docs/agents/issue-tracker.md` for how to fetch and edit issues.

## 1. Work the ticket

Select it (named by the user, inferred from context, or asked via **AskUserQuestion** among open unblocked issues), fetch its full body, and stop if it still has an open blocker. Branch off an up-to-date `main` (or rebase if continuing an existing branch for it).

## 2. Implement with `tdd`

Work through the ticket's unchecked acceptance criteria using the `tdd` skill. As each criterion goes green make a temporary checkpoint commit: `git commit -m "criterion N [temporary]: <short description>"`.

## 3. Review loop

Once every criterion is implemented, invoke the `code-review` skill with the fixed point set to the branch's merge-base with `main`. Fix what it reports, commit the fixes as temporary (`review finding [temporary]: <short description>`), re-invoke `code-review`, and repeat until clean. Don't repeat an axis which didn't find anything.

## 4. Final commit

Hand off to the `commit` skill for the squash: `git reset --soft origin/main` then commit with a real message and a `Closes #N` trailer for this ticket's issue.
