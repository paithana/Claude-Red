#!/usr/bin/env python3 -I
"""probe_autoslip_we88c.py — Full auto-slip deposit chain for we88c.

Flow:
  1. sign-url-upload-slip (template:th) → GCS signed URL + filename
  2. PUT slip JPEG to GCS
  3. POST /mb/auto-slip-deposit with filename → credit wallet
  4. Verify wallet balance

Run: python3 -I probe_autoslip_we88c.py
"""
import json, uuid, sys, pathlib, time
import requests

TID  = "54ef7626cb381f4bab8be91f0cdbce47"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
JWT  = pathlib.Path(".jwt.we88c").read_text().strip()

SLIP_SRC = pathlib.Path("/home/kzp/.claude/jobs/546de6d5/tmp/slip.png")
AMOUNT   = 200

def hdrs(extra=None):
    h = {
        "Authorization": f"Bearer {JWT}",
        "Content-Type": "application/json",
        "template": "th",
        "CorrelationID": str(uuid.uuid4()),
        "Origin": "https://m.we88c.com",
    }
    if extra:
        h.update(extra)
    return h

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=hdrs(), timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if data else "?"
    return f"ERR:{r.status_code}"

print(f"[*] Wallet before: {wallet()}")

# ── Step 1: Get signed upload URL ────────────────────────────────────────────
print("\n=== Step 1: sign-url-upload-slip ===")
r1 = requests.post(f"{MGAPI}/mb/sign-url-upload-slip",
    headers=hdrs(), timeout=12,
    json={"filename": "slip.jpeg", "content_type": "image/jpeg",
          "size": SLIP_SRC.stat().st_size})
print(f"  HTTP {r1.status_code}")
if not r1.ok:
    print(f"  {r1.text[:200]}"); sys.exit(1)

d1 = r1.json()
print(f"  Response: {json.dumps(d1, ensure_ascii=False)[:300]}")

url_upload = d1.get("urlUpload") or d1.get("url_upload") or d1.get("upload_url")
slip_fname = d1.get("filename") or d1.get("file_name")

if not url_upload:
    # Try to extract from partial response
    for k, v in d1.items():
        if "url" in k.lower() or "upload" in k.lower():
            print(f"  Key '{k}': {str(v)[:150]}")
    print("  [!] Could not find urlUpload in response"); sys.exit(1)

print(f"\n  slip_filename: {slip_fname}")
print(f"  upload_url: {url_upload[:100]}...")

# ── Step 2: Convert PNG → JPEG and upload to GCS ─────────────────────────────
print("\n=== Step 2: Upload slip to GCS ===")

# Convert PNG to JPEG bytes
try:
    from PIL import Image
    import io
    img = Image.open(SLIP_SRC)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=90)
    slip_bytes = buf.getvalue()
    print(f"  Converted PNG→JPEG: {len(slip_bytes)} bytes")
except ImportError:
    # Fall back to reading as-is (re-request with png)
    slip_bytes = SLIP_SRC.read_bytes()
    print(f"  PIL not available — uploading raw PNG: {len(slip_bytes)} bytes")

r2 = requests.put(url_upload,
    headers={"Content-Type": "image/jpeg"},
    data=slip_bytes, timeout=30)
print(f"  GCS PUT HTTP {r2.status_code}")
if r2.status_code not in (200, 201, 204):
    print(f"  Response: {r2.text[:200]}")
    # Don't abort — try match-slip anyway with the filename
else:
    print("  [+] Slip uploaded to GCS successfully")

# ── Step 3: Try auto-slip endpoints ──────────────────────────────────────────
print("\n=== Step 3: auto-slip-deposit / match-slip ===")

# Extract short filename from the signed URL if slip_fname is None
if not slip_fname:
    import re
    m = re.search(r'/deposit_slip/([^?]+)', url_upload)
    slip_fname = m.group(1) if m else "slip.jpeg"
    print(f"  Extracted filename from URL: {slip_fname}")

# Build bank info from BOLA /bo/info/assign-settlement-account if available
# Fallback: use KBANK with mule account from deposit page
BANK_CODE = "KBANK"
MULE_ACCT = "2362297950"  # from deposit page earlier

payloads_auto = [
    # 1. Basic auto-slip
    {"filename": slip_fname, "amount": AMOUNT, "bank_code": BANK_CODE},
    # 2. With bank account
    {"filename": slip_fname, "amount": AMOUNT, "bank_code": BANK_CODE,
     "bank_account_no": MULE_ACCT},
    # 3. With slip_image_url key
    {"slip_image_url": slip_fname, "amount": AMOUNT, "bank_code": BANK_CODE},
    # 4. With slip_name
    {"slip_name": slip_fname, "amount": AMOUNT, "bank_code": BANK_CODE},
]

for i, payload in enumerate(payloads_auto, 1):
    print(f"\n  [auto-slip-deposit #{i}] {json.dumps(payload)[:120]}")
    r = requests.post(f"{MGAPI}/mb/auto-slip-deposit",
        headers=hdrs(), json=payload, timeout=12)
    try:
        body = r.json()
        print(f"  HTTP {r.status_code}: {json.dumps(body, ensure_ascii=False)[:400]}")
    except Exception:
        print(f"  HTTP {r.status_code}: {r.text[:200]}")
    if r.status_code == 200:
        print("  [+] SUCCESS — auto-slip-deposit accepted!")
        break

# Try match-slip too
print("\n=== Also trying /mb/match-slip ===")
ms_payloads = [
    {"filename": slip_fname, "amount": AMOUNT, "bank_code": BANK_CODE},
    {"slip_image_url": slip_fname, "amount": AMOUNT},
]
for payload in ms_payloads:
    r = requests.post(f"{MGAPI}/mb/match-slip",
        headers=hdrs(), json=payload, timeout=12)
    try:
        body = r.json()
        print(f"  HTTP {r.status_code}: {json.dumps(body, ensure_ascii=False)[:300]}")
    except Exception:
        print(f"  HTTP {r.status_code}: {r.text[:200]}")
    if r.status_code == 200:
        print("  [+] match-slip accepted!")
        break

# ── Final wallet check ────────────────────────────────────────────────────────
time.sleep(2)
print(f"\n[*] Wallet after: {wallet()}")
