#!/usr/bin/env python3
"""probe_rtdb_cashback.py — Check RTDB for cashback/affiliate data."""
import json
import requests

TID = "54ef7626cb381f4bab8be91f0cdbce47"
API_KEY = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"
RTDB_URL = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"
PLAYER_ID = "266d74e3-d6ca-47eb-b9ac-b8c45574bad4"

# Get fresh tokens
JWT = open(".jwt.we88c").read().strip()

# Get Firebase ID token
r = requests.get(f"https://{TID}mgapi.asdgapicenterssdo.com/mb/firebase-token",
    headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
    timeout=15)
custom_token = r.json().get("firebaseToken")

r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}",
    json={"token": custom_token, "returnSecureToken": True},
    timeout=15)
fb_token = r.json().get("idToken")

# Check user data in RTDB
print("=== RTDB User Data ===")
url = f"{RTDB_URL}/users/{PLAYER_ID}.json?auth={fb_token}"
r = requests.get(url, timeout=15)
if r.ok:
    data = r.json()
    print(json.dumps(data, indent=2)[:2000] if data else "null")

# Check for cashback/affiliate paths
print("\n=== Checking cashback/affiliate paths ===")
paths = [
    f"/users/{PLAYER_ID}/cashback",
    f"/users/{PLAYER_ID}/affiliate",
    f"/users/{PLAYER_ID}/rebate",
    f"/users/{PLAYER_ID}/bonus",
    f"/users/{PLAYER_ID}/promotion",
    f"/cashback/{PLAYER_ID}",
    f"/affiliate/{PLAYER_ID}",
    f"/rebate/{PLAYER_ID}",
]

for path in paths:
    url = f"{RTDB_URL}{path}.json?auth={fb_token}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        data = r.json()
        if data is not None:
            print(f"  [DATA] {path}: {json.dumps(data)[:150]}")
        else:
            print(f"  [NULL] {path}")

# Try to write cashback to RTDB
print("\n=== Attempting to write cashback ===")
import time
test_data = {
    "available": 99999.0,
    "balance": 99999.0,
    "claimable": 99999.0,
    "timestamp": int(time.time() * 1000)
}

url = f"{RTDB_URL}/users/{PLAYER_ID}/cashback.json?auth={fb_token}"
r = requests.put(url, json=test_data, timeout=15)
print(f"Write cashback: {r.status_code}")
if r.ok:
    print(f"  Response: {r.text[:150]}")

# Try cashback-transfer again
print("\n=== Retry cashback-transfer ===")
r = requests.post(f"https://{TID}mgapi.asdgapicenterssdo.com/mb/cashback-transfer",
    headers={"Authorization": f"Bearer {JWT}", "Content-Type": "application/json", "template": "vn"},
    json={"amount": 1000},
    timeout=15)
print(f"cashback-transfer: {r.status_code}")
print(f"  Response: {r.text[:200]}")

# Check platform cashback
print("\n=== Platform cashback status ===")
r = requests.get(f"https://{TID}mgapi.asdgapicenterssdo.com/mb/cashback-transaction",
    headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
    timeout=15)
print(r.json())
