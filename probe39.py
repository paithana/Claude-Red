#!/usr/bin/env python3
"""probe39.py — F39 re-verify: cashback-transfer Go crash/deadlock (vak88z2 + slxoz1688)."""
import json, requests, time, pathlib, base64, sys

def load_jwt(path, tid, pbapi_base, creds):
    p = pathlib.Path(path)
    if p.exists():
        jwt = p.read_text().strip()
        try:
            payload = json.loads(base64.urlsafe_b64decode(jwt.split('.')[1] + '=='))
            if payload.get('exp', 0) - time.time() > 300:
                print(f"[JWT] {path}: cached, {(payload['exp']-time.time())/60:.0f}min left")
                return jwt
        except Exception:
            pass
    print(f"[JWT] re-auth {tid}...")
    r = requests.post(f"https://{tid}pbapi.asdgapicenterssdo.com/pb/authentication",
                      json={"strategy": "local", **creds},
                      headers={"Content-Type": "application/json"}, timeout=15)
    if not r.ok:
        print(f"[JWT] FAIL {r.status_code}: {r.text[:200]}")
        return None
    jwt = r.json().get("accessToken") or r.json().get("token")
    if jwt:
        p.write_text(jwt)
    return jwt


tenants = [
    {
        "name": "vak88z2",
        "tid": "af6efb584a3d317b5a11ab6209b88e1b",
        "jwt_file": ".jwt.vak88z2",
        "creds": {"username": "0811111111", "password": "oceanslotz"},
    },
    {
        "name": "slxoz1688",
        "tid": "09b2c3ab78fa9e070e9b0517ed1508d5",
        "jwt_file": "slxoz1688.jwt.txt",
        "creds": {"username": "0972571110", "password": "Aa112233"},
    },
]

for t in tenants:
    tid = t["tid"]
    mgapi = f"https://{tid}mgapi.asdgapicenterssdo.com"
    h = {"template": "vn", "Content-Type": "application/json"}

    jwt = load_jwt(t["jwt_file"], tid, f"https://{tid}pbapi.asdgapicenterssdo.com", t["creds"])
    if not jwt:
        print(f"[{t['name']}] skip — no JWT\n")
        continue
    h["Authorization"] = f"Bearer {jwt}"

    print(f"\n{'='*60}")
    print(f"[{t['name']}] Checking cashback balance...")
    r = requests.get(f"{mgapi}/mb/cashback-transaction?status=available", headers=h, timeout=15)
    print(f"  cashback-transaction: {r.status_code} {r.text[:300]}")

    r2 = requests.get(f"{mgapi}/mb/cashback", headers=h, timeout=15)
    print(f"  cashback: {r2.status_code} {r2.text[:300]}")

    available = 0.0
    for resp in [r, r2]:
        if resp.ok:
            try:
                d = resp.json()
                val = (d.get("data") or d).get("available")
                if val is not None:
                    available = float(val)
                    print(f"  available cashback: {available} THB")
                    break
            except Exception:
                pass

    if available <= 0:
        print(f"  [SKIP] No available cashback — skipping transfer probe")
        continue

    print(f"\n[{t['name']}] F39 crash probe — available={available} THB")
    amounts = []
    if available >= 1:
        amounts += [1, int(available * 0.25), int(available * 0.5), round(available * 0.99, 2), round(available, 2)]
    amounts = sorted(set(a for a in amounts if 0 < a <= available))

    for amt in amounts:
        print(f"  POST /mb/cashback-transfer amount={amt} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            r = requests.post(f"{mgapi}/mb/cashback-transfer",
                              json={"amount": amt}, headers=h, timeout=35)
            elapsed = time.time() - t0
            flag = "*** DEADLOCK ***" if elapsed > 25 else ("*** PANIC ***" if r.status_code == 502 else "")
            print(f"{r.status_code} ({elapsed:.1f}s) {flag} {r.text[:120]}")
        except requests.exceptions.Timeout:
            elapsed = time.time() - t0
            print(f"TIMEOUT ({elapsed:.0f}s) *** DEADLOCK CONFIRMED ***")
        except Exception as e:
            print(f"ERR {e}")

    print(f"\n[{t['name']}] Also probing rebate-transfer...")
    r = requests.get(f"{mgapi}/mb/rebate", headers=h, timeout=15)
    print(f"  GET /mb/rebate: {r.status_code} {r.text[:200]}")
    r = requests.post(f"{mgapi}/mb/rebate-transfer", json={"amount": 1}, headers=h, timeout=30)
    print(f"  POST /mb/rebate-transfer amount=1: {r.status_code} {r.text[:200]}")

    print(f"\n[{t['name']}] Wallet after probes:")
    rw = requests.get(f"{mgapi}/mb/wallet", headers=h, timeout=10)
    if rw.ok:
        d = rw.json().get("data", [])
        bal = d[0].get("balance") if isinstance(d, list) and d else "?"
        print(f"  balance: {bal} THB")

print("\n=== DONE ===")
