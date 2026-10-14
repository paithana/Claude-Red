#!/usr/bin/env python3 -I
"""F40 path probe — check wallet domains + credit paths."""
import requests

domains = [
    "wbwebapi.royalflush888.com",
    "wbslots-platform.royalflush888.com",
    "wbslots-fd.royalflush888.com",
]
paths = [
    "/credit", "/api/credit", "/gameApi/wallet/credit", "/wallet/credit",
    "/api/wallet/credit", "/api/v1/wallet/credit", "/callback/credit",
    "/seamless/credit", "/seamless/wallet/credit",
    "/healthz", "/",
]

for domain in domains:
    print(f"\n=== {domain} ===")
    for path in paths:
        url = f"https://{domain}{path}"
        try:
            r = requests.get(url, timeout=5)
            print(f"  GET {path} → {r.status_code} {r.text[:60]!r}")
        except Exception as e:
            print(f"  GET {path} → ERR {str(e)[:60]}")
