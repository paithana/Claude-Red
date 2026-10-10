#!/usr/bin/env python3 -I
"""probe_wss_we88c.py — WebSocket probing on we88c tenant.

Targets:
  1. Firebase RTDB WSS (we88zz project) — deposit notification paths
  2. mgapi jackpot/notification WSS
  3. pbapi WSS (FeathersJS socket.io)

Run: python3 -I probe_wss_we88c.py
"""
import asyncio, json, pathlib, ssl, uuid, time

TID  = "54ef7626cb381f4bab8be91f0cdbce47"
PLAYER_UID = "266d74e3-d6ca-47eb-b9ac-b8c45574bad4"
JWT  = pathlib.Path("/home/kzp/claude-red/.jwt.we88c").read_text().strip()

# Firebase IDs / keys
FB_PROJECT = "we88zz"
FB_REGION  = "asia-southeast1"
FB_API_KEY = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"
FB_RTDB_URL = f"wss://{FB_PROJECT}.{FB_REGION}.firebasedatabase.app/.ws?v=5&ns={FB_PROJECT}"

import requests

def refresh_firebase():
    refresh = pathlib.Path("/home/kzp/claude-red/.fb_we88c_refresh.txt").read_text().strip()
    r = requests.post(
        f"https://securetoken.googleapis.com/v1/token?key={FB_API_KEY}",
        json={"grant_type": "refresh_token", "refresh_token": refresh},
        timeout=10
    )
    d = r.json()
    if "id_token" in d:
        pathlib.Path("/home/kzp/claude-red/.fb_we88c_refresh.txt").write_text(d["refresh_token"])
        return d["id_token"]
    print(f"  [!] Firebase refresh failed: {d}")
    return None

print("=== Refreshing Firebase token ===")
FB_ID_TOKEN = refresh_firebase()
if FB_ID_TOKEN:
    print(f"  [+] Token refreshed: ...{FB_ID_TOKEN[-20:]}")
else:
    print("  [!] No Firebase token")

# ── 1. Check RTDB REST paths for deposit notifications ─────────────────────
print("\n=== Firebase RTDB REST — deposit notification paths ===")
auth_param = f"?auth={FB_ID_TOKEN}" if FB_ID_TOKEN else ""
RTDB_BASE = f"https://{FB_PROJECT}.{FB_REGION}.firebasedatabase.app"

paths_to_check = [
    f"/users/{PLAYER_UID}",
    f"/users/{PLAYER_UID}/deposit",
    f"/notification/{PLAYER_UID}",
    f"/deposit/{PLAYER_UID}",
    f"/topup/{PLAYER_UID}",
    f"/wallet/{PLAYER_UID}",
    f"/balance/{PLAYER_UID}",
    f"/transactions/{PLAYER_UID}",
    # Tenant-prefixed paths
    f"/{TID}/users/{PLAYER_UID}",
    f"/{TID}/notification/{PLAYER_UID}",
    f"/{TID}/deposit",
]

for path in paths_to_check:
    try:
        r = requests.get(f"{RTDB_BASE}{path}.json{auth_param}", timeout=8)
        body = r.text[:120] if r.text else "(empty)"
        if r.status_code == 200 and r.text not in ("null", ""):
            print(f"  [+] {path} → HTTP {r.status_code}: {body}")
        else:
            print(f"  [-] {path} → HTTP {r.status_code}: {body[:60]}")
    except Exception as e:
        print(f"  [!] {path} → {e}")

# ── 2. Check jackpot/notification WSS over REST equivalent ─────────────────
print("\n=== mgapi notification endpoints (REST) ===")
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"

def mhdr():
    return {
        "Authorization": f"Bearer {JWT}",
        "Content-Type": "application/json",
        "template": "th",
        "CorrelationID": str(uuid.uuid4()),
    }

notif_paths = [
    "/mb/notification",
    "/mb/notifications",
    "/mb/jackpot",
    "/mb/announcement",
    "/mb/announcement/list",
    "/mb/event",
    "/mb/popup",
]

for p in notif_paths:
    try:
        r = requests.get(f"{MGAPI}{p}", headers=mhdr(), timeout=8)
        body = r.text[:200]
        print(f"  [{r.status_code}] {p}: {body[:120]}")
    except Exception as e:
        print(f"  [!] {p}: {e}")

# ── 3. pbapi FeathersJS socket.io — REST equivalent (service introspection) ─
print("\n=== pbapi FeathersJS services (REST introspection) ===")
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"

def phdr():
    return {
        "Authorization": f"Bearer {JWT}",
        "Content-Type": "application/json",
    }

pb_services = [
    "/pb/notification",
    "/pb/announce",
    "/pb/announcement",
    "/pb/jackpot",
    "/pb/event",
    "/pb/popup",
    "/pb/promotion",
    "/pb/wallet",
]

for p in pb_services:
    try:
        r = requests.get(f"{PBAPI}{p}?domain=m.we88c.com", headers=phdr(), timeout=8)
        body = r.text[:200]
        print(f"  [{r.status_code}] {p}: {body[:120]}")
    except Exception as e:
        print(f"  [!] {p}: {e}")

