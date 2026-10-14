#!/usr/bin/env python3
"""probe_ws_player.py — Connect to /pb/ws with fresh JWT, listen + send deposit msgs.

   pbapi WebSocket opened but closed immediately — likely expired JWT.
   First refresh JWT via /pb/authentication, then retry WS.
"""
import json, pathlib, time, ssl, threading, base64, requests

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI  = f"https://{TID}bgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

PLAYER_UID = "eea830ab-b187-4f21-9b79-28e2773b2f6b"
BANK_INFO  = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT   = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

try:
    import websocket
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client", "-q"])
    import websocket

def check_jwt_exp(jwt):
    try:
        parts = jwt.split(".")
        pad = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(pad))
        exp = payload.get("exp", 0)
        remaining = exp - time.time()
        return remaining, payload
    except:
        return 0, {}

def refresh_jwt():
    """Re-auth to get fresh player JWT."""
    try:
        r = requests.post(f"{PBAPI}/pb/authentication",
                          headers={"Content-Type": "application/json",
                                   "Cookie": f"AWSALB={AWSALB}"},
                          json={"strategy": "local", "username": "0972571110",
                                "password": "Aa112233"},
                          timeout=15)
        if r.status_code == 201 and "accessToken" in r.text:
            jwt = r.json().get("accessToken", "")
            pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").write_text(jwt)
            print(f"  [!!!] JWT refreshed (exp in {check_jwt_exp(jwt)[0]/3600:.1f}h)")
            return jwt
        else:
            print(f"  Auth failed: HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  Auth error: {e}")
    return None

# ── Load / refresh JWT ────────────────────────────────────────────────────────
JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
remaining, payload = check_jwt_exp(JWT)
print(f"JWT check: exp in {remaining:.0f}s ({remaining/3600:.1f}h)")

if remaining < 300:  # < 5 min remaining
    print("JWT expired or near-expiry — refreshing...")
    new_jwt = refresh_jwt()
    if new_jwt:
        JWT = new_jwt
    else:
        print("  Using existing JWT anyway")
else:
    print(f"  JWT still valid ({remaining/3600:.1f}h remaining)")

# ── WebSocket connection helper ───────────────────────────────────────────────
def try_ws_listen(url, send_msgs=None, timeout=12):
    """Connect, listen for messages, optionally send."""
    received = []
    errors   = []
    opened   = threading.Event()
    done     = threading.Event()

    def on_open(ws):
        opened.set()
        print(f"  [OPEN] {url[:80]}")
        if send_msgs:
            time.sleep(1.0)  # Wait for server to send welcome/auth challenge
            for msg in send_msgs:
                try:
                    payload = msg if isinstance(msg, str) else json.dumps(msg)
                    ws.send(payload)
                    print(f"  [SENT] {payload[:100]}")
                    time.sleep(0.3)
                except Exception as e:
                    errors.append(f"send_err:{e}")
        time.sleep(3)
        try: ws.close()
        except: pass

    def on_message(ws, message):
        received.append(message)
        print(f"  [MSG!!!] {str(message)[:500]}")

    def on_error(ws, error):
        err_str = str(error)[:120]
        if "NoneType" not in err_str and "errno" not in err_str.lower():
            errors.append(err_str)
            print(f"  [ERR] {err_str}")
        elif "401" in err_str or "403" in err_str:
            print(f"  [AUTH_ERR] {err_str}")
        done.set()

    def on_close(ws, code, msg):
        print(f"  [CLOSE] code={code} msg={msg}")
        done.set()

    ws_app = websocket.WebSocketApp(
        url,
        header=[f"Authorization: Bearer {JWT}",
                "Origin: https://m.vak88z2.com"],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    t = threading.Thread(
        target=ws_app.run_forever,
        kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE},
                "ping_interval": 0},
        daemon=True
    )
    t.start()
    done.wait(timeout=timeout)
    ws_app.close()
    return received, errors

# ── Deposit notification messages ─────────────────────────────────────────────
DEPOSIT_MSGS = [
    # Auth first
    {"token": JWT},
    # Deposit notification formats
    {"topic_name": "DEPOSIT_APPROVE",
     "data": {"user_id": PLAYER_UID, "amount": 10000, "status": "success"},
     "notification": [{"type": "DEPOSIT_APPROVE", "is_read": False}]},
    {"topic_name": "TRANSACTION_DEPOSIT_APPROVE",
     "data": {"user_id": PLAYER_UID, "amount": 10000}},
    {"action": "deposit_approve", "user_id": PLAYER_UID, "amount": 10000},
    {"type": "DEPOSIT", "status": "success", "amount": 10000, "user_id": PLAYER_UID},
]

# ── 1. Listen-only on /pb/ws (with fresh JWT in URL) ─────────────────────────
print(f"\n=== /pb/ws LISTEN ONLY ===")
url = f"wss://{TID}pbapi.asdgapicenterssdo.com/pb/ws?token={JWT}"
msgs, errs = try_ws_listen(url, send_msgs=None, timeout=8)
print(f"  received {len(msgs)} msgs, {len(errs)} errors")

# ── 2. Listen + send deposit msgs on /pb/ws ────────────────────────────────────
print(f"\n=== /pb/ws SEND DEPOSIT MSGS ===")
msgs, errs = try_ws_listen(url, send_msgs=DEPOSIT_MSGS, timeout=12)
print(f"  received {len(msgs)} msgs, {len(errs)} errors")

# ── 3. Try /bo/ws with player JWT (priv-esc) ────────────────────────────────
print(f"\n=== /bo/ws with player JWT ===")
bo_url = f"wss://{TID}bgapi.asdgapicenterssdo.com/bo/ws?token={JWT}"
msgs, errs = try_ws_listen(bo_url, send_msgs=DEPOSIT_MSGS[:3], timeout=10)
print(f"  received {len(msgs)} msgs, {len(errs)} errors")

# ── 4. Check wallet after WS sends ────────────────────────────────────────────
print(f"\n=== Wallet check ===")
try:
    r = requests.get(f"{MGAPI}/mb/wallet",
                     headers={"Authorization": f"Bearer {JWT}", "template": "vn",
                              "Cookie": f"AWSALB={AWSALB}"},
                     timeout=10)
    balance = r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"
    print(f"  balance: {balance}")
except Exception as e:
    print(f"  wallet error: {e}")

print("\n=== Done ===")
