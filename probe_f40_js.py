#!/usr/bin/env python3 -I
"""F40 — fetch game JS and extract wallet endpoints."""
import requests, re

GAME_URL = "https://wbgame.royalflush888.com/cc3x5/?ssoKey=9e2b6d2ab2afdbc994a032bb7bf5887845b4fff3&lang=th-TH&apiId=1701&be=moc.888hsulflayor.ipabewbw&domain_gs=888hsulflayor&domain_platform=moc.888hsulflayor.mroftalp-tolsbw&gameID=641&gs=moc.888hsulflayor.df-tolsbw&legalLang=true&skin=0"
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

r = requests.get(GAME_URL, headers=HDRS, timeout=10)
print(f"[html] {r.status_code} len={len(r.text)}")

js_urls = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', r.text)
print(f"[html] JS files: {js_urls}")

from urllib.parse import urljoin
for js_url in js_urls:
    if not js_url.startswith("http"):
        js_url = urljoin(GAME_URL, js_url)
    print(f"\n[js] {js_url}")
    try:
        jr = requests.get(js_url, headers=HDRS, timeout=15)
        jt = jr.text
        print(f"[js] len={len(jt)}")

        # Search for any URL path containing credit/wallet/balance/debit/bet/win
        hits = re.findall(r'["\`]((?:https?://[^"\`<>]{0,100}|/[a-zA-Z0-9/_-]{2,80})(?:credit|wallet|debit|balance|bet|win|callback)[^"\`<>]{0,60})["\`]', jt, re.I)
        if hits:
            print("[js] HITS:")
            for h in sorted(set(hits)):
                print(f"  {h}")
        else:
            print("[js] no wallet path hits")

        # Also search for wbwebapi or royalflush888
        domain_hits = re.findall(r'["\`]((?:https?://)?[a-zA-Z0-9._-]*royalflush888[^"\`<>]{0,80})["\`]', jt)
        if domain_hits:
            print("[js] royalflush888 refs:")
            for h in sorted(set(domain_hits)):
                print(f"  {h}")

        # Look for API path patterns like /api/... or /v1/...
        api_paths = re.findall(r'["\`](/(?:api|v[0-9]|game|wallet|seamless)/[a-zA-Z0-9/_-]{2,60})["\`]', jt)
        if api_paths:
            print("[js] API paths:")
            for h in sorted(set(api_paths)):
                print(f"  {h}")

    except Exception as e:
        print(f"[js] ERR: {e}")
