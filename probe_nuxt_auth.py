import subprocess, json, pathlib, base64

BO_NUXT = "https://manage.vak88z2.com"

def c(args, timeout=12):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip()

def run(label, args, timeout=12):
    print(f"\n=== {label} ===")
    out, err = c(args, timeout)
    combined = (out or err)[:800]
    print(combined)
    return out

# 1. @nuxtjs/auth POST /api/auth/login (standard path)
run("1. POST /api/auth/login (admin)", [
    "curl", "-s", "--max-time", "10", "-X", "POST",
    BO_NUXT + "/api/auth/login",
    "-H", "Content-Type: application/json",
    "-H", "Origin: https://manage.vak88z2.com",
    "-H", "Referer: https://manage.vak88z2.com/",
    "-d", '{"username":"admin","password":"Aa112233"}'
])

run("2. POST /api/auth/login (Vak88z)", [
    "curl", "-s", "--max-time", "10", "-X", "POST",
    BO_NUXT + "/api/auth/login",
    "-H", "Content-Type: application/json",
    "-H", "Origin: https://manage.vak88z2.com",
    "-d", '{"username":"Vak88z","password":"admin"}'
])

# 3. GET /api/auth/user (check if returns something)
run("3. GET /api/auth/user", [
    "curl", "-s", "--max-time", "8", BO_NUXT + "/api/auth/user",
    "-H", "Origin: https://manage.vak88z2.com"
])

# 4. Try alternate paths for Nuxt auth
for path in ["/api/login", "/api/auth", "/api/bo/authentication",
             "/auth/login", "/api/auth/bo", "/api/v1/auth/login"]:
    out, _ = c([
        "curl", "-s", "--max-time", "6", "-X", "POST",
        BO_NUXT + path,
        "-H", "Content-Type: application/json",
        "-d", '{"username":"admin","password":"Aa112233"}'
    ])
    if out and "html" not in out.lower() and len(out) > 2:
        print(f"\n  {path}: {out[:200]}")
    else:
        print(f"  {path}: {'HTML/empty' if out else 'no response'}")

# 5. POST /api/auth/login with admin object body (user hint from handoff)
run("5. POST /api/auth/login (admin object body)", [
    "curl", "-s", "--max-time", "10", "-X", "POST",
    BO_NUXT + "/api/auth/login",
    "-H", "Content-Type: application/json",
    "-H", "Origin: https://manage.vak88z2.com",
    "-d", '{"id":"5958356c-eb4e-4e07-a155-83e4382e3532","username":"admin","firstname":"admin","lastname":"admin"}'
])

# 6. Nuxt server API: _nuxt/static or server routes
run("6. GET /_nuxt/server/auth", [
    "curl", "-s", "--max-time", "6", BO_NUXT + "/_nuxt/server/auth"
])
