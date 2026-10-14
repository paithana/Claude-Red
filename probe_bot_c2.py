#!/usr/bin/env python3
"""probe_bot_c2.py — Probe APK webhook paths on C2 xyzwalldetop.com.
   Tests: /webhook-kbank, /webhook-scb, /webhook-sms, /webhooks/sms/truewallet
   Auth: PAPDIEAW-KEY header (static, from F04 / env)
"""
import json, os, pathlib, urllib.request, urllib.error, ssl, time

TID = "af6efb584a3d317b5a11ab6209b88e1b"
C2  = f"https://{TID}.xyzwalldetop.com"

PAPDIEAW_KEY = os.environ.get("PAPDIEAW_KEY", "")
JWT          = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def req(method, url, body=None, headers=None):
    hdrs = {"Content-Type": "application/json", "User-Agent": "okhttp/4.9.3"}
    if headers:
        hdrs.update(headers)
    data = json.dumps(body).encode() if body else None
    rq = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(rq, context=ctx, timeout=10) as r:
            return r.status, r.read(2000).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(500).decode(errors="replace")
    except Exception as e:
        return 0, str(e)[:200]

print(f"=== C2: {C2} ===")
print(f"PAPDIEAW_KEY: {'SET' if PAPDIEAW_KEY else 'MISSING'}")
print()

# 1. Probe root to check if C2 is reachable
s, b = req("GET", C2 + "/")
print(f"GET /  → {s}: {b[:120]}")
print()

# 2. Known webhook paths from APK (F04)
paths = [
    "/webhook-kbank",
    "/webhook-scb",
    "/webhook-sms",
    "/webhooks/sms/truewallet",
    "/webhook",
    "/sms",
    "/api/sms",
    "/auth",
    "/login",
    "/info",
    "/status",
    "/config",
    "/get-config",
    "/get-webhook",
    "/api/config",
]

auth_headers = [
    {},
    {"papdieaw-key": PAPDIEAW_KEY} if PAPDIEAW_KEY else {},
    {"Authorization": f"Bearer {JWT}"},
    {"x-api-key": PAPDIEAW_KEY} if PAPDIEAW_KEY else {},
]

print("=== Webhook path sweep (GET + POST) ===")
for path in paths:
    url = C2 + path
    s, b = req("GET", url)
    snippet = b[:100].replace('\n','')
    if s not in (0, 404, 403):
        print(f"[!!!] GET {path} → {s}: {snippet}")
    else:
        print(f"      GET {path} → {s}: {snippet}")
    time.sleep(0.12)  # ~8 rps

print()
print("=== POST to /webhook-sms with fake bank SMS payload ===")
# Fake KBank OTP SMS format the APK parses
fake_sms_payloads = [
    {
        "phone": "0811111111",
        "sms": "KBank: Your account 6655379482 received 100.00 THB from 0841234567 Ref: TXN202610150001",
        "bank": "KBANK",
        "papdieaw_key": PAPDIEAW_KEY,
    },
    {
        "message": "KBank: Your account 6655379482 received 100.00 THB",
        "sender": "KBank",
        "papdieaw_key": PAPDIEAW_KEY,
    },
    # Raw APK format guess
    {
        "smsBody": "KBank: Your account 6655379482 received 100.00 THB",
        "smsSender": "KBank",
        "deviceId": "test-device",
        "papdieaw_key": PAPDIEAW_KEY,
    },
]
for path in ["/webhook-kbank", "/webhook-sms", "/sms"]:
    for i, pl in enumerate(fake_sms_payloads):
        s, b = req("POST", C2 + path, body=pl)
        if s not in (0, 404, 403):
            print(f"[!!!] POST {path} [p{i+1}] → {s}: {b[:150]}")
    time.sleep(0.12)

print()
print("=== POST /auth with PAPDIEAW_KEY ===")
auth_payloads = [
    {"papdieaw_key": PAPDIEAW_KEY, "phone": "0811111111"},
    {"key": PAPDIEAW_KEY},
    {"api_key": PAPDIEAW_KEY},
    {"token": PAPDIEAW_KEY},
]
for pl in auth_payloads:
    s, b = req("POST", C2 + "/auth", body=pl)
    if s not in (0, 404, 403):
        print(f"[!!!] POST /auth → {s}: {b[:200]}")
    time.sleep(0.12)

print()
print("=== DONE ===")
