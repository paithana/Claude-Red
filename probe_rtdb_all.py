#!/usr/bin/env python3 -I
"""Probe Firebase RTDB for all tenants — check for open write rules."""
import requests, pathlib, json, base64, time

TOKENS = {
    "we88c":    ".fb_we88c_id_token.txt",
    "slxoz1688":".fb_slxoz1688_id_token.txt",
    "vak88z2":  ".fb_vak88z2_id_token.txt",
}

RTDB_REGIONS = [
    "asia-southeast1",
    "us-central1",
    "europe-west1",
]

def decode_token(tok):
    p = tok.split(".")[1]; p += "=" * (-len(p) % 4)
    return json.loads(base64.b64decode(p))

def probe_rtdb(tenant, tok, project, uid):
    base_candidates = [
        f"https://{project}-default-rtdb.asia-southeast1.firebasedatabase.app",
        f"https://{project}-default-rtdb.firebaseio.com",
    ]
    for base in base_candidates:
        paths = [
            "/",
            f"/users/{uid}",
            f"/wallet/{uid}",
            f"/balance/{uid}",
            "/wallet",
            "/balances",
            "/credits",
        ]
        for path in paths:
            try:
                r = requests.get(f"{base}{path}.json",
                    params={"auth": tok}, timeout=6)
                body = r.text[:120]
                if r.status_code != 401 or path == "/":
                    print(f"  [{r.status_code}] {base.split('//')[1].split('.')[0]} {path} → {body!r}")
                if r.status_code == 200 and r.text not in ("null", ""):
                    print(f"  *** DATA FOUND ***")
            except Exception as e:
                if path == "/":
                    print(f"  ERR {base.split('//')[1][:40]}: {e!s:.50}")

for tenant, tok_file in TOKENS.items():
    p = pathlib.Path(tok_file)
    if not p.exists():
        print(f"\n[{tenant}] token file missing")
        continue
    tok = p.read_text().strip()
    try:
        claims = decode_token(tok)
        project = claims.get("aud", "")
        uid = claims.get("sub", "")
        exp = claims.get("exp", 0)
        age_m = int((time.time() - exp) / 60)
        print(f"\n=== {tenant} === project={project} uid={uid[:8]}... exp={'+' if exp > time.time() else '-'}{abs(age_m)}m")
        probe_rtdb(tenant, tok, project, uid)
    except Exception as e:
        print(f"\n[{tenant}] decode error: {e}")
