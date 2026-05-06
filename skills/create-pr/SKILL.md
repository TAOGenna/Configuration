---
name: create-pr
description: Create a PR with focused commits, Paul Graham-style description, ASCII diagrams, and QA results. Repo-agnostic — auto-detects base branch and lint/test commands.
---

# Create PR (`/create-pr`)

Create a pull request following these guidelines, in any git repository.

## Trigger

Use when the user asks to: "create a PR", "push and create PR", "open a PR", "submit for review".

## Resolving base branch and commands

Before doing anything else, resolve two things: which branch the PR targets, and which lint/test commands to run.

### Base branch (in order — first match wins)

1. **Explicit override in the user's message.** Treat any of these as a directive:
   - "base: `<name>`" / "base branch `<name>`"
   - "the branch should point to `<name>`"
   - "PR against `<name>`" / "target `<name>`"
   - "open it against `<name>`"
2. **Auto-detect from origin.**
   ```bash
   git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null \
     | sed 's@^refs/remotes/origin/@@'
   ```
   If empty, fall back to `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`.
3. **Ask the user.** "What base branch should this PR target?"

State the resolved base branch out loud before continuing — e.g., "Targeting `main` (auto-detected from origin/HEAD)."

### Lint / test commands (in order)

1. **Repo-level `CLAUDE.md` or `AGENTS.md`.** If either documents lint/test commands (typically under a "Commands" or "Development" section), use what's documented and skip sniffing.
2. **Sniff config files.** Highest-priority match wins:
   - `Makefile` — look for targets named `fix`, `lint`, `format`, `check`, `test`. Use the targets that exist.
   - `package.json` — read the `scripts` block. Prefer `lint`, `test`, `format` keys.
   - `pyproject.toml` — check `[tool.poetry.scripts]` or `[project.scripts]`; otherwise fall back to `ruff check` + `pytest` if those tools are configured.
   - `Cargo.toml` — `cargo fmt --check && cargo clippy && cargo test`.
   - `go.mod` — `go fmt ./... && go vet ./... && go test ./...`.
3. **If multiple plausible commands exist, ask.** Don't guess between `npm test` and `npm run test:unit` — ask which is canonical.
4. **If nothing is found, ask.** "I can't find a lint/test command for this repo — what should I run, or should I skip?"

State the resolved commands out loud — e.g., "Will run `make lint` then `make test`."

## Commit Policy

### 1. Focused, non-bloated commits

- One logical unit per commit — don't mix unrelated changes.
- Order commits to tell a reviewable story (creation → rewiring → tests).
- If a file has changes from two phases, place it in the commit where the majority of its changes belong and note the overlap.

### 2. Proper commit messages

- First line: `type: short imperative description` (under 72 chars).
- Body: explain the **why**, not just the what. Reference the ticket/issue if applicable.
- Always end with:
  ```
  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  ```
- Use HEREDOC for multi-line messages:
  ```bash
  git commit -m "$(cat <<'EOF'
  refactor: extract services layer

  Explanation here.

  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  EOF
  )"
  ```

### 3. Never commit without explicit user approval

- Show the plan (commit list with proposed messages) before executing.
- "go ahead", "proceed", "do it" counts as approval.

## PR Description Style

Write in **Paul Graham's technical writing style**:

- Clear, concise, conversational.
- Lead with what changed and why — not process or ceremony.
- Opinionated but backed by reasoning.
- Short paragraphs. No filler.

### Required Sections

```markdown
## What this does

One paragraph. What changed and why it matters. No preamble.

### [Section per logical group of changes]

Explain each group with enough context for a reviewer who hasn't
seen the conversation. Use ASCII diagrams for structural changes.

## QA results

### Unit tests
One line: X passed, Y failed (pre-existing), Z skipped.

### Manual QA
If manual QA was performed, include a table:

| # | Test | Code path exercised | Result |
|---|---|---|---|
| 1 | ... | ... | ... |

If no manual QA was performed, say so explicitly:
"No manual QA performed — only the automated checks above."

## Commits

| # | Commit | What |
|---|--------|------|
| 1 | `message` | one-line summary |

Review commit-by-commit for sanity.

## Test plan

- [x] completed items
- [ ] pending items

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### ASCII Diagrams

Use ASCII diagrams for any structural change (file moves, dependency direction, architecture). Keep them readable — max 80 chars wide.

```
BEFORE                    AFTER

old/path/                 new/path/
├── file.py  ──────────▶  ├── file.py
└── other.py ──────────▶  └── other.py
```

### QA Results Are Mandatory

The `## QA results` section must always be present. If no QA was done, say so explicitly in the section body — don't omit the section. Silent omission is how regressions ship.

## Checklist Before Creating

1. `git status` — verify clean tree, all changes staged/committed.
2. `git log <base>..HEAD` — verify commit history tells a clear story.
3. Run the resolved lint command — confirm passes.
4. Run the resolved test command — confirm passes (note pre-existing failures explicitly).
5. Push with `-u` flag.
6. `gh pr create --base <resolved-base>` — pass the body via HEREDOC for correct formatting.
