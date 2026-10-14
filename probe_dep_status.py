#!/usr/bin/env python3
"""probe_dep_status.py — Probe /mb/deposit-transaction (returns 400, not 404 → endpoint exists).

   Goal: find the required params to get real deposit list, then PATCH to approve.
"""
import base64, json, pathlib, requests, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"
KNOWN_DEP = "99e7a448-7d3a-4aee-ae87-eff1e3763347"  # our pending KBANK 1000

JWT_FILE = pathlib.Path(".jwt.vak88z2")

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

# ── 1. /mb/deposit-transaction with various params ────────────────────────────
print("\n=== 1. /mb/deposit-transaction param sweep ===")

param_sets = [
    {},
    {"domain": DOMAIN},
    {"domain": DOMAIN, "skip": 0, "limit": 10},
    {"domain": DOMAIN, "tid": TID},
    {"domain": DOMAIN, "status": "pending"},
    {"domain": DOMAIN, "approve_status": "pending"},
    {"domain": DOMAIN, "type": "deposit"},
    {"skip": 0, "limit": 10},
    {"tid": TID, "skip": 0, "limit": 10},
]

for params in param_sets:
    r = requests.get(f"{MGAPI}/mb/deposit-transaction", headers=HDR, params=params, timeout=10)
    label = "&".join(f"{k}={v}" for k,v in params.items()) or "(no params)"
    if r.status_code != 400:
        print(f"  [!!!] {label}: HTTP {r.status_code}: {r.text[:300]}")
    else:
        err = r.json().get("message","") if r.headers.get("content-type","").startswith("application/json") else r.text[:100]
        print(f"  {label}: 400: {str(err)[:100]}")

# ── 2. Direct fetch by known dep ID ──────────────────────────────────────────
print("\n=== 2. /mb/deposit-transaction/{id} with params ===")
for params in [{}, {"domain": DOMAIN}, {"tid": TID}]:
    r = requests.get(f"{MGAPI}/mb/deposit-transaction/{KNOWN_DEP}",
                     headers=HDR, params=params, timeout=10)
    label = str(params) or "(no params)"
    print(f"  GET {KNOWN_DEP[:8]}{label}: HTTP {r.status_code}: {r.text[:200]}")

# ── 3. Try PATCH/PUT on deposit-transaction ──────────────────────────────────
print("\n=== 3. PATCH/PUT /mb/deposit-transaction/{id} ===")
for method, data in [
    ("PATCH", {"approve_status": "success", "domain": DOMAIN}),
    ("PATCH", {"status": "success", "domain": DOMAIN}),
    ("PUT",   {"approve_status": "success", "status": "success", "domain": DOMAIN}),
]:
    fn = requests.patch if method == "PATCH" else requests.put
    r = fn(f"{MGAPI}/mb/deposit-transaction/{KNOWN_DEP}",
           headers=HDR, json=data, timeout=10)
    print(f"  {method} {KNOWN_DEP[:8]}: HTTP {r.status_code}: {r.text[:200]}")

# ── 4. mgapi endpoint discovery ───────────────────────────────────────────────
print("\n=== 4. mgapi endpoint discovery ===")
paths = [
    "/mb/deposit-transaction/approve",
    "/mb/deposit-transaction/admin-approve",
    f"/mb/deposit-transaction/{KNOWN_DEP}/approve",
    f"/mb/deposit-transaction/{KNOWN_DEP}/status",
    "/mb/approve-deposit",
    "/mb/deposit-approve",
    "/mb/approve",
    "/mb/transaction",
    "/mb/transaction/approve",
    f"/mb/auto-slip-deposit/{KNOWN_DEP}/approve",
    f"/mb/auto-slip-deposit/{KNOWN_DEP}",
    "/mb/auto-deposit-approve",
    "/mb/payment",
    "/mb/payment/approve",
]
for path in paths:
    r = requests.get(f"{MGAPI}{path}", headers=HDR, params={"domain": DOMAIN}, timeout=8)
    if r.status_code not in (404, 405):
        print(f"  [!!!] GET {path}: HTTP {r.status_code}: {r.text[:200]}")
    # Try POST on non-404s
    if r.status_code not in (404,):
        r2 = requests.post(f"{MGAPI}{path}", headers=HDR,
            json={"domain": DOMAIN, "approve_status": "success",
                  "deposit_transaction_id": KNOWN_DEP}, timeout=8)
        if r2.status_code not in (404, 405):
            print(f"  [!!!] POST {path}: HTTP {r2.status_code}: {r2.text[:200]}")

time.sleep(2)
print(f"\nFINAL wallet: {wallet()}")
print("=== DONE ===")
