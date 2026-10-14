#!/usr/bin/env python3 -I
"""F40 — scan Cocos engine bundle + index module for wallet/WSS endpoints."""
import requests, re

HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
BASE = "https://wbgame.royalflush888.com/cc3x5"

def scan(url, label):
    r = requests.get(url, headers=HDRS, timeout=20)
    print(f"\n[{label}] {url[-60:]} status={r.status_code} len={len(r.text)}")
    jt = r.text

    ws = re.findall(r'wss?://[^\s"\'\\`<>]{5,120}', jt)
    if ws:
        print(f"  [WSS]: {sorted(set(ws))}")

    royalflush = re.findall(r'["\`]([^"\`\s]{0,30}royalflush[^"\`\s]{0,80})["\`]', jt)
    if royalflush:
        print(f"  [royalflush]: {sorted(set(royalflush))}")

    credit = re.findall(r'["\`]([^"\`\s]{0,20}credit[^"\`\s]{0,60})["\`]', jt, re.I)
    if credit:
        print(f"  [credit]: {sorted(set(credit))}")

    wallet = re.findall(r'["\`]([^"\`\s]{0,20}wallet[^"\`\s]{0,60})["\`]', jt, re.I)
    if wallet:
        print(f"  [wallet]: {sorted(set(wallet))}")

    # Look for HTTP paths
    paths = re.findall(r'"(/[a-zA-Z][a-zA-Z0-9/_-]{3,60})"', jt)
    interesting = [p for p in set(paths) if any(k in p.lower() for k in
        ["credit","wallet","debit","balance","bet","win","callback","seamless","game","api"])]
    if interesting:
        print(f"  [api-paths]: {sorted(interesting)}")

# Main index module
scan(f"{BASE}/index.7bd12.js", "index")

# Cocos CC bundle (the big one — lazy-loaded game scripts are inside)
# It's at ../../cocos-js/cc.af2c4.js relative to the game page
scan("https://wbgame.royalflush888.com/cocos-js/cc.af2c4.js", "cocos-cc")

# Also check if there are additional bundles referenced from index
r = requests.get(f"{BASE}/index.7bd12.js", headers=HDRS, timeout=10)
print(f"\n[index-raw] {r.text}")
