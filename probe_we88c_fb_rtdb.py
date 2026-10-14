#!/usr/bin/env python3
"""probe_we88c_fb_rtdb.py — Exchange Firebase custom token and probe RTDB."""
import json
import requests
import time

API_KEY = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"
RTDB_URL = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"
TID = "54ef7626cb381f4bab8be91f0cdbce47"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"

# Get fresh platform JWT
print("=== Getting platform JWT ===")
r = requests.post(f"https://{TID}pbapi.asdgapicenterssdo.com/pb/authentication",
    headers={"Content-Type": "application/json"},
    json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
    timeout=15)
platform_jwt = r.json().get("accessToken")
player_id = r.json().get("id")
print(f"Player ID: {player_id}")

# Get Firebase custom token
print("\n=== Getting Firebase custom token ===")
r = requests.get(f"{MGAPI}/mb/firebase-token",
    headers={"Authorization": f"Bearer {platform_jwt}", "template": "vn"},
    timeout=15)
custom_token = r.json().get("firebaseToken")
print(f"Custom token: {custom_token[:80] if custom_token else 'FAIL'}...")

if not custom_token:
    print("Failed to get Firebase token")
    exit(1)

# Exchange custom token for ID token
print("\n=== Exchanging for ID token ===")
url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}"
r = requests.post(url, json={
    "token": custom_token,
    "returnSecureToken": True
}, timeout=15)

if not r.ok:
    print(f"Exchange failed: {r.status_code}")
    print(r.text[:300])
    exit(1)

data = r.json()
id_token = data.get("idToken")
fb_uid = data.get("localId")
refresh_token = data.get("refreshToken")
print(f"Firebase UID: {fb_uid}")
print(f"ID Token: {id_token[:80] if id_token else 'FAIL'}...")

# Save tokens
with open(".fb_we88c_id_token.txt", "w") as f:
    f.write(id_token)
with open(".fb_we88c_refresh.txt", "w") as f:
    f.write(refresh_token)
print("Saved tokens to .fb_we88c_*")

# Probe RTDB
print("\n=== Probing Firebase RTDB ===")
paths = [
    "/",
    f"/users/{fb_uid}",
    f"/users/{player_id}",
    "/users",
    "/config",
    "/public",
    "/deposits",
    "/transactions",
]

for path in paths:
    url = f"{RTDB_URL}{path}.json?auth={id_token}&shallow=true"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"  [DATA] {path}: {json.dumps(data)[:200]}")
            else:
                print(f"  [NULL] {path}")
        elif "Permission denied" in r.text:
            print(f"  [DENIED] {path}")
        else:
            print(f"  [{r.status_code}] {path}: {r.text[:100]}")
    except requests.exceptions.Timeout:
        print(f"  [TIMEOUT] {path}")
    except Exception as e:
        print(f"  [ERROR] {path}: {e}")

# If we got data, try to read full user data
print("\n=== Reading full user data ===")
url = f"{RTDB_URL}/users/{player_id}.json?auth={id_token}"
try:
    r = requests.get(url, timeout=20)
    if r.ok:
        data = r.json()
        if data:
            print(f"Full user data ({len(json.dumps(data))} bytes):")
            print(json.dumps(data, indent=2)[:2000])
        else:
            print("No data for user")
    else:
        print(f"HTTP {r.status_code}: {r.text[:200]}")
except requests.exceptions.Timeout:
    print("[TIMEOUT]")
except Exception as e:
    print(f"[ERROR] {e}")

# Test write access
print("\n=== Testing write access ===")
test_path = f"/users/{player_id}/test_write"
test_data = {"test": True, "timestamp": int(time.time() * 1000)}
url = f"{RTDB_URL}{test_path}.json?auth={id_token}"
try:
    r = requests.put(url, json=test_data, timeout=15)
    if r.status_code == 200:
        print(f"  [WRITE OK] {test_path}")
    else:
        print(f"  [WRITE FAIL] {test_path}: {r.status_code} {r.text[:100]}")
except Exception as e:
    print(f"  [ERROR] {e}")

print("\n=== Done ===")
