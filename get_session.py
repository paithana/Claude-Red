#!/usr/bin/env python3
"""
get_session.py — Obtain JWT + AWSALB cookies from we88c.com / vak88z login
Writes .jwt.we88c / .jwt and .awsalb to current directory for use by other probe scripts.

Usage:
    uv run get_session.py --user 0972571110 --pass 'yourpass'
    uv run get_session.py --user 0972571110 --pass 'yourpass' --platform we88c
    uv run get_session.py --user 0972571110 --pass 'yourpass' --platform vak88z
    uv run get_session.py --user 0972571110 --pass 'yourpass' --watch  # refresh loop

Credentials: pass via CLI or WE88_USER / WE88_PASS env vars.
"""
import argparse, json, os, ssl, sys, time, uuid
import urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

PLATFORMS = {
    "we88zz": {
        "login_url":  "https://54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com/mb/authenticate",
        "origin":     "https://m.we88c.com",
        "referer":    "https://m.we88c.com/th/login",
        "template":   "vn",
        "jwt_file":   ".jwt.we88c",
    },
    "vak88z": {
        "login_url":  "https://54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com/mb/authenticate",
        "origin":     "https://m.vak88z3.com",
        "referer":    "https://m.vak88z3.com/th/login",
        "template":   "vn",
        "jwt_file":   ".jwt",
    },
}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode    = ssl.CERT_NONE


def do_login(username: str, password: str, platform: str = "we88zz") -> dict:
    cfg  = PLATFORMS[platform]
    body = json.dumps({
        "username":   username,
        "password":   password,
        "device_id":  str(uuid.uuid4()),
    }).encode()

    # Load existing AWSALB — gateway requires it even on /mb/authenticate
    existing_alb = ""
    for env_k in ("AWSALB",):
        existing_alb = os.environ.get(env_k, "")
        if existing_alb: break
    if not existing_alb:
        _alb_p = Path(".awsalb")
        if _alb_p.exists(): existing_alb = _alb_p.read_text().strip()

    hdrs = {
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "User-Agent":    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15",
        "Origin":        cfg["origin"],
        "Referer":       cfg["referer"],
        "template":      cfg["template"],
        "CorrelationID": str(uuid.uuid4()),
        **({"Cookie": f"AWSALB={existing_alb}; AWSALBCORS={existing_alb}"} if existing_alb else {}),
    }

    r = urllib.request.Request(cfg["login_url"], data=body, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=10, context=CTX) as resp:
            raw_body   = resp.read(8192).decode("utf-8", errors="replace")
            raw_hdrs   = dict(resp.headers)
            status     = resp.status
    except urllib.error.HTTPError as e:
        raw_body   = e.read(4096).decode("utf-8", errors="replace")
        raw_hdrs   = dict(e.headers)
        status     = e.code
    except Exception as ex:
        return {"error": str(ex), "status": 0}

    # Extract JWT from response body
    jwt = ""
    try:
        data = json.loads(raw_body)
        jwt = (
            data.get("token") or
            data.get("access_token") or
            data.get("data", {}).get("token") or
            data.get("data", {}).get("access_token") or
            ""
        )
    except Exception:
        pass

    # Extract AWSALB from Set-Cookie headers
    awsalb = ""
    set_cookie = raw_hdrs.get("Set-Cookie", "") or raw_hdrs.get("set-cookie", "")
    if not set_cookie:
        # urllib may merge multiple Set-Cookie into one header
        for k, v in raw_hdrs.items():
            if k.lower() == "set-cookie" and "AWSALB" in v:
                set_cookie = v
                break

    import re
    m = re.search(r'AWSALB=([^;]+)', set_cookie)
    if m:
        awsalb = m.group(1)

    return {
        "status":  status,
        "jwt":     jwt,
        "awsalb":  awsalb,
        "body":    raw_body[:400],
        "headers": {k: v for k, v in raw_hdrs.items() if k.lower() in
                    ("set-cookie", "content-type", "x-request-id", "correlationid")},
    }


def save_session(jwt: str, awsalb: str, jwt_file: str = ".jwt"):
    Path(jwt_file).write_text(jwt.strip() + "\n")
    Path(".awsalb").write_text(awsalb.strip() + "\n")
    print(f"  {jwt_file} → written")
    print("  .awsalb → written")


