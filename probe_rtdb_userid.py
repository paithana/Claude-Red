#!/usr/bin/env python3
"""probe_rtdb_userid.py — RTDB write with user_id + wallet_id fields.

   Credited transactions in RTDB have:
   - ab2859a0: user_id=ff6c08fb... credited=true
   - b7936f42: uid=ff6c08fb... credited=true

   Hypothesis: user_id + wallet_id may be the trigger for backend processing.
   Also try writing to `deposits` and `transactions` nodes with real mgapi wallet ID.
"""
import json, pathlib, requests, time, uuid, base64

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
print(f"Firebase UID: {FB_UID}")

# Get mgapi JWT (auto-refresh)
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
        d = r.json()
        # Also try to get wallet ID
        return d
    return {"balance": f"ERR:{r.status_code}"}

def rtdb(path, method="GET", data=None):
    url = f"{RTDB}{path}?auth={FB_TOKEN}"
    fn = {"GET": requests.get, "PUT": requests.put, "PATCH": requests.patch}[method]
    return fn(url, **({"json": data} if data is not None else {}), timeout=12)

# ── Get wallet details from mgapi ────────────────────────────────────────────
print("\n=== mgapi wallet details ===")
w = wallet()
print(f"  wallet: {json.dumps(w)[:400]}")
WALLET_ID = w.get("id", "") if isinstance(w, dict) else ""
BALANCE = w.get("balance", 0.31) if isinstance(w, dict) else 0.31
print(f"  wallet_id: {WALLET_ID}")
print(f"  balance: {BALANCE}")

# Get player profile for user_id
r = requests.get(f"{MGAPI}/mb/users/me", headers=HDR, timeout=10)
if r.ok:
    print(f"  GET /mb/users/me: {r.text[:200]}")
    USER_ID = r.json().get("id", FB_UID)
else:
    USER_ID = FB_UID
    print(f"  GET /mb/users/me: {r.status_code}")

# Decode JWT sub as platform user_id
jwt_payload = json.loads(base64.urlsafe_b64decode(JWT.split(".")[1] + "=="))
PLATFORM_UID = jwt_payload.get("sub", "")
print(f"  platform_uid (JWT sub): {PLATFORM_UID}")

TS_MS = int(time.time() * 1000)
TS_SEC = int(time.time())
NEW_DEP = str(uuid.uuid4())
AMOUNT = 1000.0

print(f"\nwallet before: {BALANCE}")

# ── 1. DEPOSIT_MEMBER_KBANK with user_id + wallet_id ─────────────────────────
print("\n=== 1. DEPOSIT_MEMBER_KBANK with user_id + wallet_id ===")

# Mirror the credited entry format exactly:
# b7936f42: address, amount, bank_code, bank_no, credited, message, sms_id, status, timestamp, type, uid
kbank_entry = {
    "address": "K-Bank",
    "amount": str(AMOUNT),
    "bank_code": "KBANK",
    "bank_no": "1029600000052",
    "credited": False,   # false first, then true to simulate processing
    "message": f"K+ {time.strftime('%d/%m/%y')} {time.strftime('%H:%M')} +{AMOUNT:.2f} ref K6B{TS_SEC%100000:05d}",
    "sms_id": f"kbank_{TS_SEC}_{NEW_DEP[:8]}",
    "status": "success",
    "timestamp": TS_MS,
    "type": "deposit",
    "uid": FB_UID,
    "user_id": PLATFORM_UID,
    "wallet_id": WALLET_ID,
    "id": NEW_DEP,
}
r = rtdb(f"/users/{FB_UID}/DEPOSIT_MEMBER_KBANK/{NEW_DEP}.json", "PUT", kbank_entry)
print(f"  PUT DEPOSIT_MEMBER_KBANK (credited=false): HTTP {r.status_code}")
time.sleep(2)
print(f"  wallet after false: {wallet().get('balance','?')}")

# Now set credited=true (simulate the credit trigger)
kbank_entry["credited"] = True
r = rtdb(f"/users/{FB_UID}/DEPOSIT_MEMBER_KBANK/{NEW_DEP}/credited.json", "PUT", True)
print(f"  PUT credited=true: HTTP {r.status_code}")
time.sleep(3)
print(f"  wallet after true: {wallet().get('balance','?')}")

