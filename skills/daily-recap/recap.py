#!/usr/bin/env python3
"""Daily recap of Claude Code sessions, written to an Obsidian vault.

See DESIGN.md for full spec. Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable

PROJECTS_DIR = Path.home() / ".claude" / "projects"
DEFAULT_VAULT = Path("/Users/kenyi/Documents/stuff/WORK/yavendio")
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
LLM_MODEL = "claude-haiku-4-5"
LLM_TIMEOUT_SECONDS = 30

# System-injected user-text wrappers we should treat as non-prompts.
# Claude Code injects these as text blocks under user records, but they aren't real user prompts.
_NOISE_TAG_PATTERN = re.compile(
    r"<(?:task-notification|local-command-stdout|local-command-stderr|local-command-caveat|"
    r"system-reminder|output-file|tool-use-id|task-id|command-name|command-message|command-args|"
    r"user-prompt-submit-hook)\b[^>]*>.*?</(?:task-notification|local-command-stdout|local-command-stderr|"
    r"local-command-caveat|system-reminder|output-file|tool-use-id|task-id|command-name|command-message|"
    r"command-args|user-prompt-submit-hook)>",
    re.DOTALL,
)
_IMAGE_REF_PATTERN = re.compile(r"\[Image:\s*source:\s*[^\]]+\]")
_TAG_PREFIX_PATTERN = re.compile(r"^\s*<[a-zA-Z][\w-]*\b")

# Names of known noise wrappers — used for fragment detection (open OR close tag, with or without matching pair).
_NOISE_TAG_NAMES = (
    "task-notification", "local-command-stdout", "local-command-stderr",
    "local-command-caveat", "system-reminder", "output-file", "tool-use-id",
    "task-id", "command-name", "command-message", "command-args",
    "user-prompt-submit-hook", "status", "summary",
)
_NOISE_FRAGMENT_PATTERN = re.compile(
    r"</?(?:" + "|".join(_NOISE_TAG_NAMES) + r")\b",
    re.IGNORECASE,
)


# ---------- data model ----------

@dataclass
class SessionDay:
    """A single Claude session's activity restricted to one local-day window."""
    session_id: str
    project_dir: Path
    cwd: str | None = None
    git_branch: str | None = None
    ai_title: str | None = None
    first_user_msg: str | None = None
    last_user_msg: str | None = None
    user_msg_count: int = 0
    assistant_msg_count: int = 0
    edit_tool_count: int = 0
    pr_url: str | None = None
    pr_number: int | None = None

    @property
    def project_label(self) -> str:
        if self.cwd:
            return Path(self.cwd).name
        # fallback: decode from project dir name
        decoded = self.project_dir.name.lstrip("-").replace("-", "/")
        return Path("/" + decoded).name

    @property
    def project_parent(self) -> str:
        if self.cwd:
            p = Path(self.cwd)
            return p.parent.name
        return ""


# ---------- date / time ----------

def parse_date_arg(s: str | None) -> date:
    today_local = datetime.now().astimezone().date()
    if s is None or s == "yesterday":
        return today_local - timedelta(days=1)
    if s == "today":
        return today_local
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise SystemExit(f"error: could not parse date {s!r}; use YYYY-MM-DD, 'yesterday', or 'today'")


def day_window_local(d: date) -> tuple[datetime, datetime]:
    """Return [start, end) timezone-aware in local tz."""
    local_tz = datetime.now().astimezone().tzinfo
    start = datetime.combine(d, time.min, tzinfo=local_tz)
    end = start + timedelta(days=1)
    return start, end


def parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    # Be defensive about Python versions where 'Z' isn't accepted by fromisoformat
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(ts).astimezone()
    except (ValueError, TypeError):
        return None


# ---------- jsonl extraction ----------

def strip_noise(text: str) -> str:
    """Remove system-injected wrappers from user text. Return cleaned text (may be empty)."""
    if not text:
        return ""
    cleaned = _NOISE_TAG_PATTERN.sub("", text)
    cleaned = _IMAGE_REF_PATTERN.sub("", cleaned)
    return cleaned.strip()


def is_pure_noise(text: str) -> bool:
    """True if the text looks like a system-injected wrapper rather than a real user prompt.

    Stricter than strip_noise alone: if the text contains ANY fragment of a known noise tag
    (open or close, even unmatched), we treat the whole block as noise. This catches truncated
    or nested system payloads that survive the matched-pair stripper.
    """
    cleaned = strip_noise(text)
    if not cleaned:
        return True
    if _NOISE_FRAGMENT_PATTERN.search(cleaned):
        return True
    return False


def text_from_user_content(content) -> str:
    """user.message.content can be a string or a list of blocks. Return only real text (not tool_results, not system injections)."""
    if isinstance(content, str):
        if is_pure_noise(content):
            return ""
        return strip_noise(content)
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text") or ""
                if t and not is_pure_noise(t):
                    cleaned = strip_noise(t)
                    if cleaned:
                        parts.append(cleaned)
        return "\n".join(parts).strip()
    return ""