# ── 4. Check deposit transaction status (the one we created) ─────────────────
print("\n=== Deposit transaction status check ===")
DEP_ID = "f720d078-587c-4678-88e1-249cdd750beb"

try:
    r = requests.get(f"{MGAPI}/mb/deposit-transaction/{DEP_ID}", headers=mhdr(), timeout=10)
    print(f"  [{r.status_code}] GET /mb/deposit-transaction/{DEP_ID}")
    if r.ok:
        d = r.json()
        print(f"  Status: {d.get('approve_status')}")
        print(f"  Amount: {d.get('deposit_amount')}")
        print(f"  Full: {json.dumps(d, ensure_ascii=False)[:400]}")
    else:
        print(f"  {r.text[:200]}")
except Exception as e:
    print(f"  [!] {e}")

# Try listing all deposit transactions
try:
    r = requests.get(f"{MGAPI}/mb/deposit-transaction", headers=mhdr(),
                     params={"$limit": 5, "$sort[created_at]": -1}, timeout=10)
    print(f"\n  [{r.status_code}] GET /mb/deposit-transaction (list)")
    if r.ok:
        d = r.json()
        items = d.get("data", []) if isinstance(d, dict) else d
        for item in items[:3]:
            print(f"    id={item.get('id')} status={item.get('approve_status')} amount={item.get('deposit_amount')}")
    else:
        print(f"  {r.text[:200]}")
except Exception as e:
    print(f"  [!] {e}")

# ── 5. Try submitting another 200 THB deposit (chain works, replicate) ───────
print("\n=== Submit another 200 THB deposit ===")
PBINFO_ID = "2c595a21-9bba-4d06-ab30-5dc3c97dacb9"
DEPOSIT_ACCT_ID = "a62dea72-6439-11f1-a811-0644d6fb2ecf"
SLIP_PATH = pathlib.Path("/home/kzp/.claude/jobs/546de6d5/tmp/slip.png")

# Step 1: Get fresh signed URL
print("  Step 1: sign-url-upload-slip")
r1 = requests.post(f"{MGAPI}/mb/sign-url-upload-slip",
    headers=mhdr(), timeout=12,
    json={"filename": "slip.jpeg", "content_type": "image/jpeg", "size": SLIP_PATH.stat().st_size})
print(f"    HTTP {r1.status_code}")

if r1.ok:
    d1 = r1.json()
    url_upload = d1.get("urlUpload") or d1.get("url_upload") or d1.get("upload_url")
    import re
    slip_fname = d1.get("filename") or d1.get("file_name")
    if not slip_fname and url_upload:
        m = re.search(r'/deposit_slip/([^?]+)', url_upload)
        slip_fname = m.group(1) if m else None
    print(f"    fname={slip_fname}")

    # Step 2: Upload
    print("  Step 2: GCS PUT")
    try:
        from PIL import Image
        import io
        img = Image.open(SLIP_PATH)
        buf = io.BytesIO()
        img.convert("RGB").save(buf, "JPEG", quality=90)
        slip_bytes = buf.getvalue()
    except ImportError:
        slip_bytes = SLIP_PATH.read_bytes()

    r2 = requests.put(url_upload, headers={"Content-Type": "image/jpeg"}, data=slip_bytes, timeout=30)
    print(f"    GCS PUT HTTP {r2.status_code}")

    if r2.status_code in (200, 201, 204):
        # Step 3: deposit-transaction
        print("  Step 3: deposit-transaction")
        dep_payload = {
            "payment_bank_information_id": PBINFO_ID,
            "deposit_amount": 200,
            "deposit_account_id": DEPOSIT_ACCT_ID,
            "note": "",
        }
        if slip_fname:
            dep_payload["slip_image_url"] = slip_fname

        r3 = requests.post(f"{MGAPI}/mb/deposit-transaction", headers=mhdr(),
                           json=dep_payload, timeout=12)
        print(f"    HTTP {r3.status_code}")
        if r3.ok:
            d3 = r3.json()
            dep_id2 = d3.get("id")
            print(f"    [+] Deposit ID: {dep_id2}")
            print(f"    balance_after: {d3.get('balance_after_deposit')}")
            print(f"    approve_status: {d3.get('approve_status')}")

            # Step 4: auto-slip-deposit
            print("  Step 4: auto-slip-deposit")
            r4 = requests.post(f"{MGAPI}/mb/auto-slip-deposit",
                headers=mhdr(),
                json={"filename": slip_fname, "amount": 200},
                timeout=12)
            print(f"    HTTP {r4.status_code}: {r4.text[:200]}")
        else:
            print(f"    [!] {r3.text[:300]}")
else:
    print(f"    sign-url failed: {r1.text[:200]}")

# ── Final wallet check ─────────────────────────────────────────────────────
print("\n=== Final wallet balance ===")
try:
    r = requests.get(f"{MGAPI}/mb/wallet", headers=mhdr(), timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        w = data[0] if data else {}
        print(f"  Balance: {w.get('balance')} THB")
        print(f"  Turn deposit: {w.get('turn_deposit')}")
        print(f"  Turn target: {w.get('turn_deposit_target')}")
    else:
        print(f"  [{r.status_code}] {r.text[:100]}")
except Exception as e:
    print(f"  [!] {e}")