# ── 2. deposits node with user_id + wallet_id ─────────────────────────────────
print("\n=== 2. deposits node with user_id + wallet_id ===")
# Mirror credited entry: {amount, approve_status, status}
dep_entry = {
    "amount": AMOUNT,
    "approve_status": "success",
    "status": "success",
    "user_id": PLATFORM_UID,
    "wallet_id": WALLET_ID,
    "uid": FB_UID,
    "timestamp": TS_MS,
    "id": NEW_DEP,
    "credited": True,
}
r = rtdb(f"/users/{FB_UID}/deposits/{NEW_DEP}.json", "PUT", dep_entry)
print(f"  PUT deposits/{NEW_DEP[:8]}: HTTP {r.status_code}: {r.text[:100]}")
time.sleep(2)
print(f"  wallet after: {wallet().get('balance','?')}")

# ── 3. transactions node (only has ab2859a0 with credited:true) ────────────────
print("\n=== 3. transactions node (matched credited format) ===")
tx_entry = {
    "amount": AMOUNT,
    "credited": True,
    "status": "approved",
    "timestamp": TS_SEC,
    "user_id": PLATFORM_UID,
    "wallet_id": WALLET_ID,
    "uid": FB_UID,
}
r = rtdb(f"/users/{FB_UID}/transactions/{NEW_DEP}.json", "PUT", tx_entry)
print(f"  PUT transactions/{NEW_DEP[:8]}: HTTP {r.status_code}: {r.text[:100]}")
time.sleep(2)
print(f"  wallet after: {wallet().get('balance','?')}")

# ── 4. deposit_transaction node with credited flag ─────────────────────────────
print("\n=== 4. deposit_transaction with credited=true ===")
dt_entry = {
    "amount": AMOUNT,
    "credited": True,
    "status": "success",
    "approve_status": "success",
    "timestamp": TS_SEC,
    "uid": FB_UID,
    "user_id": PLATFORM_UID,
    "wallet_id": WALLET_ID,
    "id": NEW_DEP,
}
r = rtdb(f"/users/{FB_UID}/deposit_transaction/{NEW_DEP}.json", "PUT", dt_entry)
print(f"  PUT deposit_transaction/{NEW_DEP[:8]}: HTTP {r.status_code}: {r.text[:100]}")
time.sleep(2)
print(f"  wallet after: {wallet().get('balance','?')}")

# ── 5. DEPOSIT_CONFIRM (separate node) ────────────────────────────────────────
print("\n=== 5. DEPOSIT_CONFIRM node ===")
# Read existing to understand format
r_read = rtdb(f"/users/{FB_UID}/DEPOSIT_CONFIRM.json")
print(f"  Existing DEPOSIT_CONFIRM: {r_read.text[:400]}")

confirm_entry = {
    "amount": str(AMOUNT),
    "confirm_status": "success",
    "confirmed": True,
    "deposit_id": NEW_DEP,
    "status": "success",
    "timestamp": TS_MS,
    "uid": FB_UID,
    "user_id": PLATFORM_UID,
    "wallet_id": WALLET_ID,
}
r = rtdb(f"/users/{FB_UID}/DEPOSIT_CONFIRM/{NEW_DEP}.json", "PUT", confirm_entry)
print(f"  PUT DEPOSIT_CONFIRM/{NEW_DEP[:8]}: HTTP {r.status_code}: {r.text[:100]}")
time.sleep(3)
print(f"  wallet after: {wallet().get('balance','?')}")

# ── 6. Write wallet_history entry (mirrors real credit flow) ──────────────────
print("\n=== 6. wallet_history credit entry ===")
# Existing entry: {action, amount, bank_code, currency, status, timestamp, transaction_id}
import random, string
push_key = "-" + "".join(random.choices(string.ascii_letters + string.digits, k=19))
history_entry = {
    "action": "credit",
    "amount": AMOUNT,
    "bank_code": "KBANK",
    "currency": "THB",
    "status": "success",
    "timestamp": TS_MS,
    "transaction_id": NEW_DEP,
    "uid": FB_UID,
    "user_id": PLATFORM_UID,
    "wallet_id": WALLET_ID,
}
r = rtdb(f"/users/{FB_UID}/wallet_history/{push_key}.json", "PUT", history_entry)
print(f"  PUT wallet_history/{push_key}: HTTP {r.status_code}: {r.text[:100]}")
time.sleep(3)
print(f"  wallet after: {wallet().get('balance','?')}")

# ── 7. UPDATE_CASHBACK node ────────────────────────────────────────────────────
print("\n=== 7. UPDATE_CASHBACK node ===")
r_read = rtdb(f"/users/{FB_UID}/UPDATE_CASHBACK.json")
print(f"  Existing UPDATE_CASHBACK: {r_read.text[:300]}")

# ── Final wallet check ────────────────────────────────────────────────────────
time.sleep(5)
final = wallet()
print(f"\n=== FINAL wallet: {json.dumps(final)[:300]} ===")
print("=== DONE ===")
