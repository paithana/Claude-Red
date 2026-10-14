import pathlib, re

js = pathlib.Path("/home/kzp/claude-red/nuxt/manage_vak88z_bundles/b39be13.js")
content = js.read_text(errors='ignore')

# Find the nuxtjs/auth strategy config — look for the endpoints object
patterns = [
    r'login\s*[:{]\s*\{[^}]{0,200}url[^}]{0,200}\}',
    r'"url"\s*:\s*"[^"]*(?:auth|login|sign)[^"]*"',
    r'endpoints\s*[:{]\s*\{[^}]{0,400}\}',
    r'loginWith|logout|user.*url|login.*url',
    r'/bo/authentication|/account/login|/api/auth',
    r'exApi|ex_api|bgapi|bgApi',
]

for pat in patterns:
    matches = list(re.finditer(pat, content, re.IGNORECASE | re.DOTALL))
    if matches:
        print(f"\n=== {pat} ===")
        for m in matches[:5]:
            start = max(0, m.start()-100)
            end = min(len(content), m.end()+100)
            ctx = content[start:end].replace('\n', ' ')
            print(f"  {ctx[:350]}")
