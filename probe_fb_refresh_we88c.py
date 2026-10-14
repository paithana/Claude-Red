#!/usr/bin/env python3 -I
"""Refresh Firebase ID token for we88c using stored refresh token."""
import requests, pathlib, json, os, time, base64

refresh_tok = pathlib.Path(".fb_we88c_refresh.txt").read_text().strip()
api_key = os.environ.get("FIREBASE_API_KEY", "")

if not api_key:
    # Try loading from .env.lux manually
    env = pathlib.Path(".env.lux")
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("FIREBASE_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"\'')
                break

print(f"[api_key] {'found' if api_key else 'MISSING'} {api_key[:20] if api_key else ''}")
print(f"[refresh_token] {refresh_tok[:30]}...")

r = requests.post(
    "https://securetoken.googleapis.com/v1/token",
    params={"key": api_key},
    json={"grant_type": "refresh_token", "refresh_token": refresh_tok},
    timeout=10,
)
print(f"[status] {r.status_code}")
if r.status_code == 200:
    data = r.json()
    new_token = data.get("id_token", "")
    pathlib.Path(".fb_we88c_id_token.txt").write_text(new_token)
    p = new_token.split(".")[1]; p += "=" * (-len(p) % 4)
    exp = json.loads(base64.b64decode(p)).get("exp", 0)
    print(f"[OK] token saved, exp in {int((exp - time.time())/60)}m")
else:
    print(f"[ERROR] {r.text[:400]}")
