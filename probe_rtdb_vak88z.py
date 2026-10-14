#!/usr/bin/env python3
"""probe_rtdb_vak88z.py — Access vak88z Firebase RTDB with fresh token."""
import json
import requests
import asyncio
import websockets

API_KEY = "AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE"
RTDB_URL = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"

def refresh_token():
    refresh_tok = open("fb_refresh_token_new.txt").read().strip()
    url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
    r = requests.post(url, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_tok
    }, timeout=15)
    if r.ok:
        data = r.json()
        return data.get("id_token"), data.get("refresh_token")
    print(f"Refresh failed: {r.text[:200]}")
    return None, None

def probe_rtdb(id_token):
    paths = [
        "/",
        "/users",
        "/deposits",
        "/deposit_requests",
        "/transactions",
        "/wallets",
        "/players",
        "/notifications",
        "/config",
        "/settings",
        "/admin",
        "/pending",
        "/approved",
        "/slip",
        "/match",
        "/auto_deposit",
        "/queue",
        "/events",
        "/logs",
    ]

    print(f"\n=== Probing RTDB paths ===")
    for path in paths:
        url = f"{RTDB_URL}{path}.json?auth={id_token}&shallow=true"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    print(f"  [DATA] {path}: {json.dumps(data)[:300]}")
                else:
                    print(f"  [NULL] {path}")
            elif r.status_code == 401:
                pass  # Skip auth errors silently
            else:
                print(f"  [{r.status_code}] {path}")
        except Exception as e:
            print(f"  [ERR] {path}: {e}")

async def wss_rtdb(id_token):
    wss_url = RTDB_URL.replace("https://", "wss://") + "/.ws?v=5"
    print(f"\n=== WSS Connection ===")
    print(f"URL: {wss_url}")

    try:
        async with websockets.connect(wss_url, close_timeout=5) as ws:
            print(f"[CONNECTED]")

            # Receive initial message
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                print(f"Initial: {msg[:200]}")
            except asyncio.TimeoutError:
                pass

            # Send auth
            auth_msg = {
                "t": "d",
                "d": {
                    "r": 0,
                    "a": "auth",
                    "b": {"cred": id_token}
                }
            }
            await ws.send(json.dumps(auth_msg))
            print(f"Sent auth")

            # Listen for responses
            for i in range(10):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    data = json.loads(msg)
                    msg_type = data.get("d", {}).get("b", {}).get("s", "?")
                    print(f"  [{i}] {msg[:300]}")

                    # If auth successful, try to subscribe to root
                    if "ok" in msg.lower() or i == 1:
                        sub_msg = {
                            "t": "d",
                            "d": {
                                "r": 1,
                                "a": "q",
                                "b": {
                                    "p": "/",
                                    "h": ""
                                }
                            }
                        }
                        await ws.send(json.dumps(sub_msg))
                        print(f"  Subscribed to /")

                except asyncio.TimeoutError:
                    break

    except Exception as e:
        print(f"[ERROR] {e}")

# Main
print("=== vak88z Firebase RTDB Probe ===")
id_token, new_refresh = refresh_token()
if id_token:
    print(f"ID token: {id_token[:60]}...")

    # Save new refresh token
    with open("fb_refresh_token_new.txt", "w") as f:
        f.write(new_refresh)

    probe_rtdb(id_token)
    asyncio.run(wss_rtdb(id_token))
else:
    print("Failed to get ID token")
