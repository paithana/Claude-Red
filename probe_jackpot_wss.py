#!/usr/bin/env python3
"""probe_jackpot_wss.py — Jackpot WSS injection + RTDB jackpot paths."""
import json
import requests
import asyncio
import websockets
import time

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
fb_uid = r.json().get("localId")
print(f"Firebase ID token: {'OK' if fb_token else 'FAIL'}")
print(f"Firebase UID: {fb_uid}")

# 1. Check RTDB for jackpot paths
print(f"\n=== 1. Probing RTDB jackpot paths ===")
jackpot_paths = [
    "/jackpot",
    "/jackpots",
    "/jackpot_campaigns",
    "/campaigns",
    f"/users/{PLAYER_ID}/JACKPOT",
    f"/users/{PLAYER_ID}/jackpot",
    f"/users/{PLAYER_ID}/jackpot_wins",
    f"/users/{PLAYER_ID}/JACKPOT_WIN",
    f"/users/{PLAYER_ID}/JACKPOT_CAMPAIGN",
    "/global/jackpot",
    "/config/jackpot",
    "/game/jackpot",
]

for path in jackpot_paths:
    url = f"{RTDB_URL}{path}.json?auth={fb_token}&shallow=true"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data is not None:
                print(f"  [DATA] {path}: {json.dumps(data)[:150]}")
            else:
                print(f"  [NULL] {path}")
        elif "Permission denied" in r.text:
            pass  # Skip denied
        else:
            print(f"  [{r.status_code}] {path}")
    except Exception as e:
        print(f"  [ERROR] {path}: {str(e)[:50]}")

# 2. Try to write jackpot data
print(f"\n=== 2. Testing jackpot write access ===")
test_id = f"jackpot_{int(time.time())}"
jackpot_data = {
    "amount": 999999.0,
    "won": True,
    "timestamp": int(time.time() * 1000),
    "uid": PLAYER_ID,
    "status": "claimed"
}

write_paths = [
    f"/users/{PLAYER_ID}/JACKPOT_WIN/{test_id}",
    f"/users/{PLAYER_ID}/jackpot_wins/{test_id}",
    f"/users/{PLAYER_ID}/JACKPOT_CAMPAIGN/{test_id}",
]

for path in write_paths:
    url = f"{RTDB_URL}{path}.json?auth={fb_token}"
    try:
        r = requests.put(url, json=jackpot_data, timeout=10)
        if r.status_code == 200:
            print(f"  [WRITE OK] {path}")
        elif "Permission denied" in r.text:
            print(f"  [DENIED] {path}")
        else:
            print(f"  [{r.status_code}] {path}: {r.text[:80]}")
    except Exception as e:
        print(f"  [ERROR] {path}: {str(e)[:50]}")

# 3. Test jackpot REST endpoints
print(f"\n=== 3. Probing jackpot REST endpoints ===")
jackpot_endpoints = [
    "/mb/jackpot",
    "/mb/jackpots",
    "/mb/jackpot-campaign",
    "/mb/jackpot-claim",
    "/mb/jackpot/claim",
    "/mb/jackpot/win",
    "/mb/jackpot/history",
    "/mb/campaign/jackpot",
]

for ep in jackpot_endpoints:
    url = f"https://{TID}mgapi.asdgapicenterssdo.com{ep}"
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {JWT}", "template": "vn"}, timeout=10)
        if r.status_code == 200:
            print(f"  [GET 200] {ep}: {r.text[:150]}")
        elif r.status_code != 404:
            print(f"  [{r.status_code}] {ep}: {r.text[:80]}")
    except Exception as e:
        print(f"  [ERROR] {ep}: {str(e)[:50]}")

# Also try POST to claim
for ep in ["/mb/jackpot/claim", "/mb/jackpot-claim"]:
    url = f"https://{TID}mgapi.asdgapicenterssdo.com{ep}"
    try:
        r = requests.post(url, 
            headers={"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json"},
            json={"amount": 999999, "jackpot_id": test_id},
            timeout=10)
        if r.status_code != 404:
            print(f"  [POST {r.status_code}] {ep}: {r.text[:100]}")
    except Exception as e:
        pass

print(f"\n=== 4. WSS jackpot message capture + injection ===")

async def wss_jackpot():
    wss_url = f"wss://{TID}mgapi.asdgapicenterssdo.com/mb/ws?token={JWT}"
    
    try:
        async with websockets.connect(wss_url, ping_interval=20, close_timeout=5) as ws:
            print("[WSS CONNECTED]")
            
            # Capture a few jackpot messages to understand format
            print("\n[Capturing jackpot messages for 10s...]")
            start = time.time()
            jackpot_msgs = []
            
            while time.time() - start < 10:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=2)
                    data = json.loads(msg)
                    topic = data.get("topic_name", "?")
                    if topic == "JACKPOT_CAMPAIGN":
                        jackpot_msgs.append(data)
                        print(f"  [JACKPOT] {json.dumps(data)[:200]}")
                except asyncio.TimeoutError:
                    pass
            
            if jackpot_msgs:
                print(f"\nCaptured {len(jackpot_msgs)} jackpot messages")
                # Analyze message structure
                sample = jackpot_msgs[0]
                print(f"Sample structure: {list(sample.keys())}")
            
            # Try to send a message to WSS (injection test)
            print("\n[Testing WSS message injection...]")
            inject_payloads = [
                {"topic_name": "JACKPOT_WIN", "amount": 999999, "uid": PLAYER_ID},
                {"type": "jackpot_claim", "amount": 999999},
                {"action": "claim", "jackpot_id": test_id},
                json.dumps({"topic_name": "WALLET_UPDATE", "balance": 999999}),
            ]
            
            for payload in inject_payloads:
                try:
                    msg = json.dumps(payload) if isinstance(payload, dict) else payload
                    await ws.send(msg)
                    print(f"  [SENT] {msg[:100]}")
                    
                    # Check for response
                    try:
                        resp = await asyncio.wait_for(ws.recv(), timeout=2)
                        print(f"  [RESP] {resp[:150]}")
                    except asyncio.TimeoutError:
                        print(f"  [NO RESPONSE]")
                except Exception as e:
                    print(f"  [SEND ERROR] {str(e)[:50]}")
            
    except Exception as e:
        print(f"[WSS ERROR] {e}")

asyncio.run(wss_jackpot())

# 5. Check wallet after all operations
print(f"\n=== 5. Final wallet check ===")
r = requests.get(f"https://{TID}mgapi.asdgapicenterssdo.com/mb/wallet",
    headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
    timeout=10)
if r.ok:
    data = r.json().get("data", [{}])
    balance = data[0].get("balance", "?") if isinstance(data, list) else "?"
    print(f"Platform wallet: {balance} THB")

print("\n=== Done ===")
