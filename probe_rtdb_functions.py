#!/usr/bin/env python3
"""probe_rtdb_functions.py — Check for Firebase Cloud Functions triggers."""
import json
import requests
import time

TID = "54ef7626cb381f4bab8be91f0cdbce47"
API_KEY = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"
PROJECT_ID = "we88zz"

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
fb_uid = r.json().get("localId")
print(f"Firebase UID: {fb_uid}")

# 1. Check for Cloud Functions endpoints
print("\n=== Checking Cloud Functions ===")
cf_endpoints = [
    f"https://us-central1-{PROJECT_ID}.cloudfunctions.net",
    f"https://asia-southeast1-{PROJECT_ID}.cloudfunctions.net",
    f"https://{PROJECT_ID}.cloudfunctions.net",
    f"https://firebasestorage.googleapis.com/v0/b/{PROJECT_ID}.appspot.com",
]

for ep in cf_endpoints:
    try:
        r = requests.get(ep, timeout=5)
        print(f"  {ep}: {r.status_code}")
    except Exception as e:
        print(f"  {ep}: {str(e)[:50]}")

# 2. Check Firebase Functions info API
print("\n=== Firebase Functions API ===")
funcs_urls = [
    f"https://cloudfunctions.googleapis.com/v1/projects/{PROJECT_ID}/locations/-/functions",
    f"https://firebasehosting.googleapis.com/v1beta1/sites/{PROJECT_ID}",
]
for url in funcs_urls:
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {fb_token}"}, timeout=10)
        print(f"  {url.split('/')[-1]}: {r.status_code}")
        if r.ok:
            print(f"    {r.text[:200]}")
    except Exception as e:
        print(f"  ERROR: {str(e)[:50]}")

# 3. Check if there's a credit_wallet or process_deposit function
print("\n=== Probing common function names ===")
common_funcs = [
    "creditWallet", "processDeposit", "approveDeposit", "updateBalance",
    "onDepositWrite", "onDepositApprove", "syncWallet", "webhook",
    "onWrite", "processPayment", "creditBalance", "addBalance"
]

for func in common_funcs:
    for region in ["us-central1", "asia-southeast1"]:
        url = f"https://{region}-{PROJECT_ID}.cloudfunctions.net/{func}"
        try:
            r = requests.post(url, json={"test": True}, timeout=3)
            if r.status_code != 404:
                print(f"  [{r.status_code}] {func} ({region})")
                if r.ok:
                    print(f"    Response: {r.text[:100]}")
        except:
            pass

# 4. Check RTDB .info paths
print("\n=== RTDB .info paths ===")
RTDB_URL = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"
info_paths = [
    "/.info/connected",
    "/.info/serverTimeOffset",
    "/_functions",
    "/_triggers",
    "/functions",
    "/triggers",
    "/config/functions",
]

for path in info_paths:
    url = f"{RTDB_URL}{path}.json?auth={fb_token}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200 and r.json():
            print(f"  [DATA] {path}: {r.json()}")
        elif r.status_code == 200:
            print(f"  [NULL] {path}")
    except:
        pass

# 5. Check platform wallet before/after RTDB write
print("\n=== Wallet sync test ===")
def get_wallet():
    r = requests.get(f"https://{TID}mgapi.asdgapicenterssdo.com/mb/wallet",
        headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
        timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else "?"
    return f"ERR:{r.status_code}"

print(f"Platform wallet before: {get_wallet()} THB")

# Write a deposit trigger to RTDB
import uuid
test_id = str(uuid.uuid4())
deposit_data = {
    "amount": "50000.00",
    "approve_status": "success",
    "status": "success",
    "credited": True,
    "processed": True,
    "timestamp": int(time.time() * 1000),
    "bank_code": "KBANK",
    "transaction_id": test_id,
    "sync_platform": True,  # Try to trigger sync
    "force_credit": True
}

url = f"{RTDB_URL}/users/266d74e3-d6ca-47eb-b9ac-b8c45574bad4/DEPOSIT_APPROVE/{test_id}.json?auth={fb_token}"
r = requests.put(url, json=deposit_data, timeout=10)
print(f"RTDB write: {r.status_code}")

# Wait and check
time.sleep(2)
print(f"Platform wallet after: {get_wallet()} THB")

# 6. Check if there's a firestore instance
print("\n=== Checking Firestore ===")
firestore_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"
try:
    r = requests.get(firestore_url, headers={"Authorization": f"Bearer {fb_token}"}, timeout=10)
    print(f"Firestore: {r.status_code}")
    if r.ok:
        print(f"  {r.text[:300]}")
except Exception as e:
    print(f"Firestore error: {str(e)[:50]}")

print("\n=== Done ===")
