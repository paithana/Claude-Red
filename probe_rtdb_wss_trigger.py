#!/usr/bin/env python3
"""probe_rtdb_wss_trigger.py — Check if RTDB writes trigger platform WSS events."""
import json
import requests
import asyncio
import websockets
import time
import uuid

TID = "54ef7626cb381f4bab8be91f0cdbce47"
PLAYER_ID = "266d74e3-d6ca-47eb-b9ac-b8c45574bad4"
API_KEY = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"
RTDB_URL = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"

# Get fresh tokens
print("=== Getting tokens ===")
JWT = open(".jwt.we88c").read().strip()
print(f"Platform JWT: {JWT[:50]}...")

# Get Firebase token
r = requests.get(f"https://{TID}mgapi.asdgapicenterssdo.com/mb/firebase-token",
    headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
    timeout=15)
custom_token = r.json().get("firebaseToken")
print(f"Custom token: {'OK' if custom_token else 'FAIL'}")

# Exchange for ID token
r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}",
    json={"token": custom_token, "returnSecureToken": True},
    timeout=15)
fb_token = r.json().get("idToken")
print(f"Firebase ID token: {'OK' if fb_token else 'FAIL'}")

# Get initial wallet
def get_wallet():
    r = requests.get(f"https://{TID}mgapi.asdgapicenterssdo.com/mb/wallet",
        headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
        timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else "?"
    return f"ERR:{r.status_code}"

print(f"\nInitial wallet: {get_wallet()} THB")

async def monitor_and_write():
    # Connect to platform WSS
    wss_url = f"wss://{TID}mgapi.asdgapicenterssdo.com/mb/ws?token={JWT}"
    print(f"\n=== Connecting to platform WSS ===")

    try:
        async with websockets.connect(wss_url, ping_interval=20, close_timeout=5) as ws:
            print("[WSS CONNECTED]")

            # Also connect to Firebase RTDB WSS
            fb_wss_url = RTDB_URL.replace("https://", "wss://") + "/.ws?v=5"

            try:
                async with websockets.connect(fb_wss_url, close_timeout=5) as fb_ws:
                    print("[FB WSS CONNECTED]")

                    # Authenticate to Firebase
                    await fb_ws.recv()  # Handshake
                    auth_msg = {"t": "d", "d": {"r": 0, "a": "auth", "b": {"cred": fb_token}}}
                    await fb_ws.send(json.dumps(auth_msg))
                    await fb_ws.recv()  # Auth response
                    print("[FB AUTHENTICATED]")

                    # Subscribe to our user path in Firebase
                    sub_msg = {"t": "d", "d": {"r": 1, "a": "q", "b": {"p": f"/users/{PLAYER_ID}", "h": ""}}}
                    await fb_ws.send(json.dumps(sub_msg))
                    print(f"[FB SUBSCRIBED to /users/{PLAYER_ID}]")

                    # Write a deposit approval via REST
                    test_id = str(uuid.uuid4())
                    test_amount = 100000.0
                    print(f"\n=== Writing DEPOSIT_APPROVE to RTDB ===")
                    print(f"  ID: {test_id}")
                    print(f"  Amount: {test_amount}")

                    deposit_data = {
                        "amount": str(test_amount),
                        "approve_status": "success",
                        "approved_by": "admin",
                        "status": "success",
                        "timestamp": int(time.time() * 1000),
                        "uid": PLAYER_ID,
                        "credited": True,
                        "bank_code": "KBANK",
                        "bank_no": "1029600000052",
                        "transaction_type": "deposit"
                    }

                    url = f"{RTDB_URL}/users/{PLAYER_ID}/DEPOSIT_APPROVE/{test_id}.json?auth={fb_token}"
                    r = requests.put(url, json=deposit_data, timeout=15)
                    print(f"  RTDB write: {r.status_code}")

                    # Also write to DEPOSIT_CONFIRM
                    confirm_data = {
                        "amount": test_amount,
                        "approve_status": "success",
                        "bank_code": "KBANK",
                        "created_at": int(time.time() * 1000),
                        "credited": True,
                        "processed": True,
                        "status": "success",
                        "tid": TID,
                        "tx_id": test_id,
                        "uid": PLAYER_ID
                    }
                    url = f"{RTDB_URL}/users/{PLAYER_ID}/DEPOSIT_CONFIRM/{test_id}.json?auth={fb_token}"
                    r = requests.put(url, json=confirm_data, timeout=15)
                    print(f"  DEPOSIT_CONFIRM write: {r.status_code}")

                    # Write to deposit_transaction
                    tx_data = {
                        "amount": test_amount,
                        "approve_status": "success",
                        "credited": True,
                        "id": test_id,
                        "status": "success",
                        "timestamp": int(time.time()),
                        "uid": PLAYER_ID
                    }
                    url = f"{RTDB_URL}/users/{PLAYER_ID}/deposit_transaction/{test_id}.json?auth={fb_token}"
                    r = requests.put(url, json=tx_data, timeout=15)
                    print(f"  deposit_transaction write: {r.status_code}")

                    # Monitor both WSS for events
                    print(f"\n=== Monitoring for events (15s) ===")
                    start = asyncio.get_event_loop().time()

                    async def listen_platform():
                        while asyncio.get_event_loop().time() - start < 15:
                            try:
                                msg = await asyncio.wait_for(ws.recv(), timeout=2)
                                data = json.loads(msg)
                                topic = data.get("topic_name", "?")
                                if topic != "JACKPOT_CAMPAIGN":
                                    print(f"  [PLATFORM] {topic}: {json.dumps(data)[:150]}")
                            except asyncio.TimeoutError:
                                pass
                            except Exception as e:
                                print(f"  [PLATFORM ERROR] {e}")
                                break

                    async def listen_firebase():
                        while asyncio.get_event_loop().time() - start < 15:
                            try:
                                msg = await asyncio.wait_for(fb_ws.recv(), timeout=2)
                                data = json.loads(msg)
                                if '"d":{"a":"d"' in msg or '"a":"c"' in msg:  # data push or merge
                                    print(f"  [FIREBASE] {msg[:200]}")
                            except asyncio.TimeoutError:
                                pass
                            except Exception as e:
                                print(f"  [FB ERROR] {e}")
                                break

                    await asyncio.gather(listen_platform(), listen_firebase())

            except Exception as e:
                print(f"[FB WSS ERROR] {e}")

    except Exception as e:
        print(f"[WSS ERROR] {e}")

    # Check wallet after writes
    print(f"\n=== Final wallet: {get_wallet()} THB ===")

asyncio.run(monitor_and_write())
