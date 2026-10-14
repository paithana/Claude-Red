#!/usr/bin/env python3
"""probe_apk_smsactivity.py — Find how ReadSmsScb/ReadSmsKbank is called and what auth is used."""
import pathlib, re

JADX = pathlib.Path("/home/kzp/claude-red/nuxt/data/apk/jadx_out_all/LuxSms-v3/sources")

# ── 1. Read SmsActivity ───────────────────────────────────────────────────────
print("=== SmsActivity.java (first 300 lines) ===")
for f in JADX.rglob("SmsActivity.java"):
    content = f.read_text(errors='ignore')
    # Find ReadSms calls
    for kw in ["ReadSmsScb", "ReadSmsKbank", "ReadSmsKTB", "readSms", "webhook"]:
        idx = content.lower().find(kw.lower())
        if idx >= 0:
            print(f"\n  [{kw}]:")
            print(content[max(0,idx-300):idx+500])

# ── 2. Find any API provider / helper that sets auth ─────────────────────────
print("\n=== ApiProvider / ApiHelper / NetworkHelper ===")
for fname in ["ApiProvider.java", "ApiHelper.java", "NetworkHelper.java",
              "SmsViewModel.java", "LoginViewModel.java", "ListSmsViewModel.java",
              "PrefUtil.java", "AppPreference.java"]:
    for f in JADX.rglob(fname):
        content = f.read_text(errors='ignore')
        print(f"\n  {f.name} ({len(content)} bytes):")
        # Look for PAPDIEAW or auth headers
        for kw in ["PAPDIEAW", "papdieaw", "Authorization", "addHeader", "token", "Bearer",
                   "username", "password", "login", "auth", "C2", "webhook", "baseUrl",
                   "ReadSmsScb", "ReadSmsKbank"]:
            idx = content.lower().find(kw.lower())
            if idx >= 0:
                print(f"    [{kw}]: {content[max(0,idx-30):idx+200]}")

# ── 3. Check main activity / Application class for baseUrl ───────────────────
print("\n=== MainActivity / Application / App class ===")
for fname in ["MainActivity.java", "App.java", "Application.java", "MyApplication.java"]:
    for f in JADX.rglob(fname):
        content = f.read_text(errors='ignore')
        print(f"\n  {f.name}:")
        for kw in ["baseUrl", "asdgapi", "webhook", "PAPDIEAW", "addHeader"]:
            idx = content.lower().find(kw.lower())
            if idx >= 0:
                print(f"    [{kw}]: {content[max(0,idx-50):idx+300]}")

# ── 4. Search all files for asdgapi or mgapi URL ─────────────────────────────
print("\n=== Files containing mgapi/asdgapi ===")
for f in JADX.rglob("*.java"):
    content = f.read_text(errors='ignore')
    if "asdgapi" in content.lower() or "mgapi" in content.lower():
        print(f"\n  {f.name}:")
        for kw in ["asdgapi", "mgapi"]:
            idx = content.lower().find(kw.lower())
            if idx >= 0:
                print(f"    {content[max(0,idx-100):idx+300]}")
