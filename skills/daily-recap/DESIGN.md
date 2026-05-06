---
name: daily-recap
date: 2026-05-06
status: implemented v1
---

# Daily Recap — Design

## Problem
Many Claude sessions across many projects in a single day. By the next morning it is hard to remember what was actually worked on. Need a programmatic digest.

## Output
A persistent daily journal in the Obsidian vault:
`<vault>/daily-recaps/YYYY-MM-DD.md` — vault is `/Users/kenyi/Documents/stuff/WORK/yavendio`.

Per-session bullets, project-grouped. One bullet per real session (project-grouped, not per-project-collapsed).

## Activation
Two surfaces, one underlying script:
- Slash command `/daily-recap [date] [--llm]` — `~/.claude/commands/daily-recap.md`
- Phrase-triggered skill — `~/.claude/skills/daily-recap/SKILL.md` — fires on "what did I do yesterday", "recap May 5", "summarize my sessions", etc.

Both invoke `~/.claude/skills/daily-recap/recap.py`.

Single-day scope only for v1.

## Summarization
Hybrid:
- **Heuristic mode (default)** — bullet built from extracted signals only. No LLM call. Sub-second.
- **LLM mode (`--llm`)** — per-session signals are sent to `claude -p --model claude-haiku-4-5` to produce a one-line natural-language summary. Falls back to heuristic on per-session failure.

Frontmatter `mode:` records which mode produced the file.

## Date semantics
- Local timezone (system clock).
- A session belongs to day D if it has at least one `user` message with `timestamp` in `[D 00:00 local, D+1 00:00 local)`.
- Cross-midnight sessions appear in both days. The "last-prompt" shown is the last user message *within that day's window*, not the session's overall last prompt.
- Re-running for a date overwrites the file (atomic temp+rename). The .jsonl files are the source of truth; the markdown is derived.

## Filtering
Skip a session from the day if all of these hold:
- Fewer than 2 user messages on that day, AND
- No file-editing tool calls (Edit / Write / NotebookEdit / MultiEdit) on that day, AND
- No `pr-link` recorded.

Drops "started Claude, asked one trivial thing, closed" noise. A 1-message session that edited files is real work and stays.

### System-injected text filtering (added during implementation)
Claude Code injects synthetic "user" records as wrappers around system events: `<task-notification>`, `<local-command-stdout>`, `<system-reminder>`, `<output-file>`, `<status>`, `<summary>`, `<command-name>`, image refs, etc. These arrive on the user role but are NOT real user prompts. The recap script:
- Strips matched-pair noise tags via regex.
- Treats any text containing an opening or closing fragment of a known noise tag as "pure noise" and excludes it entirely (handles unmatched / nested cases like a bare `</task-notification>`).
- Applies this to BOTH string-typed and array-typed user content, AND to `ai-title` values (which are sometimes generated from a noise-prefixed message).

This is what makes the "last working on:" excerpts and titles read like real user prompts instead of internal Claude Code plumbing.

## Signals extracted per session per day
| Signal | Source |
|---|---|
| Session ID | filename (UUID) |
| Project label | `basename(cwd)` from first `system` record's `cwd` field |
| Git branch | first `system` record's `gitBranch` |
| Title | latest `ai-title.aiTitle` |
| First user message | first `user` record on day D, content text |
| Last user prompt on day D | last `user` record on day D |
| Files edited on day D | count of tool_use blocks (Edit/Write/NotebookEdit/MultiEdit) on day D |
| PR link | most recent `pr-link` record on day D, if any |
| Message counts | user / assistant on day D |

## File format

```markdown
---
date: YYYY-MM-DD
generated: ISO-8601-local
sessions: N
mode: heuristic | llm
tags: [daily-recap]
---

# YYYY-MM-DD — Daily recap

N sessions across M projects.

## <project>
- **<title>** — last working on: "<last-prompt-truncated>"; <N> files touched. [PR #X](url)

...

---

<details>
<summary>Raw session index</summary>

| Project | Session | Title | User msgs | Files | PR |
| ... |
</details>
```

Heuristic bullet recipe:
- Bold = `ai-title` (cleaned: capitalized, trailing punctuation stripped). Fallback = first 50 chars of first user message, ellipsized.
- Body = `last working on: "<last-prompt[:120]>"; N files touched.` + ` [PR #X](url)` if any.
- File count is omitted if zero AND there are zero edits (cleaner for "scratch" sessions).

LLM bullet recipe:
- Same per-session payload sent to Haiku 4.5.
- Prompt asks for `**Topic** — past-tense one-liner.` (1 line, ~120 chars max).
- Heuristic bullet is included in the prompt as a fallback hint.

## Edge cases
- Empty day (no sessions match) → write file with "No sessions on this date." line. Don't error.
- Vault `daily-recaps/` doesn't exist → create. Vault root missing → error with clear message.
- Future date → error. Invalid date string → error.
- Project name collision (two cwds with same basename) → disambiguate by including parent: e.g., `cloned/yv-ecommerce`.
- `cwd` resolution priority: first `system` record with `cwd` field → fallback to dir-name decode (replace `-` with `/`, lossy).
- Atomic write: write to `<file>.tmp` then `os.replace()`.
- LLM mode per-session failure (timeout, non-zero exit) → log and fall back to heuristic for that session.

## Architecture
```
User → "what did I do yesterday"  or  /daily-recap
              │                              │
              ▼                              ▼
         SKILL.md                  commands/daily-recap.md
              │                              │
              └────────── recap.py ──────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    walk projects/*.jsonl   group       render markdown
    extract per-session    by project   → vault file (atomic)
    signals on day D
                              │
                              ▼
                      print path + preview
```

Stdlib-only Python. No pip deps. macOS python3.

## Testing
- Smoke test: run for yesterday (May 5) on the user's real `~/.claude/projects/`. Verify the file is written, parses as markdown, and contains plausible bullets.
- Manual visual check of generated file.
- `--dry-run` flag prints to stdout instead of writing to vault, for iteration.

## Out of scope (v1)
- Multi-day ranges / weekly views (phrase like "summarize last week").
- Automatic end-of-day generation (cron / ScheduleWakeup).
- Tagging projects with custom labels.
- Cross-linking between days.
- Search/grep helpers — Obsidian gives this for free.
