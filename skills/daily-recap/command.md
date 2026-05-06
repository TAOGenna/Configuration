---
description: Generate a per-session daily recap of Claude Code sessions, grouped by project, written to the Obsidian vault. Args: [date] [--llm]. Default date is yesterday.
---

Run the daily-recap script with the user's arguments and show the output verbatim.

```bash
python3 ~/.claude/skills/daily-recap/recap.py $ARGUMENTS
```

If the user did not pass a date, the default is "yesterday". Accepted date forms: `yesterday`, `today`, `YYYY-MM-DD`. The `--llm` flag upgrades summaries via Haiku per session (slower, costs API calls).

After running, tell the user the path to the generated file.
