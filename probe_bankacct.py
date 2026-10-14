#!/usr/bin/env python3
"""probe_bankacct.py — Register KBANK payment account via pbapi/mgapi.
   The withdrawal ISEs because mgapi payment-account table is empty.
   The player's KBANK (00b6996c) is in users.payment_accounts but not
   in mgapi's standalone payment-account table.
   Try: pbapi /pb/payment-accounts, PATCH /mb/users, /mb/bank-account GET
"""
import json, pathlib, requests, time

TID  = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
JWT  = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()

KBANK_ACCT_ID = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"
KBANK_CURRENCY_ID = "4a5dab48-21ab-4bc0-8d31-6d9c15ba2ee0"
WITHDRAW_TYPE_LOCAL = "a26ca1bd-b339-4df3-89ed-4d73ad8e3e93"
USER_ID = "eea830ab-b187-4f21-9b79-28e2773b2f6b"

def mhdrs():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "template": "vn", "correlationid": f"pba-{int(time.time())}",
            "languagecode": "th", "Origin": "https://m.vak88z2.com"}

def phdrs():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "domain": "m.vak88z2.com", "Origin": "https://m.vak88z2.com"}

def req(label, method, path, hdrs_fn=mhdrs, base=MGAPI, **kw):
    print(f"\n=== {label} ===")
    url = path if path.startswith("http") else f"{base}{path}"
    r = requests.request(method, url, headers=hdrs_fn(), timeout=15, **kw)
    try:
        body = r.json()
        print(f"  HTTP {r.status_code}: {json.dumps(body, ensure_ascii=False)[:700]}")
        return r.status_code, body
    except Exception:
        print(f"  HTTP {r.status_code}: {r.text[:300]}")
        return r.status_code, r.text

# ── 1. GET /mb/bank-account (discover schema from GET) ───────────────────────
req("1. GET /mb/bank-account", "GET", "/mb/bank-account")

# ── 2. Try PBAPI payment account endpoints ───────────────────────────────────
for ep in ["/pb/payment-accounts", "/pb/payment-account",
           "/pb/bank-accounts", "/pb/bank-account"]:
    r = requests.get(f"{PBAPI}{ep}?domain=m.vak88z2.com",
                     headers=phdrs(), timeout=8)
    if r.status_code != 404:
        print(f"\n  pbapi {ep}: HTTP {r.status_code} — {r.text[:300]}")
    else:
        print(f"  pbapi {ep}: 404")

# ── 3. PATCH /mb/users (update player bank account) ─────────────────────────
req("3. PATCH /mb/users", "PATCH", "/mb/users",
    json={"payment_accounts": [{"account_id": KBANK_ACCT_ID,
           "bank_currency_information_id": KBANK_CURRENCY_ID,
           "bank_code": "KBANK", "bank_no": "0543753327",
           "account_type": "BANK", "is_default": True}]})

# ── 4. POST /pb/payment-accounts (FeathersJS) ────────────────────────────────
for payload in [
    {"account_id": KBANK_ACCT_ID, "bank_code": "KBANK",
     "bank_no": "0543753327", "user_id": USER_ID},
    {"bank_currency_information_id": KBANK_CURRENCY_ID,
     "bank_no": "0543753327", "account_type": "BANK",
     "is_default": True, "domain": "m.vak88z2.com"},
]:
    r = requests.post(f"{PBAPI}/pb/payment-accounts",
                      headers=phdrs(), json=payload, timeout=8)
    if r.status_code != 404:
        print(f"\n  pb payment-accounts POST: HTTP {r.status_code} — {r.text[:300]}")
    else:
        print(f"  pb payment-accounts POST: 404")

# ── 5. After registration attempts, check payment-account ────────────────────
req("5. GET /mb/payment-account (check)", "GET", "/mb/payment-account")

# ── 6. Withdrawal attempt ────────────────────────────────────────────────────
req("6. POST /mb/queue-withdrawal", "POST", "/mb/queue-withdrawal",
    json={"payment_account_id": KBANK_ACCT_ID,
          "withdraw_amount": 100,
          "withdraw_type_id": WITHDRAW_TYPE_LOCAL})

print("\n=== DONE ===")
