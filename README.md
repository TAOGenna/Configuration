# Configuration

My Claude Code skills, packaged as a plugin marketplace. One install brings in
my own skills plus two referenced third-party skill sets.

## Quick install

Inside Claude Code:

```
/plugin marketplace add TAOGenna/Configuration
/plugin install taogenna@configuration
```

Or from a shell:

```sh
claude plugin marketplace add TAOGenna/Configuration
claude plugin install taogenna@configuration
```

## What you get

| Plugin | Skills | Source |
|---|---|---|
| `taogenna` | `claude-sessions`: inspect past Claude Code session transcripts with jq | [`skills/`](skills/) in this repo |
| `mattpocock-skills` | 27 engineering and productivity skills: `tdd`, `code-review`, `grill-me`, `to-spec`, `handoff`, … | [mattpocock/skills](https://github.com/mattpocock/skills) |
| `janestreet-skills` | `socratic-tutor`: teaches a topic to mastery with the Socratic method | [janestreet/agent_skills](https://github.com/janestreet/agent_skills) |

The two third-party sets are installed as dependencies of `taogenna`, fetched
straight from their own repos, so nothing is copied here.

## Update

```sh
claude plugin marketplace update configuration
claude plugin update taogenna@configuration
```

## Other docs

- [terminal-setup.md](terminal-setup.md): full spec for rebuilding the terminal environment on a fresh Mac.
