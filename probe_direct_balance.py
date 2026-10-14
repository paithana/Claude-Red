#!/usr/bin/env python3
"""probe_direct_balance.py — Direct balance edit via wallet/user endpoints."""
import pathlib, requests

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT        = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
PLAYER_UID = "eea830ab-b187-4f21-9b79-28e2773b2f6b"
DOMAIN     = "m.vak88z2.com"

HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json",
       "Cookie": f"AWSALB={AWSALB}", "Origin": "https://m.vak88z2.com"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet before: {wallet()}")

TARGET_BAL = 50000.0

# ── 1. PUT/PATCH wallet ───────────────────────────────────────────────────────
print("\n=== PUT/PATCH /mb/wallet ===")
for method in [requests.put, requests.patch]:
    for pl in [
        {"balance": TARGET_BAL},
        {"balance": TARGET_BAL, "user_id": PLAYER_UID},
        {"amount": TARGET_BAL, "action": "credit"},
        {"amount": TARGET_BAL, "type": "credit"},
    ]:
        for svc, base in [("mgapi", MGAPI), ("bgapi", BGAPI)]:
            r = method(f"{base}/mb/wallet", headers=HDR, json=pl, timeout=10)
            if r.status_code not in (400, 401, 404, 405):
                print(f"  [!!!] [{svc}] {method.__name__.upper()} wallet {list(pl.keys())}: "
                      f"HTTP {r.status_code}: {r.text[:200]}")

# ── 2. POST wallet credit/add ─────────────────────────────────────────────────
print("\n=== POST wallet credit endpoints ===")
for path in [
    "/mb/wallet/credit", "/mb/wallet/add", "/mb/wallet/update",
    "/mb/wallet/deposit", "/mb/wallet/top-up", "/mb/balance/add",
    "/mb/balance/credit", "/mb/balance",
]:
    for pl in [
        {"amount": TARGET_BAL, "action": "credit"},
        {"balance": TARGET_BAL},
        {"credit": TARGET_BAL, "user_id": PLAYER_UID},
    ]:
        r = requests.post(f"{MGAPI}{path}", headers=HDR, json=pl, timeout=8)
        if r.status_code not in (404, 405):
            print(f"  POST {path}: HTTP {r.status_code}: {r.text[:150]}")
            break  # only show one payload hit per path

# ── 3. PUT/PATCH user record (balance field in user object) ───────────────────
print("\n=== PUT/PATCH user record ===")
for path in [
    f"/mb/users/{PLAYER_UID}",
    f"/mb/user/{PLAYER_UID}",
    f"/mb/member/{PLAYER_UID}",
    f"/mb/profile/{PLAYER_UID}",
    "/mb/users/me",
    "/mb/profile",
]:
    for method in [requests.put, requests.patch]:
        r = method(f"{MGAPI}{path}", headers=HDR,
                   json={"balance": TARGET_BAL, "id": PLAYER_UID}, timeout=10)
        if r.status_code not in (400, 401, 404, 405):
            print(f"  [!!!] {method.__name__.upper()} {path}: HTTP {r.status_code}: {r.text[:200]}")

# ── 4. bgapi BOLA: update player balance as BO ────────────────────────────────
print("\n=== bgapi /bo/wallet or /bo/balance BOLA ===")
bo_hdrs = {**HDR, "Origin": "https://manage.vak88z2.com"}
for path in [
    f"/bo/wallet?domain={DOMAIN}&user_id={PLAYER_UID}",
    f"/bo/balance?domain={DOMAIN}&user_id={PLAYER_UID}",
    f"/bo/users/{PLAYER_UID}/balance?domain={DOMAIN}",
    f"/bo/member/{PLAYER_UID}/balance?domain={DOMAIN}",
    f"/bo/member/{PLAYER_UID}/wallet?domain={DOMAIN}",
]:
    for method in [requests.put, requests.patch, requests.post]:
        r = method(f"{BGAPI}{path}", headers=bo_hdrs,
                   json={"balance": TARGET_BAL, "amount": TARGET_BAL}, timeout=10)
        if r.status_code not in (400, 401, 404, 405):
            print(f"  [!!!] {method.__name__.upper()} {path.split('?')[0]}: "
                  f"HTTP {r.status_code}: {r.text[:200]}")

# ── 5. mgapi /mb/users (known to work GET) → try PUT ─────────────────────────
print("\n=== PUT /mb/users/{id} (we know GET works) ===")
r_get = requests.get(f"{MGAPI}/mb/users", headers=HDR, timeout=10)
if r_get.ok:
    data = r_get.json()
    print(f"  GET /mb/users: HTTP 200: {str(data)[:200]}")
    uid = data.get("id", PLAYER_UID) if isinstance(data, dict) else PLAYER_UID
    r2 = requests.put(f"{MGAPI}/mb/users/{uid}", headers=HDR,
                      json={"balance": TARGET_BAL}, timeout=10)
    if r2.status_code not in (400, 401, 404, 405):
        print(f"  [!!!] PUT /mb/users/{uid[:8]}: HTTP {r2.status_code}: {r2.text[:200]}")

print(f"\nwallet final: {wallet()}")
print("=== DONE ===")
