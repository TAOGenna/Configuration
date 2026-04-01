# 1) Browse all project keys (more robust than deriving from pwd)
  ls -la ~/.claude/projects/

  # 2) Set project key (pick from the listing above, or derive from pwd)
  PROJECT_KEY="$(pwd | sed 's/[^[:alnum:]]/-/g')"
  SESSION_DIR="$HOME/.claude/projects/$PROJECT_KEY"

  # 3) List recent sessions (sorted by modification time, most recent first)
  ls -lt "$SESSION_DIR"/*.jsonl 2>/dev/null | head -10

  # 4) Set session (pick from the listing above by date/size)
  SESSION="$SESSION_DIR/<uuid>.jsonl"

  # 5) List record types in a session
  jq -r '.type' "$SESSION" | sort | uniq -c | sort -rn

  # 6) Pull chat text (user + assistant messages only)
  jq -r '
    select(.type == "user" or .type == "assistant") |
    "[" + .type + "] " + (
      if (.message.content | type) == "array" then
        [.message.content[] | select(.type == "text") | .text] | join(" ")
      elif (.message.content | type) == "string" then
        .message.content
      else ""
      end
    )[:500]
  ' "$SESSION" | head -50

  # 7) Pull tool calls
  jq -r '
    select(.type == "assistant") |
    .message.content[]? |
    select(.type == "tool_use") |
    "[TOOL] " + .name + " — " + (.input | tostring)[:150]
  ' "$SESSION" | head -20

  # 8) Search for a keyword
  grep -n "keyword" "$SESSION"
