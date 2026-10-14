import pathlib, re

js = pathlib.Path("/home/kzp/claude-red/nuxt/manage_vak88z_bundles/b39be13.js")
content = js.read_text(errors='ignore')

patterns = [
    # Find the actual bgapi URL used
    (r'ex_api_url|bgapi|bo_go|backoffice|api_url_go', "bgapi URL references"),
    # Find __NUXT__ runtime config
    (r'__NUXT__.*?config.*?\{[^}]{0,600}\}', "NUXT config"),
    (r'exApi|ex_api|asdgapicenter', "External API URLs"),
    # Any hardcoded tokens
    (r'"token"\s*:\s*"[a-zA-Z0-9._-]{40,}"', "Hardcoded token values"),
    (r'Bearer [a-zA-Z0-9._-]{40,}', "Bearer tokens"),
    # Firebase RTDB paths that might store BO tokens
    (r'rtdb|realtime|firebaseio|/bo_|/admin_|/users/', "Firebase RTDB paths"),
    # Any deposit/finance endpoints not in /api/
    (r'"/mb/|"/bo/|"/pb/', "Direct API paths"),
]

for pat, label in patterns:
    matches = list(re.finditer(pat, content, re.IGNORECASE | re.DOTALL))
    if matches:
        print(f"\n=== {label} ({len(matches)} hits) ===")
        seen = set()
        for m in matches[:6]:
            start = max(0, m.start()-60)
            end = min(len(content), m.end()+120)
            ctx = content[start:end].replace('\n', ' ')
            if ctx[:80] not in seen:
                seen.add(ctx[:80])
                print(f"  {ctx[:280]}")

# Also check 04d2a27.js (299KB - likely nuxt config bundle)
print("\n\n=== 04d2a27.js: NUXT runtime config ===")
cfg_js = pathlib.Path("/home/kzp/claude-red/nuxt/manage_vak88z_bundles/04d2a27.js")
cfg = cfg_js.read_text(errors='ignore')
for pat in [r'asdgapicenter|bgapi|bo_go|ex_api|__NUXT__']:
    for m in re.finditer(pat, cfg, re.IGNORECASE):
        start = max(0, m.start()-80)
        end = min(len(cfg), m.end()+200)
        ctx = cfg[start:end].replace('\n', ' ')
        print(f"  {ctx[:350]}")
        break  # one hit per pattern
