#!/usr/bin/env python3
"""probe_dl_bo_js.py — Download and grep BO Nuxt JS chunks for API endpoints + auth."""
import re, requests, pathlib

BO_BASE = "https://manage.vak88z2.com"
OUT_DIR = pathlib.Path("/home/kzp/.claude/jobs/546de6d5/tmp/bo_js")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# JS chunks from /account/login page
CHUNKS = [
    "/_nuxt/60456cc.js",
    "/_nuxt/3ef060e.js",
    "/_nuxt/33bd344.js",
    "/_nuxt/3bdb0c1.js",
]

# Also fetch the main page to find more chunks
print("=== Fetching main page for chunk list ===")
r = requests.get(f"{BO_BASE}/account/login", timeout=10)
extra_chunks = re.findall(r'"(/_nuxt/[a-f0-9]+\.js)"', r.text)
all_chunks = list(dict.fromkeys(CHUNKS + extra_chunks))
print(f"  Found {len(all_chunks)} chunks total")

all_text = ""
for chunk in all_chunks:
    url = f"{BO_BASE}{chunk}"
    try:
        r = requests.get(url, timeout=15)
        if r.ok:
            fname = OUT_DIR / chunk.split("/")[-1]
            fname.write_text(r.text)
            all_text += r.text
            print(f"  Downloaded {chunk} ({len(r.text)}B)")
        else:
            print(f"  FAIL {chunk}: {r.status_code}")
    except Exception as e:
        print(f"  ERR {chunk}: {e}")

print(f"\nTotal JS: {len(all_text)}B")

# ── Extract interesting patterns ──────────────────────────────────────────────
print("\n=== API endpoints ===")
# Paths with /bo/ or /mb/ or /pb/
paths = re.findall(r'["\`]([/](?:bo|mb|pb|api)[/][^\s"\'`]{3,60})["\`]', all_text)
unique_paths = sorted(set(paths))
for p in unique_paths[:60]:
    print(f"  {p}")

print("\n=== Header/key patterns ===")
# Internal headers, API keys, secrets
header_patterns = re.findall(r'["\'](x-[a-z-]{5,40})["\']', all_text, re.I)
for h in sorted(set(header_patterns))[:20]:
    print(f"  header: {h}")

key_patterns = re.findall(r'(?:apiKey|api_key|serviceKey|internalKey|secret)["\s]*[:=]["\s]*([^\s"\'}{,;]{8,})', all_text, re.I)
for k in key_patterns[:10]:
    print(f"  key: {k[:60]}")

print("\n=== Auth flow (axios/fetch interceptors) ===")
# Look for Authorization header construction
auth_snippets = re.findall(r'.{0,100}[Aa]uthorization.{0,150}', all_text)
for s in auth_snippets[:10]:
    print(f"  {s[:200]}")

print("\n=== deposit/approve/task references ===")
for kw in ["deposit", "approve", "assign-task", "slip", "task"]:
    hits = re.findall(rf'.{{0,40}}{kw}.{{0,80}}', all_text, re.I)
    for h in hits[:5]:
        print(f"  [{kw}] {h[:160]}")

print("=== DONE ===")
