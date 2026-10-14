#!/usr/bin/env python3 -I
"""login.py — re-auth we88c player JWT using {fb_name}.Jwt password pattern."""
import json, base64, pathlib, urllib.request, urllib.error, ssl, os, sys

TID   = "54ef7626cb381f4bab8be91f0cdbce47"
URL   = f"https://{TID}pbapi.asdgapicenterssdo.com/pb/authentication"
USER  = os.environ.get("USERNAME_WE88C", "0972571110")
JWT_F = pathlib.Path("/home/kzp/claude-red/.jwt.we88c")
FB_F  = pathlib.Path("/home/kzp/claude-red/.fb_we88c_id_token.txt")

# Decode Firebase display name from saved id_token
fb_name = ""
if FB_F.exists():
    try:
        token = FB_F.read_text().strip()
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.b64decode(payload))
        fb_name = claims.get("name", "")
        print(f"[+] Firebase name: {fb_name!r}")
    except Exception as e:
        print(f"[!] Could not decode FB token: {e}", file=sys.stderr)

# Build password candidates
passwords = []
if fb_name:
    passwords.append(f"{fb_name}.Jwt")
# Also try env PASSWORD as fallback
env_pass = os.environ.get("PASSWORD", "")
if env_pass:
    passwords.append(env_pass)

if not passwords:
    print("[!] No password candidates found. Set PASSWORD env or provide .fb_we88c_id_token.txt")
    sys.exit(1)

ctx = ssl.create_default_context()
for pwd in passwords:
    print(f"[*] Trying password: {pwd[:20]}{'...' if len(pwd)>20 else ''}")
    body = json.dumps({"strategy": "local", "username": USER, "password": pwd}).encode()
    req = urllib.request.Request(URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        data = json.loads(e.read(500))
    except Exception as e:
        print(f"  [!] Error: {e}")
        continue

    token = data.get("accessToken")
    if token:
        JWT_F.write_text(token)
        print(f"[+] Auth OK — JWT saved to {JWT_F}")
        print(f"    Token: {token[:60]}...")
        # Decode exp
        try:
            p = token.split(".")[1]; p += "="*(-len(p)%4)
            exp = json.loads(base64.b64decode(p)).get("exp", 0)
            import datetime
            print(f"    Expires: {datetime.datetime.utcfromtimestamp(exp)} UTC")
        except Exception:
            pass
        sys.exit(0)
    else:
        print(f"  [-] Failed: {json.dumps(data)[:150]}")

print("[!] All passwords failed.")
sys.exit(1)
