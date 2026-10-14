#!/usr/bin/env python3
"""probe_search_ws.py — Find WebSocket URL from BO JS bundle."""
import re, pathlib

NUXT = pathlib.Path("/home/kzp/claude-red/nuxt")

for js in sorted(NUXT.glob("*.js"), key=lambda f: f.stat().st_size, reverse=True):
    content = js.read_text(errors='ignore')
    print(f"\n{'='*60}")
    print(f"=== {js.name} ({len(content)//1024}KB) ===")

    patterns = [
        (r'wss?://.{0,200}', "WebSocket URL literal"),
        (r'"wss://"\s*\+\s*.{0,200}|"wss://".concat\(.{0,200}', "wss concat pattern"),
        (r'new\s+(?:WebSocket|Socket|m)\s*\(\s*["\']wss?.{0,200}', "WS constructor"),
        (r'var\s+[a-z]\s*=\s*["\'][^"\']*(?:vak88|bgapi|mgapi|ws)[^"\']*["\']', "domain var"),
        (r'browserBaseURL|socketBaseURL|wsBaseURL|socketURL', "WS base URL var"),
        (r'\.asdgapicenterssdo\.com', "API domain in bundle"),
        (r'\.vak88z2\.com|\.vak88[a-z0-9]', "vak88 domain"),
        (r'socket\.io|SocketIO|io\s*\(', "Socket.io"),
        (r'luxino\._token|_token\.local', "token cookie"),
        # Context around wss// variable resolution
        (r'[a-z]\s*=\s*["\']\s*["\']\s*,\s*[a-z]\s*=\s*.{0,300}wss', "wss var context"),
    ]

    for pat, label in patterns:
        hits = list(re.finditer(pat, content, re.IGNORECASE | re.DOTALL))
        if hits:
            print(f"\n  [{label}]")
            for m in hits[:3]:
                start = max(0, m.start() - 80)
                end = min(len(content), m.end() + 400)
                ctx = content[start:end].replace('\n', ' ')
                print(f"    {ctx[:600]}")
