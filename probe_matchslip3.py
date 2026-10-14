#!/usr/bin/env python3
"""probe_matchslip3.py — match-slip with slip_datetime (user hint: need datetime field).
   Also tries GCS service-account approach for mgapi auth.
"""
import json, pathlib, requests, time
from datetime import datetime, timezone, timedelta

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
JWT   = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
DEPOSIT_ID  = "30083b71-5f1a-4fa7-8309-31b2baf96427"
DEPOSIT_ID2 = "b88c0b6d-c18c-4ae6-b4af-19a66af3ccb9"
SLIP1 = "4fe3f863-ba84-4938-98f1-d3015c25688c.jfif"
SLIP2 = "3df384d8-ec4f-470a-affa-0c1f5b14d383.jfif"
AUTOSLIP_BANK_ID = "18a9502b-94ae-4188-8841-094be8b3b974"
KBANK_ACCT = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

# Slip datetime — use the deposit creation time (approximately now-30min)
SLIP_DT = datetime.now(tz=timezone(timedelta(hours=7)))
SLIP_DT_ISO = SLIP_DT.strftime("%Y-%m-%dT%H:%M:%S+07:00")
SLIP_DT_SHORT = SLIP_DT.strftime("%d/%m/%Y %H:%M")  # Thai format "09/10/2026 09:36"
SLIP_EPOCH = int(SLIP_DT.timestamp())

def hdrs():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "template": "vn", "correlationid": f"ms3-{int(time.time())}",
            "languagecode": "th", "Origin": "https://m.vak88z2.com"}

def post_ms(label, payload):
    print(f"\n=== POST /mb/match-slip ({label}) ===")
    r = requests.post(f"{MGAPI}/mb/match-slip", headers=hdrs(),
                      json=payload, timeout=12)
    try:
        body = r.json()
        out = json.dumps(body, ensure_ascii=False)
        print(f"  HTTP {r.status_code}: {out[:800]}")
        return r.status_code, body
    except Exception:
        print(f"  HTTP {r.status_code}: {r.text[:300]}")
        return r.status_code, r.text

# ── Payloads with datetime (user hint) ──────────────────────────────────────
print(f"slip_datetime ISO: {SLIP_DT_ISO}")
print(f"slip_datetime Thai: {SLIP_DT_SHORT}")
print(f"slip_epoch: {SLIP_EPOCH}")

payloads = [
    # 1. deposit_id + slip_datetime ISO
    ({"deposit_id": DEPOSIT_ID, "slip_datetime": SLIP_DT_ISO}, "deposit_id+slip_datetime(ISO)"),
    # 2. deposit_id + transaction_date
    ({"deposit_id": DEPOSIT_ID, "transaction_date": SLIP_DT_ISO}, "deposit_id+transaction_date"),
    # 3. deposit_id + slip datetime + amount
    ({"deposit_id": DEPOSIT_ID, "slip_datetime": SLIP_DT_ISO, "amount": 100}, "deposit_id+dt+amount"),
    # 4. deposit_id + datetime + bank
    ({"deposit_id": DEPOSIT_ID, "datetime": SLIP_DT_ISO, "bank_code": "SCB", "amount": 100},
     "deposit_id+datetime+bank+amount"),
    # 5. slip image + datetime
    ({"slip_image_url": SLIP1, "slip_datetime": SLIP_DT_ISO, "amount": 100, "bank_code": "SCB"},
     "slip+slip_datetime+amount+bank"),
    # 6. Full payment info + datetime (closest to real payment)
    ({"deposit_id": DEPOSIT_ID,
      "slip_image_url": SLIP1,
      "slip_datetime": SLIP_DT_ISO,
      "amount": 100.0,
      "bank_code": "SCB",
      "payment_bank_information_id": AUTOSLIP_BANK_ID,
      "sender_name": "ธนวัฒน์ พุฒอินทร์",
      "sender_account": "0543753327",
      "ref_no": f"K6B{SLIP_EPOCH % 100000:05d}"},
     "full-with-datetime"),
    # 7. Thai date format
    ({"deposit_id": DEPOSIT_ID, "slip_datetime": SLIP_DT_SHORT, "amount": 100}, "Thai-date-format"),
    # 8. Unix timestamp
    ({"deposit_id": DEPOSIT_ID, "slip_timestamp": SLIP_EPOCH, "amount": 100}, "unix-timestamp"),
    # 9. Transaction datetime + ref
    ({"deposit_id": DEPOSIT_ID,
      "transaction_datetime": SLIP_DT_ISO,
      "ref_no": f"K6B{SLIP_EPOCH % 100000:05d}",
      "amount": 100},
     "transaction_datetime+ref"),
    # 10. Minimal with transaction date only
    ({"transaction_date": SLIP_DT_ISO, "amount": 100, "bank_code": "SCB",
      "payment_bank_information_id": AUTOSLIP_BANK_ID},
     "minimal-transaction_date"),
]

for payload, label in payloads:
    code, body = post_ms(label, payload)
    if code == 200 or (isinstance(body, dict) and body.get("id")):
        print(f"\n  [!!!] MATCH-SLIP WORKED! deposit_id={body.get('id', body)}")
        break
    if isinstance(body, dict):
        msg = body.get("message", "")
        if isinstance(msg, dict): msg = msg.get("en", "")
        if msg and "Internal Server Error" not in str(msg):
            print(f"  >> Non-ISE message: {msg}")

# ── Also check GET /mb/match-slip for schema hints ───────────────────────────
print("\n=== GET /mb/match-slip ===")
r = requests.get(f"{MGAPI}/mb/match-slip", headers=hdrs(), timeout=10)
print(f"  HTTP {r.status_code}: {r.text[:300]}")

print("\n=== GET /mb/deposit-transaction/{id} (check status) ===")
for did in [DEPOSIT_ID, DEPOSIT_ID2]:
    r = requests.get(f"{MGAPI}/mb/deposit-transaction/{did}",
                     headers=hdrs(), timeout=10)
    d = r.json() if r.ok else {}
    print(f"  {did[:8]}: HTTP {r.status_code}: status={d.get('approve_status','?')} amount={d.get('deposit_amount','?')}")

print("\n=== Wallet balance ===")
r2 = requests.get(f"{MGAPI}/mb/wallet", headers=hdrs(), timeout=10)
d = r2.json() if r2.ok else {}
print(f"  Balance: {d.get('balance', '?')}")

print("\n=== DONE ===")
