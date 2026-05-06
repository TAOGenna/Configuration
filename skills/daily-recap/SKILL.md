---
name: daily-recap
description: Generate a per-session daily recap of Claude Code work, grouped by project, written to the user's Obsidian vault. Use when the user asks "what did I do yesterday", "recap [date]", "summarize my sessions", "daily recap", or any variant of looking back at their recent Claude sessions.
---

# Daily Recap

Generate a persistent daily journal entry for the user's Claude Code sessions on a given date. The entry lives in their Obsidian vault at `/Users/kenyi/Documents/stuff/WORK/yavendio/daily-recaps/YYYY-MM-DD.md`.

## How to invoke

Run the underlying script. **Do not parse the JSONL files yourself** — that is what the script is for.

```
python3 ~/.claude/skills/daily-recap/recap.py [DATE] [--llm]
```

- `DATE` accepts: omitted (yesterday), `yesterday`, `today`, or `YYYY-MM-DD`.
- `--llm` upgrades each per-session bullet using a Haiku call. Default is the fast heuristic mode. Only pass `--llm` if the user explicitly asks for higher-quality summaries.

The script prints the written file's path and a preview to stdout. Show that to the user verbatim.

## Resolving the date from natural language

When the user's request implies a date, pass it as an arg:
- "what did I do yesterday" → no arg (yesterday is the default)
- "recap today" / "what have I done so far today" → `today`
- "summarize my sessions from May 5" / "recap May 5" → `2026-05-05` (use the current year unless they specify)
- "what was I working on last Tuesday" → resolve to absolute date and pass `YYYY-MM-DD`

If the user's date phrase is ambiguous (e.g., "Monday" but unclear which Monday), ask one short clarifying question before running.

## After running

- Confirm the file was written (the script prints the path).
- Offer to open it: tell the user the path so they can open in Obsidian.
- If the user reads the bullets and points at one that looks wrong, the bottom of the file has a "Raw session index" with session UUIDs. They can `claude --resume <uuid>` to re-open the underlying session.

## What NOT to do

- Don't try to read JSONL files yourself or summarize sessions inline. The script does the extraction deterministically; doing it inline burns tokens and gives flakier output.
- Don't loop over sessions to call the model yourself — the `--llm` flag handles that via a sub-process per session.
- Don't write to a different output path. The vault path is fixed.
