#!/usr/bin/env python3
"""probe_search_bo_js.py — Grep cached BO JS bundles for JWT secret / auth config.

   Target: nuxt/manage_vak88z_bundles/b39be13.js (3.1MB minified)
   Also check: tmp/bo_js/ cached chunks from earlier download
   Looking for: jwtSecret, SECRET, authKey, authentication config
"""
import pathlib, re, json

PATHS = [
    pathlib.Path("/home/kzp/.claude/jobs/546de6d5/tmp/bo_js"),
    pathlib.Path("/home/kzp/claude-red/nuxt/manage_vak88z_bundles"),
]

PATTERNS = [
    # JWT secret patterns
    r'(?:jwtSecret|jwt_secret|JWT_SECRET|secret)["\s]*[:=]["\s]*["\']([^"\']{8,})["\']',
    r'(?:authSecret|auth_secret|AUTH_SECRET)["\s]*[:=]["\s]*["\']([^"\']{8,})["\']',
    r'(?:privateKey|private_key)["\s]*[:=]["\s]*["\']([^"\']{16,})["\']',
    # Authentication config
    r'authentication["\s]*[:=]["\s]*\{([^}]{20,})\}',
    r'(?:secret|key)["\s]*:["\s]*["\']([a-f0-9]{32,})["\']',
    # FeathersJS auth config
    r'localStrategy[^{]*\{([^}]{20,})\}',
    r'entity["\s]*:["\s]*["\']([^"\']+)["\'][^}]*secret["\s]*:["\s]*["\']([^"\']{8,})["\']',
    # Token signing
    r'sign\([^,]+,["\s]*["\']([^"\']{8,})["\']',
    r'verify\([^,]+,["\s]*["\']([^"\']{8,})["\']',
    # Hard-coded secrets (hex or base64)
    r'"([a-f0-9]{64})"',   # 256-bit hex
    r'"([a-f0-9]{32})"',   # 128-bit hex
    # API keys
    r'(?:apiKey|api_key|API_KEY)["\s]*[:=]["\s]*["\']([^"\']{20,})["\']',
    # Environment variable leaks
    r'process\.env\.([A-Z_]+SECRET[A-Z_]*)',
    r'process\.env\.([A-Z_]+KEY[A-Z_]*)',
    r'process\.env\.(JWT[A-Z_]*)',
    # Nuxt config
    r'runtimeConfig[^{]*\{([^}]{50,})\}',
    r'publicRuntimeConfig[^{]*\{([^}]{50,})\}',
]

def search_file(fpath):
    try:
        content = fpath.read_text(errors="replace")
    except Exception as e:
        print(f"  ERROR reading {fpath}: {e}")
        return

    size_kb = fpath.stat().st_size // 1024
    print(f"\n--- {fpath.name} ({size_kb}KB) ---")

    found = {}
    for pat in PATTERNS:
        matches = re.findall(pat, content, re.IGNORECASE)
        if matches:
            found[pat[:50]] = matches[:5]

    if found:
        for pat, matches in found.items():
            print(f"  PATTERN: {pat[:60]}")
            for m in matches:
                if isinstance(m, tuple):
                    m = " | ".join(m)
                if len(m) > 200:
                    m = m[:200] + "..."
                print(f"    >> {m}")
    else:
        print(f"  (no matches)")

    # Also do specific targeted string searches
    targets = [
        "jwtSecret", "jwt_secret", "JWT_SECRET",
        "authentication", "localStrategy", "secret",
        "PAPDIEAW", "webhook_key", "webhook-key",
        "process.env",
    ]
    for t in targets:
        idx = content.find(t)
        if idx >= 0:
            snippet = content[max(0, idx-30):idx+100]
            snippet = snippet.replace("\n", " ")
            print(f"  STRING [{t}]: ...{snippet}...")


for search_dir in PATHS:
    if not search_dir.exists():
        print(f"DIR NOT FOUND: {search_dir}")
        continue
    print(f"\n=== Searching {search_dir} ===")
    js_files = list(search_dir.glob("*.js"))
    print(f"  {len(js_files)} JS files found")
    for fpath in sorted(js_files, key=lambda x: x.stat().st_size, reverse=True)[:5]:
        search_file(fpath)

print("\n=== DONE ===")
