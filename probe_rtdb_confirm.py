#!/usr/bin/env python3
"""probe_rtdb_confirm.py — PATCH existing DEPOSIT_CONFIRM entries to status=success.

   FINDING: DEPOSIT_CONFIRM has PLATFORM-CREATED entries (push keys) with
   status="pending" linked to real mgapi tx_ids. These differ from fake UUIDs
   we've been creating. Backend may have Firebase listener watching for
   status changes on these entries.

   Strategy: PATCH status="pending" → "success" on existing platform entries.
"""
import json, pathlib, requests, time, base64

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
RTDB  = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

_new = pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt")
FB_TOKEN = (_new.read_text().strip() if _new.exists() and _new.stat().st_size > 100
            else pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip())

parts = FB_TOKEN.split(".")
pad = parts[1] + "=" * (-len(parts[1]) % 4)
payload = json.loads(base64.urlsafe_b64decode(pad))
FB_UID = payload.get("sub") or payload.get("user_id", "")

JWT_FILE = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2")

def get_jwt():
    cached = JWT_FILE.read_text().strip() if JWT_FILE.exists() else ""
    if cached:
        p = json.loads(base64.urlsafe_b64decode(cached.split(".")[1] + "=="))
        if p.get("exp", 0) - time.time() > 300:
            return cached
    r = requests.post(
        f"https://{TID}pbapi.asdgapicenterssdo.com/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15,
    )
    if r.status_code in (200, 201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    raise RuntimeError(f"Auth failed: {r.status_code}")

JWT = get_jwt()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    if r.ok:
        items = r.json().get("data", [])
        return items[0].get("balance", "?") if items else "?"
    return f"ERR:{r.status_code}"

def rtdb(path, method="GET", data=None):
    url = f"{RTDB}{path}?auth={FB_TOKEN}"
    fn = {"GET": requests.get, "PUT": requests.put, "PATCH": requests.patch}[method]
    return fn(url, **({"json": data} if data is not None else {}), timeout=12)

print(f"wallet before: {wallet()}")

# ── 1. Read ALL DEPOSIT_CONFIRM entries ───────────────────────────────────────
print("\n=== 1. Read all DEPOSIT_CONFIRM entries ===")
r = rtdb(f"/users/{FB_UID}/DEPOSIT_CONFIRM.json")
print(f"  HTTP {r.status_code}: {r.text[:1000]}")

confirm_entries = {}
if r.ok and r.text != "null":
    confirm_entries = r.json() or {}
    print(f"  Total entries: {len(confirm_entries)}")
    for key, val in confirm_entries.items():
        if isinstance(val, dict):
            print(f"  {key}: status={val.get('status','?')} tx_id={val.get('tx_id','?')[:8]} amount={val.get('amount','?')}")

# ── 2. PATCH each pending entry → success ────────────────────────────────────
print("\n=== 2. PATCH pending entries to success ===")
for key, val in confirm_entries.items():
    if not isinstance(val, dict):
        continue
    status = val.get("status", "")
    tx_id = val.get("tx_id", "")
    amount = val.get("amount", 0)

    # Try patching regardless of current status
    r = rtdb(f"/users/{FB_UID}/DEPOSIT_CONFIRM/{key}/status.json", "PUT", "success")
    print(f"  [{key}] PUT status=success: HTTP {r.status_code}: {r.text[:60]}")

    # Also PATCH the whole entry with success fields
    patch = {"status": "success", "credited": True, "processed": True}
    r2 = rtdb(f"/users/{FB_UID}/DEPOSIT_CONFIRM/{key}.json", "PATCH", patch)
    print(f"  [{key}] PATCH credited=true: HTTP {r2.status_code}: {r2.text[:60]}")
    time.sleep(1)

time.sleep(3)
print(f"\nwallet after DEPOSIT_CONFIRM patches: {wallet()}")

# ── 3. Try PATCHING the DEPOSIT_CONFIRM entry back to the working format ──────
# The one real credit had: DEPOSIT_MEMBER_KBANK with message + credited=true
# Try matching that exact format from an existing tx_id
print("\n=== 3. Mirror credited KBANK entry format for pending tx_ids ===")
for key, val in confirm_entries.items():
    if not isinstance(val, dict):
        continue
    tx_id = val.get("tx_id", "")
    if not tx_id or val.get("bank_code", "") != "KBANK":
        continue
    amount = val.get("amount", 1000)
    print(f"  Processing KBANK confirm {key} / tx={tx_id[:8]} amount={amount}")

    TS = int(time.time())
    kbank_mirror = {
        "address": "K-Bank",
        "amount": str(amount),
        "bank_code": "KBANK",
        "bank_no": "1029600000052",
        "credited": True,
        "message": f"K+ {time.strftime('%d/%m/%y')} {time.strftime('%H:%M')} +{amount}.00 ref K6B{TS%100000:05d}",
        "sms_id": f"kbank_{TS}_{tx_id[:8]}",
        "status": "success",
        "timestamp": TS * 1000,
        "type": "deposit",
        "uid": FB_UID,
        "tx_id": tx_id,
    }
    r = rtdb(f"/users/{FB_UID}/DEPOSIT_MEMBER_KBANK/{tx_id}.json", "PUT", kbank_mirror)
    print(f"  PUT DEPOSIT_MEMBER_KBANK/{tx_id[:8]}: HTTP {r.status_code}")
    time.sleep(2)
    print(f"  wallet: {wallet()}")

# ── 4. Read back DEPOSIT_CONFIRM to see if status changed ─────────────────────
print("\n=== 4. DEPOSIT_CONFIRM state after patches ===")
r = rtdb(f"/users/{FB_UID}/DEPOSIT_CONFIRM.json")
if r.ok and r.text != "null":
    entries = r.json() or {}
    for key, val in entries.items():
        if isinstance(val, dict):
            print(f"  {key}: status={val.get('status','?')} credited={val.get('credited','?')} tx_id={val.get('tx_id','?')[:8]}")

# ── 5. Check if mgapi deposit status changed ──────────────────────────────────
print("\n=== 5. mgapi deposit status for tx_ids ===")
for key, val in confirm_entries.items():
    tx_id = val.get("tx_id", "") if isinstance(val, dict) else ""
    if tx_id:
        r = requests.get(f"{MGAPI}/mb/deposit-transaction/{tx_id}", headers=HDR, timeout=10)
        print(f"  GET /mb/deposit-transaction/{tx_id[:8]}: HTTP {r.status_code}: {r.text[:150]}")

time.sleep(5)
print(f"\nFINAL wallet: {wallet()}")
print("=== DONE ===")
