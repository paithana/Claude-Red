#!/usr/bin/env python3
"""probe_firebase_rtdb_wss.py — Trace Firebase RTDB WebSocket for we88c.

   Firebase RTDB uses WebSocket for real-time sync.
   Endpoint format: wss://<project>.firebaseio.com/.ws?v=5&ns=<namespace>
"""
import asyncio
import json
import websockets
import requests
import base64

# Firebase config from we88c
FIREBASE_API_KEY = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"

# Common Firebase project names to try
PROJECTS = [
    "we88c",
    "we88z",
    "we88c-default-rtdb",
    "we88z-default-rtdb",
    "z-seamless",
    "z-seamless-default-rtdb",
    "luxino",
    "luxino-pub",
    "i-gamingplatform",
]

# Try to get Firebase config from the we88c site
print("=== Fetching Firebase config from we88c ===")
try:
    r = requests.get("https://m.we88c.com/", timeout=15)
    if "firebaseConfig" in r.text:
        # Extract config
        import re
        match = re.search(r'firebaseConfig\s*[=:]\s*(\{[^}]+\})', r.text)
        if match:
            print(f"Found firebaseConfig: {match.group(1)[:200]}")

        # Also look for databaseURL
        match = re.search(r'databaseURL["\']?\s*[=:]\s*["\']([^"\']+)', r.text)
        if match:
            print(f"Found databaseURL: {match.group(1)}")

        # Look for projectId
        match = re.search(r'projectId["\']?\s*[=:]\s*["\']([^"\']+)', r.text)
        if match:
            print(f"Found projectId: {match.group(1)}")
            PROJECTS.insert(0, match.group(1))
except Exception as e:
    print(f"Error fetching site: {e}")

# Try to discover RTDB endpoint via REST API
print("\n=== Probing Firebase RTDB REST endpoints ===")
for proj in PROJECTS[:5]:
    urls = [
        f"https://{proj}.firebaseio.com/.json",
        f"https://{proj}-default-rtdb.firebaseio.com/.json",
        f"https://{proj}.firebasedatabase.app/.json",
    ]
    for url in urls:
        try:
            r = requests.get(url, params={"shallow": "true", "auth": ""}, timeout=5)
            print(f"\n{url}")
            print(f"  HTTP {r.status_code}: {r.text[:200]}")
            if r.status_code == 200:
                print(f"  [!] ACCESSIBLE")
        except Exception as e:
            pass  # Timeout = doesn't exist

# Try WebSocket connection to known RTDB endpoints
print("\n\n=== Testing Firebase RTDB WebSocket ===")

async def test_rtdb_wss(project):
    urls = [
        f"wss://{project}.firebaseio.com/.ws?v=5&ns={project}",
        f"wss://{project}-default-rtdb.firebaseio.com/.ws?v=5&ns={project}",
        f"wss://s-usc1c-nss-2061.firebaseio.com/.ws?v=5&ns={project}",
    ]

    for url in urls:
        try:
            async with websockets.connect(url, close_timeout=3) as ws:
                print(f"\n[CONNECTED] {url}")

                # Firebase RTDB protocol: send initial handshake
                # Format: {"t":"d","d":{"r":1,"a":"s","b":{"c":{"sdk.js.8-10-0":1}}}}
                handshake = {
                    "t": "d",
                    "d": {
                        "r": 1,
                        "a": "s",
                        "b": {"c": {"sdk.js.8-10-0": 1}}
                    }
                }
                await ws.send(json.dumps(handshake))

                # Listen for response
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    print(f"  Recv: {msg[:300]}")

                    # Try to subscribe to paths
                    subscribe = {
                        "t": "d",
                        "d": {
                            "r": 2,
                            "a": "q",  # query
                            "b": {
                                "p": "/",  # path
                                "h": ""
                            }
                        }
                    }
                    await ws.send(json.dumps(subscribe))

                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    print(f"  Recv: {msg[:300]}")

                except asyncio.TimeoutError:
                    print(f"  [TIMEOUT]")

        except Exception as e:
            pass  # Connection failed = wrong project

for proj in PROJECTS[:5]:
    asyncio.run(test_rtdb_wss(proj))

# Also try the discovered GCS service account project
print("\n\n=== Trying z-seamless project ===")
asyncio.run(test_rtdb_wss("z-seamless"))

print("\n\n=== Done ===")
