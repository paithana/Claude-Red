#!/usr/bin/env python3
"""probe_rtdb_wss_paths.py — Try various paths on Firebase RTDB via WSS."""
import json
import requests
import asyncio
import websockets

API_KEY = "AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE"
RTDB_URL = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"
USER_ID = "ff6c08fb-c109-4c33-9b9f-342e2aca3822"

def refresh_token():
    refresh_tok = open("fb_refresh_token_new.txt").read().strip()
    url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
    r = requests.post(url, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_tok
    }, timeout=15)
    if r.ok:
        return r.json().get("id_token")
    return None

async def wss_probe(id_token):
    wss_url = RTDB_URL.replace("https://", "wss://") + "/.ws?v=5"
    print(f"=== WSS {wss_url} ===")

    paths_to_try = [
        f"/users/{USER_ID}",
        f"/user/{USER_ID}",
        f"/players/{USER_ID}",
        f"/player/{USER_ID}",
        f"/deposits/{USER_ID}",
        f"/deposit/{USER_ID}",
        f"/wallets/{USER_ID}",
        f"/wallet/{USER_ID}",
        f"/notifications/{USER_ID}",
        f"/transactions/{USER_ID}",
        f"/pending/{USER_ID}",
        f"/queue/{USER_ID}",
        "/public",
        "/config",
        "/settings",
        "/system",
        # Also try with player ID from we88c
        "/users/266d74e3-d6ca-47eb-b9ac-b8c45574bad4",
        "/deposits/266d74e3-d6ca-47eb-b9ac-b8c45574bad4",
    ]

    try:
        async with websockets.connect(wss_url, close_timeout=5) as ws:
            # Receive handshake
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            print(f"Handshake: {msg[:100]}")

            # Auth
            auth_msg = {
                "t": "d",
                "d": {
                    "r": 0,
                    "a": "auth",
                    "b": {"cred": id_token}
                }
            }
            await ws.send(json.dumps(auth_msg))

            # Wait for auth response
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            if '"s":"ok"' in msg:
                print(f"[AUTH OK]")
            else:
                print(f"[AUTH FAIL] {msg[:200]}")
                return

            # Try each path
            print(f"\n=== Subscribing to paths ===")
            accessible_paths = []

            for i, path in enumerate(paths_to_try):
                sub_msg = {
                    "t": "d",
                    "d": {
                        "r": i + 1,
                        "a": "q",  # query/listen
                        "b": {
                            "p": path,
                            "h": ""
                        }
                    }
                }
                await ws.send(json.dumps(sub_msg))

                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=2)
                    data = json.loads(msg)
                    status = data.get("d", {}).get("b", {}).get("s", "?")

                    if status == "ok" or "d" in data.get("d", {}).get("b", {}):
                        content = data.get("d", {}).get("b", {}).get("d", {})
                        if content:
                            print(f"  [DATA] {path}: {json.dumps(content)[:200]}")
                            accessible_paths.append(path)
                        else:
                            print(f"  [EMPTY] {path}")
                            accessible_paths.append(path)
                    elif status == "permission_denied":
                        pass  # Skip silently
                    else:
                        print(f"  [{status}] {path}")

                except asyncio.TimeoutError:
                    pass

            print(f"\n=== Accessible paths: {len(accessible_paths)} ===")
            for p in accessible_paths:
                print(f"  {p}")

            # Monitor for any pushed updates
            print(f"\n=== Monitoring for updates (10s) ===")
            start = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start < 10:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=2)
                    print(f"  Push: {msg[:200]}")
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)

    except Exception as e:
        print(f"[ERROR] {e}")

# Main
id_token = refresh_token()
if id_token:
    asyncio.run(wss_probe(id_token))
else:
    print("Failed to get ID token")
