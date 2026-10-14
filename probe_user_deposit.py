#!/usr/bin/env python3
"""probe_user_deposit.py — Try /user/deposit/add with GCS slip UID.
   Also scan for all deposit-related endpoints across pbapi, mgapi, bgapi.
"""
import json, pathlib, requests, time, uuid

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
JWT    = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
DOMAIN = "m.vak88z2.com"
TS     = int(time.time())

# GCS slip UIDs from previous uploads (already uploaded to GCS)
SLIP1 = "4fe3f863-ba84-4938-98f1-d3015c25688c.jfif"
SLIP2 = "3df384d8-ec4f-470a-affa-0c1f5b14d383.jfif"
# Previous deposit IDs
DEP_ID1 = "30083b71-5f1a-4fa7-8309-31b2baf96427"
DEP_ID2 = "b88c0b6d-c18c-4ae6-b4af-19a66af3ccb9"
# Bank info
KBANK_ACCT_ID    = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"   # player's KBANK payment account
AUTOSLIP_BANK_ID = "18a9502b-94ae-4188-8841-094be8b3b974"   # platform SCB autoslip bank
KBANK_PLATFORM   = "1029600000052"                           # platform's KBANK account number

def hdrs():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "template": "vn", "correlationid": f"ud-{TS}",
            "languagecode": "th", "Origin": f"https://{DOMAIN}"}

# ── 1. POST /user/deposit/add on pbapi (FeathersJS) ──────────────────────────
print("=== POST /user/deposit/add (pbapi) with GCS slip UID ===")

# Various payload shapes for a deposit add with GCS slip
payloads = [
    # Basic: slip UID + amount
    {"slip_uid": SLIP1, "amount": 100.0, "domain": DOMAIN},
    {"slip_image_uid": SLIP1, "amount": 100.0, "domain": DOMAIN},
    {"slip": SLIP1, "amount": 100.0, "domain": DOMAIN},
    # With bank info
    {"slip_uid": SLIP1, "amount": 100.0, "bank_code": "SCB",
     "payment_bank_information_id": AUTOSLIP_BANK_ID, "domain": DOMAIN},
    # Full deposit object matching mgapi format but with slip_uid
    {"slip_uid": SLIP1, "deposit_amount": 100.0, "is_auto_slip": True,
     "payment_bank_information_id": AUTOSLIP_BANK_ID,
     "deposit_account_id": KBANK_ACCT_ID, "domain": DOMAIN},
    # With deposit_id reference
    {"slip_uid": SLIP1, "deposit_id": DEP_ID1, "amount": 100.0, "domain": DOMAIN},
    {"slip_uid": SLIP1, "deposit_id": DEP_ID1, "domain": DOMAIN},
    # Firebase UID as slip reference
    {"firebase_uid": SLIP1.replace(".jfif", ""), "amount": 100.0, "domain": DOMAIN},
    # GCS path format
    {"slip_url": f"slips/{SLIP1}", "amount": 100.0, "domain": DOMAIN},
    {"slip_url": f"gs://vak88/{SLIP1}", "amount": 100.0, "domain": DOMAIN},
]

paths_to_try = [
    "/user/deposit/add",
    "/pb/user/deposit/add",
    "/pb/deposit/add",
    "/pb/deposit",
    "/user/deposit",
]

for path in paths_to_try:
    for i, payload in enumerate(payloads[:3]):  # Try first 3 payloads per path
        try:
            r = requests.post(f"{PBAPI}{path}", headers=hdrs(), json=payload, timeout=10)
            if r.status_code not in (404, 405):
                print(f"\n  POST {path} [payload {i+1}]: HTTP {r.status_code}: {r.text[:300]}")
        except Exception as e:
            pass  # Silent skip

# Also try mgapi
print("\n=== POST /user/deposit/add (mgapi) ===")
for path in ["/user/deposit/add", "/mb/user/deposit/add", "/mb/deposit/add"]:
    for i, payload in enumerate(payloads[:4]):
        try:
            r = requests.post(f"{MGAPI}{path}", headers=hdrs(), json=payload, timeout=10)
            if r.status_code not in (404, 405):
                print(f"  POST {path} [p{i+1}]: HTTP {r.status_code}: {r.text[:300]}")
        except:
            pass

# ── 2. Re-sign new slip and use its UID immediately ──────────────────────────
print("\n=== Fresh GCS slip upload → /user/deposit/add ===")
new_slip_name = f"{uuid.uuid4()}.jfif"

r = requests.post(f"{MGAPI}/mb/sign-url-upload-slip",
                  headers=hdrs(),
                  json={"file_name": new_slip_name, "file_type": "image/jpeg"},
                  timeout=10)
