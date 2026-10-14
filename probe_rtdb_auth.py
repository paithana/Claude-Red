#!/usr/bin/env python3
"""probe_rtdb_auth.py — Access Firebase RTDB with authenticated token.

   Refresh the FB ID token and probe RTDB endpoints.
"""
import json
import requests
import asyncio
import websockets

# Firebase API keys (from the nuxt apps)
FIREBASE_CONFIGS = {
    "vak88z": {
        "apiKey": "AIzaSyAyKD2lDZpBvZkKcfWR3xL5E_MvBbxp8-0",
        "rtdb": "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"
    },
    "we88zz": {
        "apiKey": "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s",  # we88c key
        "rtdb": "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"
    },
    "slxoz1688": {
        "apiKey": "AIzaSyAP6AJiPGOqHJnSMq4fLjJN1TQ8DWbYFJo",
        "rtdb": "https://slxoz1688-default-rtdb.asia-southeast1.firebasedatabase.app"
    },
}

def refresh_token(api_key, refresh_token):
    """Exchange refresh token for new ID token"""
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
    r = requests.post(url, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }, timeout=15)
    if r.ok:
        data = r.json()
        return data.get("id_token"), data.get("refresh_token")
    print(f"Refresh failed: {r.status_code} {r.text[:200]}")
    return None, None

def probe_rtdb(rtdb_url, id_token):
    """Probe RTDB paths with auth token"""
    paths = [
        "/",
        "/users",
        "/deposits",
        "/transactions",
        "/wallets",
        "/players",
        "/notifications",
        "/config",
        "/settings",
        "/admin",
    ]

    print(f"\n=== Probing {rtdb_url} ===")
    for path in paths:
        url = f"{rtdb_url}{path}.json?auth={id_token}&shallow=true"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data:
                    print(f"  [OK] {path}: {str(data)[:200]}")
                else:
                    print(f"  [EMPTY] {path}")
            elif r.status_code == 401:
                print(f"  [401] {path}: Unauthorized")
            else:
                print(f"  [{r.status_code}] {path}: {r.text[:100]}")
        except Exception as e:
            print(f"  [ERR] {path}: {e}")

async def wss_rtdb(rtdb_url, id_token):
    """Connect to RTDB via WebSocket"""
    # Convert HTTPS to WSS
    wss_url = rtdb_url.replace("https://", "wss://") + "/.ws?v=5"
    print(f"\n=== WSS {wss_url} ===")

    try:
        async with websockets.connect(wss_url, close_timeout=5) as ws:
            print(f"  [CONNECTED]")

            # Send auth with token
            auth_msg = {
                "t": "d",
                "d": {
                    "r": 0,
                    "a": "auth",
                    "b": {"cred": id_token}
                }
            }
            await ws.send(json.dumps(auth_msg))

            # Listen for auth response
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"  Auth response: {msg[:300]}")

                # Subscribe to root
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

                # Listen for data
                for _ in range(5):
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=3)
                        print(f"  Data: {msg[:300]}")
                    except asyncio.TimeoutError:
                        break

            except asyncio.TimeoutError:
                print(f"  [TIMEOUT waiting for response]")

    except Exception as e:
        print(f"  [ERROR] {e}")

# Load refresh token
print("=== Loading refresh tokens ===")
try:
    refresh_tok_vak = open("fb_refresh_token_new.txt").read().strip()
    print(f"  vak88z refresh token: {refresh_tok_vak[:30]}...")
except:
    refresh_tok_vak = None
    print("  vak88z: no refresh token")

# Refresh and probe
if refresh_tok_vak:
    for proj, config in FIREBASE_CONFIGS.items():
        print(f"\n\n{'='*50}")
        print(f"PROJECT: {proj}")
        print(f"{'='*50}")

        # Try refreshing with vak88z token (may work cross-project if same Firebase)
        id_token, new_refresh = refresh_token(config["apiKey"], refresh_tok_vak)
        if id_token:
            print(f"  Got ID token: {id_token[:50]}...")
            probe_rtdb(config["rtdb"], id_token)
            asyncio.run(wss_rtdb(config["rtdb"], id_token))
        else:
            print(f"  Failed to get ID token for {proj}")

print("\n\n=== Done ===")
