#!/usr/bin/env python3
"""probe_matchslip2.py — Find correct payload for /mb/match-slip (exists, ISEing).
   Deposit IDs waiting for approval:
     30083b71 (probe35, slip=4fe3f863.jfif)
     b88c0b6d (probe.py all, slip=3df384d8.jfif)
"""
import json, pathlib, requests, time

TID  = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
JWT  = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
KBANK_ACCT = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"
WITHDRAW_TYPE_LOCAL = "a26ca1bd-b339-4df3-89ed-4d73ad8e3e93"
DEPOSIT_ID  = "30083b71-5f1a-4fa7-8309-31b2baf96427"
DEPOSIT_ID2 = "b88c0b6d-c18c-4ae6-b4af-19a66af3ccb9"
SLIP1 = "4fe3f863-ba84-4938-98f1-d3015c25688c.jfif"
SLIP2 = "3df384d8-ec4f-470a-affa-0c1f5b14d383.jfif"
AUTOSLIP_BANK_ID = "18a9502b-94ae-4188-8841-094be8b3b974"

def hdrs():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "template": "vn", "correlationid": f"pms2-{int(time.time())}",
            "languagecode": "th", "Origin": "https://m.vak88z2.com"}

def req(label, payload):
    print(f"\n=== POST /mb/match-slip ({label}) ===")
    r = requests.post(f"{MGAPI}/mb/match-slip", headers=hdrs(),
                      json=payload, timeout=12)
    try:
        body = r.json()
        out = json.dumps(body, ensure_ascii=False)
        print(f"  HTTP {r.status_code}: {out[:700]}")
        return r.status_code, body
    except Exception:
        print(f"  HTTP {r.status_code}: {r.text[:300]}")
        return r.status_code, r.text

# Systematic payload variations for /mb/match-slip
payloads = [
    # Format 1: deposit_id only
    ({"deposit_id": DEPOSIT_ID}, "deposit_id only"),
    # Format 2: with slip
    ({"deposit_id": DEPOSIT_ID, "slip_image_url": SLIP1}, "deposit_id+slip"),
    # Format 3: amount + bank
    ({"deposit_id": DEPOSIT_ID, "amount": 100, "bank_code": "SCB"}, "deposit_id+amount+bank"),
    # Format 4: transaction reference
    ({"ref_no": "K6B0910001", "amount": 100, "bank_code": "SCB",
      "sender_account": "0543753327"}, "ref_no+amount+bank+sender"),
    # Format 5: same as deposit-transaction payload
    ({"deposit_amount": 100, "payment_bank_information_id": AUTOSLIP_BANK_ID,
      "deposit_account_id": KBANK_ACCT, "slip_image_url": SLIP1,
      "is_auto_slip": True}, "full deposit payload"),
    # Format 6: minimal with slip
    ({"slip_image_url": SLIP1}, "slip only"),
    ({"slip_image_url": SLIP2}, "slip2 only"),
    # Format 7: with bank info
    ({"slip_image_url": SLIP1, "payment_bank_information_id": AUTOSLIP_BANK_ID,
      "deposit_id": DEPOSIT_ID}, "slip+bank+deposit_id"),
    # Format 8: transaction-style
    ({"transaction_id": DEPOSIT_ID, "slip_url": SLIP1}, "transaction_id+slip_url"),
    ({"id": DEPOSIT_ID, "slip": SLIP1, "amount": 100}, "id+slip+amount"),
    # Format 9: bank_account_id + amount
    ({"bank_account_id": KBANK_ACCT, "amount": 100}, "bank_account_id+amount"),
    # Format 10: empty body (see what's required)
    ({}, "empty body"),
]

for payload, label in payloads:
    code, body = req(label, payload)
    # If non-ISE error, print more context
    if isinstance(body, dict):
        msg = body.get("message", {})
        if isinstance(msg, dict):
            en_msg = msg.get("en", "")
            if en_msg and "Internal Server Error" not in en_msg:
                print(f"  >> English message: {en_msg}")
        elif isinstance(msg, str) and "Internal Server Error" not in msg:
            print(f"  >> Message: {msg}")
        errors = body.get("errors")
        if errors:
            print(f"  >> Errors: {json.dumps(errors, ensure_ascii=False)[:200]}")
    if code == 200 or (isinstance(body, dict) and body.get("id")):
        print(f"\n  [!!!] MATCH-SLIP WORKED! body={json.dumps(body)[:200]}")
        break

# Also try GET /mb/match-slip with params
print("\n=== GET /mb/match-slip (discover schema) ===")
r = requests.get(f"{MGAPI}/mb/match-slip?deposit_id={DEPOSIT_ID}",
                 headers=hdrs(), timeout=10)
print(f"  HTTP {r.status_code}: {r.text[:300]}")

# Final balance + withdrawal check
print("\n=== Wallet balance ===")
r2 = requests.get(f"{MGAPI}/mb/wallet", headers=hdrs(), timeout=10)
d = r2.json() if r2.ok else {}
print(f"  Balance: {d.get('balance', '?')}")

print("\n=== DONE ===")