def decode_exp(jwt: str) -> int:
    import base64
    try:
        parts = jwt.split(".")
        pad   = parts[1] + "=" * (-len(parts[1]) % 4)
        p     = json.loads(base64.urlsafe_b64decode(pad))
        return p.get("exp", 0)
    except Exception:
        return 0


def fmt_ttl(exp: int) -> str:
    left = exp - time.time()
    if left <= 0: return "EXPIRED"
    h, r = divmod(int(left), 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}h {m:02d}m {s:02d}s"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--user",     metavar="PHONE",    help="Username / phone")
    ap.add_argument("--pass",     metavar="PASS",     dest="password", help="Password")
    ap.add_argument("--platform", "--tenant", metavar="PLATFORM", default="we88zz",
                    dest="platform", help="Platform: " + " / ".join(PLATFORMS) + " (aliases: we88, vak88, lux)")
    ap.add_argument("--awsalb",   metavar="COOKIE",   help="AWSALB cookie value (overrides .awsalb file; use - to prompt)")
    ap.add_argument("--watch",    action="store_true",
                    help="Refresh session before expiry (loop)")
    ap.add_argument("--refresh-at", type=int, default=600,
                    help="Refresh when TTL drops below N seconds (default 600 = 10min)")
    args = ap.parse_args()

    # Fuzzy platform name
    _pmap = {"we88": "we88zz", "we88c": "we88zz", "vak88": "vak88z", "lux": "luxino"}
    args.platform = _pmap.get(args.platform.lower(), args.platform)
    if args.platform not in PLATFORMS:
        print(f"Unknown platform '{args.platform}'. Choose: {', '.join(PLATFORMS)}")
        sys.exit(1)

    username = args.user     or os.environ.get("WE88_USER", "")
    password = args.password or os.environ.get("WE88_PASS", "")

    # Dynamic AWSALB input
    if args.awsalb == "-":
        args.awsalb = input("Paste AWSALB cookie value: ").strip()
    if args.awsalb:
        Path(".awsalb").write_text(args.awsalb.strip() + "\n")
        print(f"  .awsalb → updated from --awsalb flag")

    if not username or not password:
        print("Provide --user and --pass (or WE88_USER / WE88_PASS env vars)")
        sys.exit(1)

    def refresh():
        print(f"\n[{datetime.now(timezone.utc).strftime('%H:%M:%SZ')}] Logging in to {args.platform} as {username}…")
        result = do_login(username, password, args.platform)
        status = result.get("status", 0)
        jwt    = result.get("jwt", "")
        awsalb = result.get("awsalb", "")

        if status == 200 and jwt:
            exp = decode_exp(jwt)
            print(f"  ✓ [{status}] JWT obtained — exp {datetime.fromtimestamp(exp, tz=timezone.utc).strftime('%H:%MZ')} ({fmt_ttl(exp)})")
            if awsalb:
                print(f"  ✓ AWSALB obtained ({awsalb[:20]}…)")
            else:
                print("  ⚠ AWSALB not found in Set-Cookie — may need browser-based login")
            jwt_file = PLATFORMS[args.platform].get("jwt_file", ".jwt")
            save_session(jwt, awsalb, jwt_file)
            return exp
        else:
            print(f"  ✗ [{status}] Login failed: {result.get('body','')[:120]}")
            print("  Hint: AWSALB cookie might be required for initial auth.")
            print("        Capture it from browser DevTools → Network → login request → Cookie header")
            return 0

    if args.watch:
        exp = refresh()
        if not exp:
            sys.exit(1)
        try:
            while True:
                left = exp - time.time()
                if left <= args.refresh_at:
                    exp = refresh()
                    if not exp:
                        break
                else:
                    sleep = min(60, left - args.refresh_at)
                    print(f"  Token valid {fmt_ttl(exp)} — next check in {int(sleep)}s")
                    time.sleep(sleep)
        except KeyboardInterrupt:
            print("\nWatch stopped.")
    else:
        exp = refresh()
        if not exp:
            sys.exit(1)
        print(f"\nRun probe scripts now — token valid for {fmt_ttl(exp)}")
        print("  python3 jwt_chk.py")
        print("  python3 chk_balance.py")
        print("  python3 api_probe.py")


if __name__ == "__main__":
    main()
