#!/usr/bin/env python3 -I
"""scan_transcripts.py — Extract frequent read-only bash/MCP commands from transcripts."""
import json, pathlib, re, sys
from collections import Counter

PROJECTS = pathlib.Path.home() / ".claude" / "projects"
jsonls = sorted(
    [f for f in PROJECTS.rglob("*.jsonl")],
    key=lambda f: f.stat().st_mtime,
    reverse=True
)[:50]

print(f"Scanning {len(jsonls)} transcript files...\n", file=sys.stderr)

bash_cmds: Counter = Counter()
mcp_tools: Counter = Counter()

# Commands already auto-allowed — skip these
AUTO_ALLOWED = {
    "cal","uptime","cat","head","tail","wc","stat","strings","hexdump","od",
    "nl","id","uname","free","df","du","locale","groups","nproc","basename",
    "dirname","realpath","cut","paste","tr","column","tac","rev","fold",
    "expand","unexpand","fmt","comm","cmp","numfmt","readlink","diff","true",
    "false","sleep","which","type","expr","seq","tsort","pr","echo","ls","cd",
    "pwd","whoami","alias","git","gh","docker","rg","grep","egrep","fgrep",
    "jq","find","sed","sort","ps","date","file","xargs","base64","sha256sum",
    "sha1sum","md5sum","tree","hostname","lsof","pgrep","tput","ss","fd",
    "fdfind","uniq","history","arch","ifconfig","netstat",
}

# Interpreters / shells — never allowlist wildcards for these
UNSAFE = {
    "python","python3","node","bun","deno","ruby","perl","php","lua",
    "bash","sh","zsh","fish","eval","exec","ssh","npx","bunx","uvx",
    "uv","make","just","cargo","go","pyright","sudo","docker run",
    "kubectl exec",
}

def leading_tokens(cmd: str) -> tuple[str, str]:
    """Return (cmd0, cmd0+cmd1) stripping env prefixes and pipes."""
    # Strip env var assignments at start
    cmd = re.sub(r'^\s*([A-Z_]+=\S+\s+)+', '', cmd).strip()
    # Take first pipeline segment
    cmd = cmd.split("|")[0].strip()
    # Take first &&/; segment
    cmd = re.split(r'&&|;', cmd)[0].strip()
    tokens = cmd.split()
    if not tokens:
        return ("", "")
    t0 = tokens[0].lstrip("./")
    t1 = tokens[1] if len(tokens) > 1 else ""
    return (t0, f"{t0} {t1}".strip())

for f in jsonls:
    try:
        for line in f.read_text(errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("type") != "assistant":
                continue
            msg = obj.get("message", {})
            for block in msg.get("content", []):
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = block.get("name", "")
                inp  = block.get("input", {})
                if name == "Bash":
                    cmd = inp.get("command", "")
                    t0, t01 = leading_tokens(cmd)
                    if t0 and t0 not in AUTO_ALLOWED and t0 not in UNSAFE:
                        bash_cmds[t01 or t0] += 1
                elif name.startswith("mcp__") or "__" in name:
                    mcp_tools[name] += 1
    except Exception:
        continue

print("=== TOP BASH COMMANDS (non-auto-allowed, potentially allowable) ===")
for cmd, count in bash_cmds.most_common(40):
    print(f"  {count:4d}  {cmd}")

print("\n=== TOP MCP TOOLS ===")
for tool, count in mcp_tools.most_common(30):
    print(f"  {count:4d}  {tool}")
