#!/usr/bin/env python3
"""pull_vak_config.py — Pull all accessible config from vak88z2 via BOLA.

Saves each endpoint response to data/json/vak88z2_extract/<name>.json
"""
import json, pathlib, requests, sys, time

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
BGAPI = f"https://{TID}bgapi.asdgapicenterssdo.com"
DOM   = "m.vak88z2.com"

JWT_FILE = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2")
JWT      = JWT_FILE.read_text().strip()

OUT_DIR = pathlib.Path("/home/kzp/claude-red/data/json/vak88z2_extract")
OUT_DIR.mkdir(parents=True, exist_ok=True)

HDR_MB = {"Authorization": f"Bearer {JWT}", "template": "th", "Content-Type": "application/json"}
HDR_BO = {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json"}
HDR_PB = {"Content-Type": "application/json"}

s = requests.Session()

def get(url, headers, label, params=None):
    try:
        r = s.get(url, headers=headers, params=params, timeout=15)
        status = r.status_code
        try:
            data = r.json()
        except Exception:
            data = r.text[:2000]
        return status, data
    except Exception as e:
        return 0, str(e)

def save(name, data):
    p = OUT_DIR / f"{name}.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return p

def count(data):
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for k in ("data","items","list","result","results"):
            if k in data and isinstance(data[k], list):
                return len(data[k])
    return "?"

results = []

# ── bgapi BOLA endpoints ─────────────────────────────────────────────────────
BO_ENDPOINTS = [
    ("general_config",          f"{BGAPI}/bo/info/general-config",              HDR_BO, {"domain": DOM}),
    ("admins",                  f"{BGAPI}/bo/info/admin",                        HDR_BO, {"domain": DOM}),
    ("assign_settlement",       f"{BGAPI}/bo/info/assign-settlement-account",    HDR_BO, {"domain": DOM}),
    ("settlement_account",      f"{BGAPI}/bo/info/settlement-account",           HDR_BO, {"domain": DOM}),
    ("all_settlement_balance",  f"{BGAPI}/bo/info/all-settlement-balance",       HDR_BO, {"domain": DOM}),
    ("bank_deposit",            f"{BGAPI}/bo/info/bank-deposit",                 HDR_BO, {"domain": DOM}),
    ("payment_bank_account",    f"{BGAPI}/bo/info/payment-bank-account",         HDR_BO, {"domain": DOM}),
    ("provider",                f"{BGAPI}/bo/info/provider",                     HDR_BO, {"domain": DOM}),
    ("game",                    f"{BGAPI}/bo/info/game",                         HDR_BO, {"domain": DOM}),
    ("game_category",           f"{BGAPI}/bo/info/game-category",                HDR_BO, {"domain": DOM}),
    ("promotion",               f"{BGAPI}/bo/info/promotion",                    HDR_BO, {"domain": DOM}),
    ("promotion_history",       f"{BGAPI}/bo/info/promotion-history",            HDR_BO, {"domain": DOM}),
    ("bank",                    f"{BGAPI}/bo/info/bank",                         HDR_BO, {"domain": DOM}),
    ("blacklist_user",          f"{BGAPI}/bo/info/blacklist-user",               HDR_BO, {"domain": DOM}),
    ("notification_count",      f"{BGAPI}/bo/notification-count",                HDR_BO, {"domain": DOM}),
    ("permission",              f"{BGAPI}/bo/info/permission",                   HDR_BO, {"domain": DOM}),
    ("role",                    f"{BGAPI}/bo/info/role",                         HDR_BO, {"domain": DOM}),
    ("upline",                  f"{BGAPI}/bo/info/upline",                       HDR_BO, {"domain": DOM}),
    ("affiliate",               f"{BGAPI}/bo/info/affiliate",                    HDR_BO, {"domain": DOM}),
    ("affiliate_member",        f"{BGAPI}/bo/info/affiliate-member",             HDR_BO, {"domain": DOM}),
    ("specific_domain_config",  f"{BGAPI}/bo/info/specific-domain-config",       HDR_BO, {"domain": DOM}),
    ("payment_type_bo",         f"{BGAPI}/bo/info/payment-type",                 HDR_BO, {"domain": DOM}),
    ("gateway_config",          f"{BGAPI}/bo/info/gateway-config",               HDR_BO, {"domain": DOM}),
    ("sms_config",              f"{BGAPI}/bo/info/sms-config",                   HDR_BO, {"domain": DOM}),
    ("withdraw_config",         f"{BGAPI}/bo/info/withdraw-config",              HDR_BO, {"domain": DOM}),
    ("auto_withdraw",           f"{BGAPI}/bo/info/auto-withdraw",                HDR_BO, {"domain": DOM}),
    ("cashback_config",         f"{BGAPI}/bo/info/cashback-config",              HDR_BO, {"domain": DOM}),
    ("rebate_config",           f"{BGAPI}/bo/info/rebate-config",                HDR_BO, {"domain": DOM}),
    ("line_config",             f"{BGAPI}/bo/info/line-config",                  HDR_BO, {"domain": DOM}),
    ("domain_config",           f"{BGAPI}/bo/info/domain-config",                HDR_BO, {"domain": DOM}),
    ("member_level",            f"{BGAPI}/bo/info/member-level",                 HDR_BO, {"domain": DOM}),
    ("point_config",            f"{BGAPI}/bo/info/point-config",                 HDR_BO, {"domain": DOM}),
    ("slip_deposit_task",       f"{BGAPI}/bo/slip-deposit-task",                 HDR_BO, {"domain": DOM, "status": "waiting", "skip": 0, "limit": 50}),
    ("withdraw_task",           f"{BGAPI}/bo/withdraw-task",                     HDR_BO, {"domain": DOM, "status": "waiting", "skip": 0, "limit": 50}),
    ("member_info",             f"{BGAPI}/bo/info/member",                       HDR_BO, {"domain": DOM, "skip": 0, "limit": 20}),
    ("transaction_deposit",     f"{BGAPI}/bo/transaction-deposit",               HDR_BO, {"domain": DOM, "skip": 0, "limit": 20}),
    ("transaction_withdraw",    f"{BGAPI}/bo/transaction-withdraw",              HDR_BO, {"domain": DOM, "skip": 0, "limit": 20}),
    ("info_admin",              f"{BGAPI}/bo/info/admin",                        HDR_BO, {"domain": DOM, "skip": 0, "limit": 200}),
]

# ── mgapi member endpoints ───────────────────────────────────────────────────
MB_ENDPOINTS = [
    ("mb_wallet",          f"{MGAPI}/mb/wallet",                 HDR_MB, None),
    ("mb_users",           f"{MGAPI}/mb/users",                  HDR_MB, None),
    ("mb_payment_type",    f"{MGAPI}/mb/payment-type",           HDR_MB, {"include": "true"}),
    ("mb_promotion",       f"{MGAPI}/mb/promotion",              HDR_MB, {"domain": DOM}),
    ("mb_cashback",        f"{MGAPI}/mb/cashback",               HDR_MB, None),
    ("mb_rebate",          f"{MGAPI}/mb/rebate",                 HDR_MB, None),
    ("mb_point",           f"{MGAPI}/mb/point",                  HDR_MB, None),
    ("mb_bank",            f"{MGAPI}/mb/bank",                   HDR_MB, None),
    ("mb_game",            f"{MGAPI}/mb/game",                   HDR_MB, None),
    ("mb_provider",        f"{MGAPI}/mb/provider",               HDR_MB, None),
    ("mb_notification",    f"{MGAPI}/mb/notification",           HDR_MB, None),
    ("mb_deposit_list",    f"{MGAPI}/mb/deposit-transaction",    HDR_MB, {"skip": 0, "limit": 20}),
    ("mb_withdraw_list",   f"{MGAPI}/mb/withdraw-transaction",   HDR_MB, {"skip": 0, "limit": 20}),
    ("mb_payment_slip",    f"{MGAPI}/mb/payment-slip-information", HDR_MB, None),
    ("mb_affiliate",       f"{MGAPI}/mb/affiliate",              HDR_MB, None),
    ("mb_member_level",    f"{MGAPI}/mb/member-level",           HDR_MB, None),
]

# ── pbapi public endpoints ───────────────────────────────────────────────────
PB_ENDPOINTS = [
    ("pb_custom_function",   f"{PBAPI}/pb/custom-function",           HDR_PB, {"page_show_list": "index"}),
    ("pb_payment_type",      f"{PBAPI}/pb/payment-type",              HDR_PB, {"domain": DOM}),
    ("pb_notification_modal",f"{PBAPI}/pb/notification-modal",        HDR_PB, {"domain": DOM}),
    ("pb_domain_config",     f"{PBAPI}/pb/domain-page-config/deposit",HDR_PB, {"domain": DOM}),
    ("pb_language",          f"{PBAPI}/pb/language",                  HDR_PB, {"domain": DOM}),
    ("pb_currency",          f"{PBAPI}/pb/currency",                  HDR_PB, {"domain": DOM}),
    ("pb_latest_win",        f"{PBAPI}/pb/latest-win",                HDR_PB, {"domain": DOM}),
    ("pb_enable_feature",    f"{PBAPI}/pb/enable-feature",            HDR_PB, {"domain": DOM}),
]

print(f"[pull_vak_config] JWT={JWT[:20]}...  out={OUT_DIR}")
print(f"{'─'*70}")

all_endpoints = (
    [("BO", *e) for e in BO_ENDPOINTS] +
    [("MB", *e) for e in MB_ENDPOINTS] +
    [("PB", *e) for e in PB_ENDPOINTS]
)

ok_count = 0
fail_count = 0

for prefix, name, url, hdrs, params in all_endpoints:
    status, data = get(url, hdrs, name, params)
    n = count(data)
    tag = "✓" if status == 200 else "✗"
    note = f"n={n}" if status == 200 else f"HTTP {status}"
    print(f"  {tag} [{prefix}] {name:<35s} {note}")
    if status == 200:
        save(name, data)
        ok_count += 1
    else:
        fail_count += 1
    time.sleep(0.1)

print(f"\n{'─'*70}")
print(f"[DONE] {ok_count} OK / {fail_count} failed → {OUT_DIR}")

# Print key values from general_config
gc_path = OUT_DIR / "general_config.json"
if gc_path.exists():
    gc = json.loads(gc_path.read_text())
    print(f"\n── General Config highlights ──────────────────────────────────────")
    for item in (gc if isinstance(gc, list) else gc.get("data", [gc])):
        for k in ["bot_webhook_external_url", "auto_withdraw_status", "two_factor_authen_status",
                  "auto_slip_status", "notification_line_status", "auto_cashback_status"]:
            v = item.get(k) if isinstance(item, dict) else None
            if v is not None:
                print(f"  {k}: {v}")

# Print settlement balances
sb_path = OUT_DIR / "all_settlement_balance.json"
if sb_path.exists():
    sb = json.loads(sb_path.read_text())
    items = sb if isinstance(sb, list) else sb.get("data", [])
    if items:
        print(f"\n── Settlement Balances ({len(items)} accounts) ──────────────────────")
        total = 0
        for a in items:
            bal = a.get("balance", a.get("amount", 0))
            try:
                total += float(str(bal).replace(",",""))
            except:
                pass
            bank = a.get("bank_code", a.get("bank","?"))
            acct = a.get("bank_no", a.get("account_no","?"))
            print(f"  {bank} {acct}: {bal} THB")
        print(f"  TOTAL: {total:,.2f} THB")

# Print notification/task queue
nq_path = OUT_DIR / "notification_count.json"
if nq_path.exists():
    nq = json.loads(nq_path.read_text())
    print(f"\n── Notification/Task Queue ─────────────────────────────────────────")
    print(f"  {json.dumps(nq, ensure_ascii=False)}")
