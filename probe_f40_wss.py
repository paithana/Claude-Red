#!/usr/bin/env python3 -I
"""F40 — extract import-map modules + scan for WSS wallet endpoints."""
import requests, re, json

GAME_BASE = "https://wbgame.royalflush888.com/cc3x5"
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Fetch import map
r = requests.get(f"{GAME_BASE}/src/import-map.e7209.json", headers=HDRS, timeout=10)
print(f"[import-map] {r.text}")

# Fetch HTML and extract all script/module references
r2 = requests.get(GAME_BASE + "/", headers=HDRS, timeout=10)
html = r2.text

# Find inline script content and all referenced URLs
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(scripts):
    if s.strip():
        print(f"\n[inline-script-{i}] {s[:500]}")

# Look for any ws:// or wss:// in HTML
ws_hits = re.findall(r'wss?://[^\s"\'<>]+', html)
if ws_hits:
    print(f"\n[wss-in-html] {ws_hits}")

# Fetch the main app bundle — often lazy-loaded, try common names
extra_bundles = [
    "/src/app.bundle.js", "/src/main.js", "/src/main.bundle.js",
    "/src/vendor.js", "/src/runtime.js",
]
for b in extra_bundles:
    try:
        br = requests.get(f"{GAME_BASE}{b}", headers=HDRS, timeout=5)
        if br.status_code == 200 and len(br.text) > 100:
            jt = br.text
            print(f"\n[bundle] {b} len={len(jt)}")
            ws = re.findall(r'wss?://[^\s"\'\\`<>]{5,100}', jt)
            if ws: print(f"  WSS: {ws}")
            paths = re.findall(r'["\`](/(?:api|v[0-9]|game|wallet|seamless|credit)[^"\`<>]{2,60})["\`]', jt)
            if paths: print(f"  paths: {sorted(set(paths))}")
    except Exception:
        pass

# Also try fetching the HTML source looking for SystemJS/lazy load patterns
system_patterns = re.findall(r'System\.import\(["\']([^"\']+)["\']', html)
if system_patterns:
    print(f"\n[SystemJS imports] {system_patterns}")
    for mod in system_patterns:
        from urllib.parse import urljoin
        mod_url = urljoin(GAME_BASE + "/", mod)
        try:
            mr = requests.get(mod_url, headers=HDRS, timeout=10)
            if mr.status_code == 200:
                jt = mr.text
                print(f"\n[module] {mod_url[:80]} len={len(jt)}")
                ws = re.findall(r'wss?://[^\s"\'\\`<>]{5,100}', jt)
                if ws: print(f"  WSS: {ws}")
                royalflush = re.findall(r'["\`]([^"\`]*royalflush[^"\`]{0,80})["\`]', jt)
                if royalflush: print(f"  royalflush refs: {sorted(set(royalflush))}")
                credit_paths = re.findall(r'["\`](/[a-zA-Z0-9/_-]*credit[^"\`<>]{0,40})["\`]', jt)
                if credit_paths: print(f"  credit paths: {sorted(set(credit_paths))}")
        except Exception as e:
            print(f"  ERR: {e!s:.60}")