print(f"  sign-url: HTTP {r.status_code}")
if r.ok:
    sign_data = r.json()
    upload_url  = sign_data.get("url", "")
    gcs_file    = sign_data.get("file_name", new_slip_name)
    gcs_uid     = gcs_file.replace(".jfif", "").split("/")[-1]  # extract UUID part
    print(f"  gcs_file: {gcs_file}")
    print(f"  gcs_uid: {gcs_uid}")

    # Upload minimal JPEG
    minimal_jpeg = bytes([
        0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,0x49,0x46,0x00,0x01,
        0x01,0x00,0x00,0x01,0x00,0x01,0x00,0x00,
        0xFF,0xDB,0x00,0x43,0x00,0x08,0x06,0x06,0x07,0x06,0x05,0x08,
        0x07,0x07,0x07,0x09,0x09,0x08,0x0A,0x0C,0x14,0x0D,0x0C,0x0B,
        0x0B,0x0C,0x19,0x12,0x13,0x0F,0x14,0x1D,0x1A,0x1F,0x1E,0x1D,
        0x1A,0x1C,0x1C,0x20,0x24,0x2E,0x27,0x20,0x22,0x2C,0x23,0x1C,
        0x1C,0x28,0x37,0x29,0x2C,0x30,0x31,0x34,0x34,0x34,0x1F,0x27,
        0x39,0x3D,0x38,0x32,0x3C,0x2E,0x33,0x34,0x32,
        0xFF,0xD9
    ])
    ru = requests.put(upload_url, data=minimal_jpeg,
                      headers={"Content-Type": "image/jpeg"}, timeout=15)
    print(f"  GCS upload: HTTP {ru.status_code}")

    if ru.status_code in (200, 204):
        # Now try /user/deposit/add with fresh GCS UID
        slip_dt = time.strftime("%Y-%m-%dT%H:%M:%S+07:00")

        fresh_payloads = [
            {"slip_uid": gcs_uid, "amount": 100.0, "domain": DOMAIN},
            {"slip_uid": gcs_file, "amount": 100.0, "domain": DOMAIN},
            {"slip_uid": gcs_uid, "deposit_amount": 100.0, "is_auto_slip": True,
             "payment_bank_information_id": AUTOSLIP_BANK_ID,
             "deposit_account_id": KBANK_ACCT_ID, "domain": DOMAIN},
            # Try the mgapi deposit format but pointing to /user/deposit/add
            {"deposit_amount": 100.0, "slip_image_url": gcs_file, "is_auto_slip": True,
             "payment_bank_information_id": AUTOSLIP_BANK_ID,
             "deposit_account_id": KBANK_ACCT_ID, "domain": DOMAIN},
            # UID only (most minimal)
            {"uid": gcs_uid, "amount": 100.0, "domain": DOMAIN},
            # With slip datetime
            {"slip_uid": gcs_uid, "slip_datetime": slip_dt, "amount": 100.0,
             "bank_code": "SCB", "domain": DOMAIN},
        ]

        print(f"\n  Trying /user/deposit/add with gcs_uid={gcs_uid[:20]}...")
        for path in ["/user/deposit/add", "/pb/user/deposit/add",
                     "/pb/deposit/add", "/pb/deposit"]:
            for i, pl in enumerate(fresh_payloads):
                try:
                    r = requests.post(f"{PBAPI}{path}", headers=hdrs(), json=pl, timeout=10)
                    if r.status_code not in (404, 405):
                        print(f"  [!!!] POST {path} [p{i+1}]: HTTP {r.status_code}: {r.text[:400]}")
                        if r.status_code == 200:
                            print(f"  [!!!] SUCCESS!")
                except:
                    pass

        # Also try mgapi with UID
        print(f"\n  Trying mgapi /mb/* with gcs_uid...")
        for path in ["/mb/deposit-transaction", "/user/deposit/add",
                     "/mb/deposit/add", "/mb/auto-deposit"]:
            try:
                # Try the slip UID directly in the deposit endpoint
                pl = {"deposit_amount": 100.0, "slip_image_url": gcs_file,
                      "slip_uid": gcs_uid, "is_auto_slip": True,
                      "payment_bank_information_id": AUTOSLIP_BANK_ID,
                      "deposit_account_id": KBANK_ACCT_ID}
                r = requests.post(f"{MGAPI}{path}", headers=hdrs(), json=pl, timeout=10)
                if r.status_code not in (404, 405):
                    print(f"  POST {path}: HTTP {r.status_code}: {r.text[:300]}")
                    if r.ok:
                        d = r.json()
                        print(f"  [!!!] id={d.get('id','?')} status={d.get('approve_status','?')}")
            except:
                pass

# ── 3. Check existing deposits + wallet ──────────────────────────────────────
print("\n=== Current state ===")
r = requests.get(f"{MGAPI}/mb/wallet", headers=hdrs(), timeout=10)
print(f"  Balance: {r.json().get('balance','?') if r.ok else r.text[:80]}")

# Try to list all deposits
for path in ["/mb/deposit-transaction?skip=0&limit=10", "/mb/deposit-transaction?status=waiting"]:
    r = requests.get(f"{MGAPI}{path}", headers=hdrs(), timeout=10)
    print(f"  GET {path}: HTTP {r.status_code}: {r.text[:200]}")

print("\n=== DONE ===")
