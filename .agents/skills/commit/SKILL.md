---
name: commit
description: Make a git commit following Conventional Commits, with the issue number referenced in a footer trailer, closing the issue if this commit completes all its work. Use this skill whenever the user asks to commit, says "make a commit", "commit this", "commit my changes", "/commit", or wants to save their work to git.
---

# Commit Skill

Write the message per [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): pick `type` from the spec's set based on the diff, match this repo's existing convention of no scopes, and flag breaking changes exactly as the spec describes.

Layer issue tracking on as a footer trailer:
- `Closes #N` — only when the diff covers everything the issue describes.
- `Refs #N` — partial work, or any time you're not closing it.
- Multiple issues: one trailer line per issue.
- No related issue: omit the trailer.

```
feat: add FeedSourceRepository with DataStore persistence

Implements CRUD operations for feed source URLs/names backed by
Jetpack DataStore.

Closes #5
```

## Step-by-step

### 1. Understand what changed

Run these in parallel:
- `git status` — see staged/unstaged files
- `git diff HEAD` — see full diff of changes
- `git log --oneline -5` — see recent commit style to match

### 2. Find the issue number

Try in order until you have it:

1. **User told you** — they mentioned "#5" or "issue 5" in their request.
2. **Branch name** — extract from branch names like `feature/issue-5-feed-repo` or `feat/5-something`. Run `git branch --show-current`.
3. **Ask the user** — if none of the above works, ask: "Which issue does this work relate to? (or say 'none' if there isn't one)"

### 3. Decide whether to close the issue

Look at the issue to understand its scope: `gh issue view <N>`. Compare the issue's checklist/description against what the diff actually implements.

Close (`Closes #N`) only when the diff covers everything the issue describes; otherwise reference it (`Refs #N`). When in doubt, reference — it's easy to close manually later, hard to reopen.

### 4. Stage and commit

Stage only relevant files — prefer naming them explicitly over `git add -A` to avoid accidentally including secrets or generated files.

Then commit:
```bash
git commit -m "$(cat <<'EOF'
type: description

Closes #N
EOF
)"
```

Swap in `Refs #N`, or drop the trailer entirely, per the decision above.

### 5. Confirm

Run `git log --oneline -1` and show the user the resulting commit line.
