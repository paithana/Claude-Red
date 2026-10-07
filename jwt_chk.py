#!/usr/bin/env python3
"""
jwt_chk.py — JWT decoder + live validation per platform
Usage:
    uv run jwt_chk.py                        # reads .jwt or JWT env
    uv run jwt_chk.py --jwt eyJhbGci...      # explicit token
    uv run jwt_chk.py --platform we88zz      # test against we88zz gateway
    uv run jwt_chk.py --all                  # test all known gateways
    uv run jwt_chk.py --watch                # loop every 30s until expiry
"""
import argparse, base64, json, os, ssl, sys, time, uuid
import urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── Platform → gateway map ────────────────────────────────────────────────────
PLATFORMS = {
    "we88zz": {
        "gateway": "54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com",
        "template": "vn",
        "origin":   "https://m.we88c.com",
        "jwt_file": ".jwt.we88c",
    },
    "vak88z": {
        "gateway": "54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com",
        "template": "vn",
        "origin":   "https://m.vak88z3.com",
        "jwt_file": ".jwt",
    },
    "luxino": {
        "gateway": "54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com",
        "template": "vn",
        "origin":   "https://m.luxino.com",
        "jwt_file": ".jwt",
    },
}
DEFAULT_PLATFORM = "we88zz"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode    = ssl.CERT_NONE


# ── JWT helpers ───────────────────────────────────────────────────────────────
def _b64pad(s: str) -> str:
    return s + "=" * (-len(s) % 4)

def decode_jwt(token: str) -> dict:
    parts = token.strip().split(".")
    if len(parts) < 2:
        return {}
    try:
        header  = json.loads(base64.urlsafe_b64decode(_b64pad(parts[0])))
        payload = json.loads(base64.urlsafe_b64decode(_b64pad(parts[1])))
        return {"header": header, "payload": payload, "sig_present": len(parts) == 3}
    except Exception as e:
        return {"error": str(e)}

def ttl(exp: int) -> str:
    left = exp - time.time()
    if left <= 0:
        return "EXPIRED"
    h, r = divmod(int(left), 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}h {m:02d}m {s:02d}s"

def exp_dt(exp: int) -> str:
    return datetime.fromtimestamp(exp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── API probe ─────────────────────────────────────────────────────────────────
def live_check(token: str, platform: str) -> dict:
    cfg  = PLATFORMS.get(platform, PLATFORMS[DEFAULT_PLATFORM])
    host = cfg["gateway"]
    url  = f"https://{host}/mb/users?_t={int(time.time()*1000)}"
    alb = load_awsalb()
    hdrs = {
        "Authorization":  f"Bearer {token}",
        "Accept":         "application/json",
        "template":       cfg["template"],
        "Referer":        cfg["origin"] + "/th/deposit",
        "CorrelationID":  str(uuid.uuid4()),
        "User-Agent":     "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15",
        **({"Cookie": f"AWSALB={alb}; AWSALBCORS={alb}"} if alb else {}),
    }
    r = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(r, timeout=8, context=CTX) as resp:
            body = json.loads(resp.read(8192))
            if body.get("data"):
                u = body["data"][0]
                return {
                    "status":   resp.status,
                    "username": u.get("username"),
                    "name":     f"{u.get('first_name','')} {u.get('last_name','')}".strip(),
                    "game_id":  u.get("user_in_game"),
                    "sub":      u.get("id"),
                }
            return {"status": resp.status, "body": body}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "body": e.read(512).decode()}
    except Exception as ex:
        return {"status": 0, "error": str(ex)}


# ── Display ───────────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
DIM    = "\033[2m"

def colour_ttl(exp: int) -> str:
    left = exp - time.time()
    t    = ttl(exp)
    if left <= 0:     return f"{RED}{t}{RESET}"
    if left < 900:    return f"{RED}{t}{RESET}"
    if left < 1800:   return f"{YELLOW}{t}{RESET}"
    return f"{GREEN}{t}{RESET}"