def is_tool_result_user_record(content) -> bool:
    """A 'user' record can actually be a tool_result echoback. Detect that."""
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                return True
    return False


def extract_session_for_day(jsonl_path: Path, start: datetime, end: datetime) -> SessionDay | None:
    """Stream-parse a session .jsonl and return per-day aggregates. None if no activity in window."""
    sd = SessionDay(session_id=jsonl_path.stem, project_dir=jsonl_path.parent)
    had_activity_in_window = False
    last_user_in_window: tuple[datetime, str] | None = None
    first_user_in_window: tuple[datetime, str] | None = None
    last_pr_in_window: tuple[datetime, dict] | None = None

    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rtype = rec.get("type")

                if rtype == "system" and sd.cwd is None:
                    cwd = rec.get("cwd")
                    if cwd:
                        sd.cwd = cwd
                        sd.git_branch = rec.get("gitBranch")

                elif rtype == "ai-title":
                    title = rec.get("aiTitle")
                    if title:
                        cleaned_title = strip_noise(title)
                        if cleaned_title:
                            sd.ai_title = cleaned_title  # last clean one wins

                elif rtype == "user":
                    msg = rec.get("message") or {}
                    content = msg.get("content")
                    if is_tool_result_user_record(content):
                        continue  # not a real user prompt
                    text = text_from_user_content(content)
                    if not text:
                        continue
                    ts = parse_ts(rec.get("timestamp", ""))
                    if ts is None:
                        continue
                    if start <= ts < end:
                        had_activity_in_window = True
                        sd.user_msg_count += 1
                        if first_user_in_window is None:
                            first_user_in_window = (ts, text)
                        last_user_in_window = (ts, text)

                elif rtype == "assistant":
                    ts = parse_ts(rec.get("timestamp", ""))
                    if ts is None or not (start <= ts < end):
                        continue
                    sd.assistant_msg_count += 1
                    msg = rec.get("message") or {}
                    content = msg.get("content")
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "tool_use":
                                if block.get("name") in EDIT_TOOLS:
                                    sd.edit_tool_count += 1

                elif rtype == "pr-link":
                    ts = parse_ts(rec.get("timestamp", ""))
                    if ts is None or not (start <= ts < end):
                        continue
                    if last_pr_in_window is None or ts > last_pr_in_window[0]:
                        last_pr_in_window = (ts, rec)
    except (OSError, UnicodeDecodeError):
        return None

    if not had_activity_in_window:
        return None

    if first_user_in_window:
        sd.first_user_msg = first_user_in_window[1]
    if last_user_in_window:
        sd.last_user_msg = last_user_in_window[1]
    if last_pr_in_window:
        rec = last_pr_in_window[1]
        sd.pr_url = rec.get("prUrl")
        sd.pr_number = rec.get("prNumber")

    return sd


# ---------- filtering ----------

def is_near_empty(sd: SessionDay) -> bool:
    return (
        sd.user_msg_count < 2
        and sd.edit_tool_count == 0
        and sd.pr_url is None
    )


# ---------- rendering ----------

def clean_title(s: str) -> str:
    s = s.strip().rstrip(".:;,!?")
    if not s:
        return s
    return s[0].upper() + s[1:]


def truncate(s: str, n: int) -> str:
    s = " ".join(s.split())  # collapse whitespace
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


def heuristic_bullet(sd: SessionDay) -> str:
    if sd.ai_title:
        title = clean_title(sd.ai_title)
    elif sd.first_user_msg:
        title = truncate(sd.first_user_msg, 50)
    else:
        title = "(untitled session)"

    parts: list[str] = []
    if sd.last_user_msg:
        parts.append(f'last working on: "{truncate(sd.last_user_msg, 120)}"')
    if sd.edit_tool_count > 0:
        parts.append(f"{sd.edit_tool_count} file edit{'s' if sd.edit_tool_count != 1 else ''}")
    body = "; ".join(parts) if parts else "no edits"
    bullet = f"- **{title}** — {body}."
    if sd.pr_url and sd.pr_number:
        bullet += f" [PR #{sd.pr_number}]({sd.pr_url})"
    return bullet


def llm_bullet(sd: SessionDay, fallback: str) -> str:
    """Call claude -p with Haiku to produce a one-line summary. Fall back on failure."""
    payload = {
        "ai_title": sd.ai_title,
        "first_user_msg": (sd.first_user_msg or "")[:400],
        "last_user_msg": (sd.last_user_msg or "")[:400],
        "user_msgs_today": sd.user_msg_count,
        "files_edited_today": sd.edit_tool_count,
        "pr_number": sd.pr_number,
        "project": sd.project_label,
    }
    prompt = (
        "Summarize this Claude Code work session as ONE markdown bullet line. "
        "Format: `- **Topic** — past-tense verb phrase describing what was done.` "
        "Maximum 140 characters total. No follow-up text, no preamble. "
        f"Heuristic fallback: {fallback}\n\n"
        f"Session signals (JSON):\n{json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", LLM_MODEL],
            capture_output=True,
            text=True,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            return fallback
        out = result.stdout.strip()
        # Take only the first non-empty line; ensure it starts with "- "
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("- "):
                # Append PR if model dropped it
                if sd.pr_url and sd.pr_number and f"#{sd.pr_number}" not in line:
                    line += f" [PR #{sd.pr_number}]({sd.pr_url})"
                return line
            break
        return fallback
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return fallback


