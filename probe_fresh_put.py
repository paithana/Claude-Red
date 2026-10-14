#!/usr/bin/env python3
"""probe_fresh_put.py — Create deposit and immediately try PUT approve on full UUID.

   Previous PUT probes failed because we only had 8-char partial IDs.
   This probe captures the full UUID from creation response, then PUTs immediately.

   Also: BOLA via bgapi — list deposits for specific user_id with player JWT.
"""
import json, pathlib, requests, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json",
       "Cookie": f"AWSALB={AWSALB}"}

BANK_INFO  = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT   = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"
PLAYER_UID = "eea830ab-b187-4f21-9b79-28e2773b2f6b"
KNOWN_TX   = "3d939de8-a02c-4d3b-9ae1-fa8737737cb5"

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet before: {wallet()}")

# ── 1. Create deposit, capture full UUID, immediately PUT ─────────────────────
print("\n=== Create + immediate PUT ===")
r = requests.post(f"{MGAPI}/mb/deposit-transaction",
                  headers=HDR,
                  json={"deposit_amount": 10000.0, "is_auto_slip": True,
                        "payment_bank_information_id": BANK_INFO,
                        "deposit_account_id": DEP_ACCT},
                  timeout=12)
if r.ok:
    d = r.json()
    dep_id = d.get("id", "")
    bal_after = d.get("balance_after_deposit", "?")
    print(f"  Created: id={dep_id}  status={d.get('approve_status','?')}  bal_after={bal_after}")

    if dep_id:
        put_payloads = [
            {"approve_status": "success", "status": "success"},
            {"approve_status": "success", "transaction_id": KNOWN_TX},
            {"approve_status": "success", "is_match_slip": True, "transaction_id": KNOWN_TX},
            {"status": "success", "credited": True},
            {"approve_status": "success", "approved_by": "5958356c-eb4e-4e07-a155-83e4382e3532"},
            # /mb/deposit/add with id
            {"id": dep_id, "approve_status": "success"},
        ]
        for pl in put_payloads:
            for svc, base in [("mgapi", MGAPI), ("bgapi", BGAPI), ("pbapi", PBAPI)]:
                r2 = requests.put(f"{base}/mb/deposit-transaction/{dep_id}",
                                  headers={**HDR, "Origin": "https://manage.vak88z2.com"},
                                  json=pl, timeout=10)
                if r2.status_code not in (400, 401, 404, 405, 500):
                    print(f"  [!!!] [{svc}] PUT {pl}: HTTP {r2.status_code}: {r2.text[:300]}")
                    if r2.ok and r2.json().get("approve_status") in ("success","approved"):
                        print(f"  [!!!!!!] APPROVED! wallet: {wallet()}")
                elif r2.status_code == 200:
                    print(f"  [{svc}] PUT 200: {r2.text[:200]}")
else:
    print(f"  CREATE FAILED: HTTP {r.status_code}: {r.text[:100]}")

# ── 2. BOLA — list player deposits via bgapi with user_id param ───────────────
print("\n=== BOLA: bgapi deposit list by user_id ===")
bo_hdrs = {**HDR, "Origin": "https://manage.vak88z2.com"}
for path in [
    f"/bo/deposit-transaction?domain=m.vak88z2.com&user_id={PLAYER_UID}&skip=0&limit=20",
    f"/bo/deposit-transaction?domain=m.vak88z2.com&member_id={PLAYER_UID}&skip=0&limit=20",
    f"/bo/deposit-transaction?domain=m.vak88z2.com&player_id={PLAYER_UID}&skip=0&limit=20",
    f"/bo/deposit-history?domain=m.vak88z2.com&user_id={PLAYER_UID}&skip=0&limit=20",
    f"/bo/slip-deposit?domain=m.vak88z2.com&user_id={PLAYER_UID}&skip=0&limit=20",
    f"/bo/info/deposit-transaction?domain=m.vak88z2.com&user_id={PLAYER_UID}",
]:
    r = requests.get(f"{BGAPI}{path}", headers=bo_hdrs, timeout=10)
    if r.ok:
        data = r.json()
        items = data if isinstance(data, list) else data.get("data", data.get("items", [data]))
        print(f"  [!!!] {path.split('?')[0]}: HTTP 200 ({len(items) if isinstance(items,list) else '?'})")
        if isinstance(items, list):
            for it in items[:5]:
                dep_id2 = it.get("id","")
                status = it.get("approve_status", it.get("status","?"))
                amt = it.get("deposit_amount", it.get("amount","?"))
                print(f"    id={dep_id2}  status={status}  amt={amt}")
                # Immediately try to approve
                if status == "waiting" and dep_id2:
                    r3 = requests.put(f"{MGAPI}/mb/deposit-transaction/{dep_id2}",
                                      headers=HDR,
                                      json={"approve_status": "success", "transaction_id": KNOWN_TX},
                                      timeout=10)
                    print(f"    -> PUT approve: HTTP {r3.status_code}: {r3.text[:100]}")
    elif r.status_code not in (404, 405):
        print(f"  {path.split('?')[0]}: HTTP {r.status_code}: {r.text[:80]}")

# ── 3. Try PATCH instead of PUT ───────────────────────────────────────────────
print("\n=== PATCH /mb/deposit-transaction/{id} ===")
r = requests.post(f"{MGAPI}/mb/deposit-transaction",
                  headers=HDR,
                  json={"deposit_amount": 1000.0, "is_auto_slip": True,
                        "payment_bank_information_id": BANK_INFO,
                        "deposit_account_id": DEP_ACCT},
                  timeout=12)
if r.ok:
    patch_id = r.json().get("id", "")
    print(f"  Created for PATCH: {patch_id}")
    for pl in [
        {"approve_status": "success"},
        {"approve_status": "success", "status": "success"},
        {"status": "success", "transaction_id": KNOWN_TX},
    ]:
        for svc, base in [("mgapi", MGAPI), ("bgapi", BGAPI)]:
            r2 = requests.patch(f"{base}/mb/deposit-transaction/{patch_id}",
                                headers={**HDR, "Origin": "https://manage.vak88z2.com"},
                                json=pl, timeout=10)
            if r2.status_code not in (400, 401, 404, 405, 500):
                print(f"  [!!!] [{svc}] PATCH {list(pl.keys())}: HTTP {r2.status_code}: {r2.text[:300]}")

# ── 4. /bo/deposit-transaction POST approve with player JWT ───────────────────
print("\n=== POST /bo/deposit-transaction (BO approve path) ===")
for path in [
    "/bo/deposit-transaction",
    "/bo/deposit-transaction/approve",
    "/bo/deposit-transaction/success",
    "/bo/slip-deposit-approve",
]:
    r = requests.post(f"{BGAPI}{path}?domain=m.vak88z2.com",
                      headers=bo_hdrs,
                      json={"deposit_id": dep_id, "approve_status": "success",
                            "user_id": PLAYER_UID, "amount": 10000.0},
                      timeout=10)
    if r.status_code not in (401, 404, 405):
        print(f"  [!!!] POST {path}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        print(f"  POST {path}: HTTP {r.status_code}")

print(f"\nwallet final: {wallet()}")
print("=== DONE ===")
