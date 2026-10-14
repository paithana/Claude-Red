#!/usr/bin/env python3
"""probe_socketio_we88c.py — Socket.IO exploration on we88c pbapi.

   Try to find deposit notification channels via socket.io.
"""
import requests
import json

TID = "54ef7626cb381f4bab8be91f0cdbce47"
JWT = open(".jwt.we88c").read().strip()

PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"

HDR = {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json"}

# Try various socket.io polling endpoints
print("=== Socket.IO Polling Endpoints ===")
endpoints = [
    f"{PBAPI}/socket.io/?EIO=4&transport=polling",
    f"{PBAPI}/socket.io/?EIO=3&transport=polling",
    f"{MGAPI}/socket.io/?EIO=4&transport=polling",
    f"{MGAPI}/socket.io/?EIO=3&transport=polling",
    f"{PBAPI}/ws/",
    f"{MGAPI}/ws/",
    f"{PBAPI}/realtime/",
    f"{MGAPI}/realtime/",
]

for ep in endpoints:
    try:
        r = requests.get(ep, headers=HDR, timeout=10)
        print(f"\n{ep}")
        print(f"  HTTP {r.status_code}")
        if r.ok and r.text:
            print(f"  Response: {r.text[:300]}")
    except Exception as e:
        print(f"\n{ep}")
        print(f"  Error: {e}")

# Check if there are any real-time notification endpoints
print("\n\n=== Notification Endpoints ===")
notif_endpoints = [
    "/mb/notifications",
    "/mb/notification",
    "/mb/alerts",
    "/mb/messages",
    "/mb/inbox",
    "/mb/deposit-notifications",
    "/mb/transaction-history",
    "/mb/deposit-history",
]

for path in notif_endpoints:
    try:
        r = requests.get(f"{MGAPI}{path}", headers=HDR, timeout=10)
        if r.status_code != 404:
            print(f"\n{path}")
            print(f"  HTTP {r.status_code}")
            if r.ok:
                print(f"  Response: {r.text[:500]}")
    except Exception as e:
        print(f"\n{path}: Error {e}")

# Check pbapi endpoints
print("\n\n=== PBApi Notification Endpoints ===")
pb_endpoints = [
    "/pb/notifications",
    "/pb/messages",
    "/pb/inbox",
    "/pb/deposit-notifications",
    "/pb/deposit-transactions",
    "/pb/transaction-history",
]

for path in pb_endpoints:
    try:
        r = requests.get(f"{PBAPI}{path}", headers=HDR, params={"domain": "m.we88c.com", "$limit": 5}, timeout=10)
        if r.status_code != 404:
            print(f"\n{path}")
            print(f"  HTTP {r.status_code}")
            if r.ok:
                print(f"  Response: {r.text[:500]}")
    except Exception as e:
        print(f"\n{path}: Error {e}")

# Try to find deposit status endpoint
print("\n\n=== Deposit Status Endpoints ===")
dep_endpoints = [
    "/mb/deposit-status",
    "/mb/deposit-list",
    "/mb/deposits",
    "/mb/my-deposits",
    "/mb/player-deposits",
    "/mb/transaction-status",
    "/mb/slip-status",
]

for path in dep_endpoints:
    try:
        r = requests.get(f"{MGAPI}{path}", headers=HDR, timeout=10)
        if r.status_code != 404:
            print(f"\n{path}")
            print(f"  HTTP {r.status_code}")
            if r.ok:
                print(f"  Response: {r.text[:500]}")
    except Exception as e:
        print(f"\n{path}: Error {e}")

print("\n\n=== Done ===")