def disambiguate_labels(sessions: list[SessionDay]) -> dict[str, str]:
    """Map session_id → display project label, disambiguating collisions by parent dir."""
    by_label: dict[str, list[SessionDay]] = defaultdict(list)
    for sd in sessions:
        by_label[sd.project_label].append(sd)
    out: dict[str, str] = {}
    for label, members in by_label.items():
        cwds = {sd.cwd for sd in members if sd.cwd}
        if len(cwds) <= 1:
            for sd in members:
                out[sd.session_id] = label
        else:
            for sd in members:
                parent = sd.project_parent
                out[sd.session_id] = f"{parent}/{label}" if parent else label
    return out


def render_markdown(d: date, sessions: list[SessionDay], mode: str) -> str:
    label_map = disambiguate_labels(sessions)
    by_project: dict[str, list[SessionDay]] = defaultdict(list)
    for sd in sessions:
        by_project[label_map[sd.session_id]].append(sd)

    now_local = datetime.now().astimezone()
    out: list[str] = []
    out.append("---")
    out.append(f"date: {d.isoformat()}")
    out.append(f"generated: {now_local.isoformat(timespec='seconds')}")
    out.append(f"sessions: {len(sessions)}")
    out.append(f"mode: {mode}")
    out.append("tags: [daily-recap]")
    out.append("---")
    out.append("")
    out.append(f"# {d.isoformat()} — Daily recap")
    out.append("")

    if not sessions:
        out.append("No sessions on this date.")
        out.append("")
        return "\n".join(out)

    out.append(f"{len(sessions)} sessions across {len(by_project)} projects.")
    out.append("")

    for project in sorted(by_project.keys(), key=str.lower):
        out.append(f"## {project}")
        members = sorted(
            by_project[project],
            key=lambda s: (-s.edit_tool_count, -s.user_msg_count),
        )
        for sd in members:
            base = heuristic_bullet(sd)
            if mode == "llm":
                base = llm_bullet(sd, base)
            out.append(base)
        out.append("")

    # Raw session index
    out.append("---")
    out.append("")
    out.append("<details>")
    out.append("<summary>Raw session index</summary>")
    out.append("")
    out.append("| Project | Session | Title | User msgs | Edits | PR |")
    out.append("|---|---|---|---|---|---|")
    for sd in sorted(sessions, key=lambda s: label_map[s.session_id].lower()):
        title = (sd.ai_title or "").replace("|", "\\|")
        pr = f"#{sd.pr_number}" if sd.pr_number else ""
        out.append(
            f"| {label_map[sd.session_id]} | `{sd.session_id[:8]}…` | {title} | "
            f"{sd.user_msg_count} | {sd.edit_tool_count} | {pr} |"
        )
    out.append("")
    out.append("</details>")
    out.append("")
    return "\n".join(out)


# ---------- vault write ----------

def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------- main ----------

def gather_sessions(d: date) -> list[SessionDay]:
    start, end = day_window_local(d)
    sessions: list[SessionDay] = []
    if not PROJECTS_DIR.exists():
        return sessions
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for jsonl in project_dir.glob("*.jsonl"):
            sd = extract_session_for_day(jsonl, start, end)
            if sd is None:
                continue
            if is_near_empty(sd):
                continue
            sessions.append(sd)
    return sessions


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Daily recap of Claude Code sessions")
    p.add_argument("date", nargs="?", default=None, help="yesterday|today|YYYY-MM-DD (default: yesterday)")
    p.add_argument("--llm", action="store_true", help="Upgrade per-session bullets via Haiku")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout instead of writing to vault")
    p.add_argument("--vault", default=str(DEFAULT_VAULT), help="Obsidian vault root")
    args = p.parse_args(argv)

    d = parse_date_arg(args.date)
    if d > datetime.now().astimezone().date():
        raise SystemExit(f"error: {d.isoformat()} is in the future")

    sessions = gather_sessions(d)
    mode = "llm" if args.llm else "heuristic"
    md = render_markdown(d, sessions, mode)

    if args.dry_run:
        sys.stdout.write(md)
        return 0

    vault = Path(args.vault)
    if not vault.exists():
        raise SystemExit(f"error: vault {vault} does not exist")
    out_path = vault / "daily-recaps" / f"{d.isoformat()}.md"
    write_atomic(out_path, md)

    print(f"Wrote {out_path}")
    print(f"  {len(sessions)} sessions, mode={mode}")
    print()
    # Preview: first ~20 lines after frontmatter
    lines = md.splitlines()
    after_fm = lines
    if lines and lines[0] == "---":
        try:
            close = lines.index("---", 1)
            after_fm = lines[close + 1 :]
        except ValueError:
            pass
    preview = "\n".join(after_fm[:25])
    print(preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
