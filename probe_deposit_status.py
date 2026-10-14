#!/usr/bin/env python3
"""probe_deposit_status.py — Check current deposit status + find correct GET endpoint.
   Deposits 30083b71 and b88c0b6d were created but GET /mb/deposit-transaction/{id} returns 404.
"""
import json, pathlib, requests, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
JWT   = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
DEPOSIT_ID  = "30083b71-5f1a-4fa7-8309-31b2baf96427"
DEPOSIT_ID2 = "b88c0b6d-c18c-4ae6-b4af-19a66af3ccb9"
KBANK_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"
AUTOSLIP_BANK_ID = "18a9502b-94ae-4188-8841-094be8b3b974"

def hdrs():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "template": "vn", "correlationid": f"ds-{int(time.time())}",
            "languagecode": "th", "Origin": "https://m.vak88z2.com"}

# ── 1. Try all deposit-transaction GET path variants ─────────────────────────
print("=== Deposit GET path variants ===")
for path in [
    f"/mb/deposit-transaction/{DEPOSIT_ID}",
    f"/mb/deposit-transactions/{DEPOSIT_ID}",
    f"/mb/deposit-transaction?id={DEPOSIT_ID}",
    f"/mb/deposit-transaction?deposit_id={DEPOSIT_ID}",
    "/mb/deposit-transaction",
    "/mb/deposit-transactions",
    "/mb/deposit-transaction?skip=0&limit=10",
    "/mb/deposit-transaction?status=waiting",
    f"/mb/deposit-transaction/{DEPOSIT_ID}/status",
]:
    r = requests.get(f"{MGAPI}{path}", headers=hdrs(), timeout=10)
    body = r.text[:200]
    print(f"  {path}: HTTP {r.status_code}: {body}")

# ── 2. Re-submit a new deposit (in case old ones expired) ─────────────────────
print("\n=== Re-submit deposit 100 THB (AUTOSLIP SCB) ===")
import hashlib, uuid
slip_id = str(uuid.uuid4())
slip_name = f"{slip_id}.jfif"

# Sign URL
r = requests.post(f"{MGAPI}/mb/sign-url-upload-slip",
                  headers=hdrs(),
                  json={"file_name": slip_name, "file_type": "image/jpeg"},
                  timeout=10)
print(f"  sign-url: HTTP {r.status_code}")
if r.ok:
    sign_data = r.json()
    upload_url = sign_data.get("url", "")
    gcs_filename = sign_data.get("file_name", slip_name)
    print(f"  gcs_filename: {gcs_filename}")

    # Upload minimal JPEG to GCS
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
    up_hdrs = {"Content-Type": "image/jpeg", "Content-Length": str(len(minimal_jpeg))}
    ru = requests.put(upload_url, data=minimal_jpeg, headers=up_hdrs, timeout=15)
    print(f"  GCS upload: HTTP {ru.status_code}")

    if ru.status_code in (200, 204):
        # Submit deposit
        dep_payload = {
            "deposit_amount": 100.0,
            "note": "",
            "slip_image_url": gcs_filename,
            "is_auto_slip": True,
            "payment_bank_information_id": AUTOSLIP_BANK_ID,
            "deposit_account_id": KBANK_ACCT,
        }
        rd = requests.post(f"{MGAPI}/mb/deposit-transaction",
                           headers=hdrs(), json=dep_payload, timeout=12)
        print(f"  deposit: HTTP {rd.status_code}: {rd.text[:300]}")
        if rd.ok:
            d = rd.json()
            new_dep_id = d.get("id", "?")
            print(f"  [!!!] NEW DEPOSIT ID: {new_dep_id}")
            print(f"  approve_status: {d.get('approve_status','?')}")

# ── 3. Current wallet ─────────────────────────────────────────────────────────
print("\n=== Wallet ===")
r = requests.get(f"{MGAPI}/mb/wallet", headers=hdrs(), timeout=10)
print(f"  {r.json().get('balance','?') if r.ok else r.text[:100]}")
print("\n=== DONE ===")
