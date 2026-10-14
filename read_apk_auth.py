#!/usr/bin/env python3
"""read_apk_auth — examine service account login files in jadx output"""
import pathlib, re

jadx = pathlib.Path("/home/kzp/claude-red/nuxt/data/apk/jadx_out_all")

# Read key auth-related files
targets = [
    "AuthenticateRequest.java", "LoginRequest.java",
    "ListItemSmsRequest.java", "ListApi.java",
    "SmsService.java", "ApiService.java", "RetrofitClient.java",
    "MainActivity.java", "SmsReceiver.java", "C2Service.java",
    "ApiHelper.java", "NetworkHelper.java", "Constants.java",
    "Config.java", "AppConfig.java", "BuildConfig.java",
]

for fname in targets:
    hits = list(jadx.rglob(fname))
    for f in hits[:1]:
        content = f.read_text(errors='ignore')
        print(f"\n{'='*60}")
        print(f"FILE: {f.relative_to(jadx)}")
        print(f"SIZE: {len(content)} bytes")
        print(f"{'='*60}")
        print(content[:3000])

# Also: find anything with hardcoded URLs or credentials
print("\n\n=== Hardcoded base URLs ===")
for f in jadx.rglob("*.java"):
    try:
        c = f.read_text(errors='ignore')
        for m in re.finditer(r'https?://[^\s"\']{15,}', c):
            url = m.group()
            if any(x in url for x in ['asdgapi', 'staging-bot', 'bot-auto', 'ztechdev', 'luxino', 'webhook']):
                start = max(0, m.start()-60)
                end = min(len(c), m.end()+60)
                ctx = c[start:end].replace('\n', ' ')
                print(f"  {f.name}: {ctx[:200]}")
    except:
        pass

# Find hardcoded username/password pairs
print("\n\n=== Hardcoded credentials ===")
cred_pat = re.compile(r'(?:username|user|login|account)\s*[=:]\s*["\']([^"\']{3,30})["\']', re.IGNORECASE)
pwd_pat  = re.compile(r'(?:password|passwd|pwd|secret|key)\s*[=:]\s*["\']([^"\']{4,64})["\']', re.IGNORECASE)
for f in jadx.rglob("*.java"):
    try:
        c = f.read_text(errors='ignore')
        creds = cred_pat.findall(c)
        pwds  = pwd_pat.findall(c)
        if creds or pwds:
            # Filter out obvious false positives
            real_creds = [x for x in creds if not any(p in x.lower() for p in ['view', 'text', 'field', 'hint', 'label', 'button'])]
            real_pwds  = [x for x in pwds  if len(x) > 6 and not any(p in x.lower() for p in ['enter', 'field', 'hint', 'label', 'text'])]
            if real_creds or real_pwds:
                print(f"\n  {f.name}:")
                for c2 in real_creds[:3]: print(f"    user: {c2}")
                for p in real_pwds[:3]:   print(f"    pass: {p}")
    except:
        pass
