# 1) Derive project key
  PROJECT_KEY="$(pwd | sed 's/[^[:alnum:]]/-/g')"
  SESSION_DIR="$HOME/.claude/projects/$PROJECT_KEY"

  # 2) Most recent session
  SESSION="$(find "$SESSION_DIR" -maxdepth 1 -type f -name '*.jsonl' | sort | tail -n 1)"
  echo "SESSION=$SESSION"

  # 3) List record types in a session
  jq -r '.type' "$SESSION" | sort | uniq -c | sort -rn

  # 4) Pull chat text (user + assistant messages only)
  jq -r '
    select(.type == "user" or .type == "assistant") |
    "[" + .type + "] " + (
      if (.message.content | type) == "array" then
        [.message.content[] | select(.type == "text") | .text] | join(" ")
      elif (.message.content | type) == "string" then
        .message.content
      else ""
      end
    )[:200]
  ' "$SESSION" | head -50

  # 5) Pull tool calls
  jq -r '
    select(.type == "assistant") |
    .message.content[]? |
    select(.type == "tool_use") |
    "[TOOL] " + .name + " — " + (.input | tostring)[:150]
  ' "$SESSION" | head -20

  # 6) Search for a keyword
  grep -n "keyword" "$SESSION"

  # 7) List recent sessions (by modification time, most recent last)
  ls -lt "$SESSION_DIR"/*.jsonl 2>/dev/null | head -10