def print_jwt(token: str, platform: str | None = None, live: bool = True):
    decoded = decode_jwt(token)
    if "error" in decoded:
        print(f"{RED}[!] JWT decode error: {decoded['error']}{RESET}")
        return

    hdr = decoded["header"]
    pay = decoded["payload"]
    exp = pay.get("exp", 0)
    iat = pay.get("iat", 0)
    now = time.time()

    print(f"\n{BOLD}{'─'*60}{RESET}")
    print(f"{BOLD}JWT Analysis{RESET}  ({hdr.get('alg','?')} / {hdr.get('typ','?')})")
    print(f"{'─'*60}")

    # Core fields
    print(f"  {CYAN}sub{RESET}              {pay.get('sub','–')}")
    print(f"  {CYAN}cf{RESET}               {pay.get('cf','–')}")
    print(f"  {CYAN}is_not_complete{RESET}  {pay.get('is_not_complete','–')}")
    print(f"  {CYAN}iat{RESET}              {exp_dt(iat)}  ({datetime.fromtimestamp(iat, tz=timezone.utc).strftime('%H:%M:%S UTC')})")
    print(f"  {CYAN}exp{RESET}              {exp_dt(exp)}  {colour_ttl(exp)}")

    if exp < now:
        print(f"\n  {RED}✗ TOKEN EXPIRED{RESET}")
    else:
        print(f"\n  {GREEN}✓ TOKEN VALID{RESET}")

    # Extra fields
    extra = {k: v for k, v in pay.items() if k not in ("sub", "cf", "is_not_complete", "exp", "iat")}
    if extra:
        print(f"  {DIM}extra: {json.dumps(extra)}{RESET}")

    # Live API check
    platforms_to_check = list(PLATFORMS.keys()) if platform == "all" else [platform or DEFAULT_PLATFORM]

    if live and exp > now:
        print(f"\n{BOLD}Live API check:{RESET}")
        for plat in platforms_to_check:
            result = live_check(token, plat)
            status = result.get("status", 0)
            if status == 200:
                print(f"  {GREEN}✓{RESET} [{plat}] {status}  "
                      f"user={result.get('username','?')}  "
                      f"name={result.get('name','?')}  "
                      f"game={result.get('game_id','?')}")
            elif status == 401:
                print(f"  {RED}✗{RESET} [{plat}] {status}  REJECTED")
            else:
                print(f"  {YELLOW}⚠{RESET} [{plat}] {status}  {str(result.get('body',''))[:60]}")
    elif exp <= now:
        print(f"\n  {DIM}(skipping live check — token expired){RESET}")

    print(f"{'─'*60}\n")


# ── Token loading ─────────────────────────────────────────────────────────────
def load_token(arg: str | None) -> str:
    if arg:
        return arg.strip()
    for env in ("JWT", "WE88_JWT"):
        v = os.environ.get(env, "")
        if v:
            return v.strip()
    for candidate in (Path(".jwt.we88c"), Path(".jwt"), Path.home() / ".claude/jobs/.jwt"):
        if candidate.exists():
            t = candidate.read_text().strip()
            if t:
                return t
    return ""

def load_awsalb() -> str:
    v = os.environ.get("AWSALB", "")
    if v: return v
    p = Path(".awsalb")
    return p.read_text().strip() if p.exists() else ""


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jwt",      metavar="TOKEN",    help="JWT token string")
    ap.add_argument("--platform", metavar="PLATFORM", help="Platform to live-check: " + "/".join(PLATFORMS))
    ap.add_argument("--all",      action="store_true", help="Check all platforms")
    ap.add_argument("--watch",    action="store_true", help="Loop every 30s until expiry")
    ap.add_argument("--no-live",  action="store_true", help="Decode only, skip API call")
    args = ap.parse_args()

    token = load_token(args.jwt)
    if not token:
        print("No JWT found. Use --jwt TOKEN, set JWT env var, or write token to .jwt")
        sys.exit(1)

    platform = "all" if args.all else args.platform
    live     = not args.no_live

    if args.watch:
        decoded = decode_jwt(token)
        exp     = decoded.get("payload", {}).get("exp", 0)
        try:
            while time.time() < exp:
                print_jwt(token, platform=platform, live=live)
                remaining = exp - time.time()
                if remaining <= 0:
                    break
                sleep = min(30, remaining)
                print(f"{DIM}Next check in {int(sleep)}s  (Ctrl+C to stop){RESET}")
                time.sleep(sleep)
        except KeyboardInterrupt:
            pass
        print(f"\n{RED}Token expired or watch stopped.{RESET}")
    else:
        print_jwt(token, platform=platform, live=live)


if __name__ == "__main__":
    main()
