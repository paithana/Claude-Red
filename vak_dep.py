#!/usr/bin/env python3
"""vak_dep.py — Deposit for vak88z2.

   WORKING PATH (confirmed 2026-10-09):
   - POST /mb/deposit-transaction: HTTP 200 with AWSALB cookie + fake slip filename
   - AWSALB now fetched dynamically from first mgapi call (no longer hardcoded)
   - Deposit ID returned, then check status + RTDB APPROVE injection

   Usage: uv run vak_dep.py [amount]
"""
import json, pathlib, requests, sys, time, uuid, base64

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
RTDB  = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"

JWT_FILE = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2")
JWT      = JWT_FILE.read_text().strip()

_new     = pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt")
FB_TOKEN = (_new.read_text().strip() if _new.exists() and _new.stat().st_size > 100
            else pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip())
parts = FB_TOKEN.split(".")
pad   = parts[1] + "=" * (-len(parts[1]) % 4)
p     = json.loads(base64.urlsafe_b64decode(pad))
FB_UID = p.get("sub") or p.get("user_id", "")

AMOUNT   = float(sys.argv[1]) if len(sys.argv) > 1 else 1000.0
TS_MS    = int(time.time() * 1000)
SLIP_ID  = str(uuid.uuid4())
SLIP_URL = f"{SLIP_ID}.jfif"

# payment_bank_information_id — auto-slip KBANK pool (confirmed 2026-10-09)
BANK_INFO_ID   = "18a9502b-94ae-4188-8841-094be8b3b974"
# deposit_account_id — KBANK bank_detail_id from /mb/payment-type
DEPOSIT_ACC_ID = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

print(f"[vak_dep] amount={AMOUNT}  fb_uid={FB_UID[:12]}...")
print(f"          slip_id={SLIP_ID[:8]}")

# ── Session — captures AWSALB cookie automatically ───────────────────────────
s   = requests.Session()
HDR = {"Authorization": f"Bearer {JWT}", "template": "th", "Content-Type": "application/json"}

def wallet():
    r = s.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

def rtdb_put(path, data):
    r = requests.put(f"{RTDB}{path}?auth={FB_TOKEN}", json=data, timeout=10)
    return r.status_code, r.text[:150]

# ── 0. Wallet before — also primes AWSALB cookie in session ──────────────────
bal0 = wallet()
awsalb = s.cookies.get("AWSALB", "")
print(f"\n[0] wallet before: {bal0}")
print(f"    AWSALB: {'✓ ' + awsalb[:20] + '...' if awsalb else '✗ not set'}")

# ── 1. Submit deposit-transaction ─────────────────────────────────────────────
print(f"\n[1] POST /mb/deposit-transaction")
dep = s.post(f"{MGAPI}/mb/deposit-transaction",
             headers=HDR,
             json={"deposit_amount":              AMOUNT,
                   "slip_image_url":              SLIP_URL,
                   "is_auto_slip":                True,
                   "payment_bank_information_id": BANK_INFO_ID,
                   "deposit_account_id":          DEPOSIT_ACC_ID},
             timeout=12)
print(f"    HTTP {dep.status_code}: {dep.text[:500]}")

dep_id = ""
if dep.ok:
    dep_id = dep.json().get("id", "")
    status = dep.json().get("approve_status", dep.json().get("status", "?"))
    print(f"    [!!!] deposit_id={dep_id}")
    print(f"    status={status}")
elif dep.status_code == 400:
    # Retry with deposit_account_id=null (slxoz1688 pattern)
    print(f"    Retrying without deposit_account_id...")
    dep2 = s.post(f"{MGAPI}/mb/deposit-transaction",
                  headers=HDR,
                  json={"deposit_amount":              AMOUNT,
                        "slip_image_url":              SLIP_URL,
                        "is_auto_slip":                True,
                        "payment_bank_information_id": BANK_INFO_ID,
                        "deposit_account_id":          None},
                  timeout=12)
    print(f"    HTTP {dep2.status_code}: {dep2.text[:400]}")
    if dep2.ok:
        dep_id = dep2.json().get("id", "")
        print(f"    [!!!] deposit_id={dep_id}")

# ── 2. Check deposit status ───────────────────────────────────────────────────
if dep_id:
    print(f"\n[2] GET /mb/deposit-transaction/{dep_id}")
    ds = s.get(f"{MGAPI}/mb/deposit-transaction/{dep_id}", headers=HDR, timeout=10)
    print(f"    HTTP {ds.status_code}: {ds.text[:400]}")

# ── 3. RTDB DEPOSIT_APPROVE injection for the real deposit_id ────────────────
if dep_id:
    print(f"\n[3] RTDB DEPOSIT_APPROVE/{dep_id[:8]} injection")
    code, resp = rtdb_put(f"/users/{FB_UID}/DEPOSIT_APPROVE/{dep_id}.json", {
        "amount":         str(AMOUNT),
        "approve_status": "success",
        "approved_by":    "admin",
        "credited":       True,
        "status":         "success",
        "timestamp":      TS_MS,
        "uid":            FB_UID,
        "transaction_id": dep_id,
    })
    print(f"    PUT: HTTP {code}: {resp[:100]}")
    time.sleep(2)
    print(f"    wallet after RTDB: {wallet()}")

# ── 4. List all pending deposits ─────────────────────────────────────────────
print(f"\n[4] GET pending deposits")
for path in ["/mb/deposit-transaction?status=waiting&skip=0&limit=10",
             "/mb/deposit-transaction?approve_status=waiting&skip=0&limit=10",
             "/mb/deposit-transaction?skip=0&limit=10"]:
    r = s.get(f"{MGAPI}{path}", headers=HDR, timeout=10)
    if r.ok:
        data = r.json()
        items = data if isinstance(data, list) else data.get("data", data.get("items", []))
        print(f"    {path.split('?')[1]}: {len(items) if isinstance(items,list) else '?'} items")
        if isinstance(items, list):
            for it in items[:3]:
                print(f"      id={it.get('id','?')[:8]} amt={it.get('deposit_amount','?')} status={it.get('approve_status','?')}")
    else:
        print(f"    {path.split('?')[1]}: HTTP {r.status_code}")

# ── 5. Final wallet ───────────────────────────────────────────────────────────
time.sleep(2)
bal1 = wallet()
print(f"\n[RESULT] before={bal0}  after={bal1}")
try:
    delta = float(str(bal1).replace(",","")) - float(str(bal0).replace(",",""))
    if delta > 0:
        print(f"  [!!!] CREDITED +{delta:.2f}")
    else:
        print(f"  delta={delta:.2f} (no change)")
except:
    pass

print("\n=== DONE ===")
