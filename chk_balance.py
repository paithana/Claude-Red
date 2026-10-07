#!/usr/bin/env python3
"""Post-probe: check wallet balance to detect if any forge succeeded."""
import json, ssl, sys, uuid, time
import urllib.request, urllib.error
from pathlib import Path

API_BASE = "https://54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com"
JWT = ""
for _jf in (".jwt.we88c", ".jwt"):
    if Path(_jf).exists():
        JWT = Path(_jf).read_text().strip()
        if JWT:
            break
if not JWT:
    print("Put valid JWT in .jwt.we88c (or .jwt) then run again")
    sys.exit(0)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode    = ssl.CERT_NONE

def get(path):
    r = urllib.request.Request(f"{API_BASE}{path}", headers={
        "Authorization": f"Bearer {JWT}",
        "Accept": "application/json",
        "CorrelationID": str(uuid.uuid4()),
    })
    try:
        with urllib.request.urlopen(r, timeout=8, context=CTX) as resp:
            return json.loads(resp.read(8192))
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read(2048).decode()}

wallet = get(f"/mb/wallet")
if "error" not in wallet:
    d = wallet["data"][0]
    print(f"balance : {d['balance']}")
    print(f"points  : {d['pointData']['point']}")
    print(f"turn_dep: {d.get('turn_deposit')}")

users = get(f"/mb/users?_t={int(time.time()*1000)}")
if "error" not in users:
    u = users["data"][0]
    print(f"username: {u['username']}")
    print(f"name    : {u['first_name']} {u['last_name']}")
    print(f"game_id : {u.get('user_in_game')}")
    print(f"payment_accounts: {json.dumps(u.get('payment_accounts', []), ensure_ascii=False)[:300]}")
