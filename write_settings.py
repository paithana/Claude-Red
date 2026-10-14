#!/usr/bin/env python3
import json, pathlib

settings = {
  "model": "claude-opus-5-5",
  "modelSettings": {"claude-opus-5-5": {"effortLevel": "high"}},
  "permissions": {
    "defaultMode": "auto",
    "allow": [
      "mcp__claude-in-chrome__read_page",
      "mcp__claude-in-chrome__read_network_requests",
      "mcp__claude-in-chrome__tabs_context_mcp",
      "mcp__claude-in-chrome__find",
      "mcp__claude-in-chrome__get_page_text",
      "mcp__claude-in-chrome__read_console_messages",
      "mcp__claude-in-chrome__navigate",
      "mcp__claude-in-chrome__tabs_close_mcp",
      "mcp__claude_ai_NotFair-GoogleAds__executeRead",
      "mcp__claude_ai_NotFair-GoogleAds__search",
      "mcp__claude_ai_Google_Drive__read_file_content",
      "mcp__claude_ai_Trello__trelloReadCard",
      "mcp__claude_ai_Trello__trelloReadBoard",
      "mcp__claude_ai_Trello__trelloReadList",
      "mcp__claude_ai_Trello__trelloSearch",
      "mcp__playwright__browser_take_screenshot",
      "mcp__playwright__browser_navigate"
    ]
  },
  "worktree": {"bgIsolation": "none"}
}

p = pathlib.Path("/home/kzp/claude-red/.claude/settings.json")
p.write_text(json.dumps(settings, indent=2) + "\n")
print(f"Written {p} ({p.stat().st_size} bytes)")
print(json.dumps(settings, indent=2))
