import pathlib, re, subprocess

dirs = [
    pathlib.Path("/home/kzp/claude-red/nuxt/manage_vak88z_bundles"),
    pathlib.Path("/home/kzp/claude-red/nuxt/data/js_bundles"),
]

patterns = [
    (r'jwt.{0,20}secret|secret.{0,20}jwt|jwtSecret|JWT_SECRET|signing.?key', "JWT secret patterns"),
    (r'["\'][a-f0-9]{32,64}["\']', "32-64 char hex strings"),
    (r'Authorization|bearer|Bearer', "Auth header references"),
    (r'axiosCreate|axios\.create|interceptors|headers\[', "Axios config / interceptors"),
    (r'cf\s*[:=]\s*["\'][0-9a-f]{16,}', "cf claim values"),
    (r'PAPDIEAW|papdieaw|webhook.?key|hook.?key', "Webhook keys"),
    (r'process\.env\.|config\.["\']?secret|config\.["\']?key', "Env var refs"),
]

for d in dirs:
    if not d.exists():
        print(f"[!] Not found: {d}")
        continue
    files = list(d.glob("*.js"))
    print(f"\n=== {d.name}: {len(files)} JS files ===")
    for js in files:
        print(f"  {js.name} ({js.stat().st_size//1024}KB)")

    for pattern, label in patterns:
        hits = []
        for js in files:
            try:
                content = js.read_text(errors='ignore')
                for m in re.finditer(pattern, content, re.IGNORECASE):
                    start = max(0, m.start()-80)
                    end = min(len(content), m.end()+80)
                    ctx = content[start:end].replace('\n', ' ')
                    hits.append(f"  {js.name}: ...{ctx}...")
            except Exception as e:
                print(f"  [!] {js.name}: {e}")

        if hits:
            print(f"\n--- {label} ---")
            for h in hits[:8]:
                print(h[:250])
