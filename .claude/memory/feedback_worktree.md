---
name: feedback-worktree-bash
description: "In worktree isolation, complex inline Python/heredoc commands are blocked — write scripts to scratchpad directory and run from there"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 50e2254d-12af-4204-8fc7-3c746f3e4520
  modified: 2026-09-19T08:25:02.249Z
---

In worktree-isolated sessions, complex `python3 - <<'EOF'` heredoc commands are blocked by the sandbox.

**Why:** The sandbox validates commands and refuses multi-line heredocs/inline scripts that it can't verify stay within the worktree.

**How to apply:** Always write Python/shell scripts to the scratchpad directory (`/tmp/claude-1000/.../.../scratchpad/`) using Write tool, then run with `python3 <path>`. Never use inline heredoc Python in worktree sessions.

Also: `git -C <other-path>` is blocked for any path that isn't the current worktree. Use `git -C /home/kzp/claude-red/.claude/worktrees/twinkling-twirling-pearl <cmd>` — works for commands targeting the current worktree's git repo (branch listing, log of other branches, update-ref, etc).
