#!/usr/bin/env python3
"""Probe all 791 unknown endpoints in lux-sitemap.json."""
import json, time, sys, os
from curl_cffi import requests as cffi_requests

TID = "af6efb584a3d317b5a11ab6209b88e1b"
HOSTS = {
    "pbapi":  f"https://{TID}pbapi.asdgapicenterssdo.com",
    "mgapi":  f"https://{TID}mgapi.asdgapicenterssdo.com",
    "bgapi":  f"https://{TID}bgapi.asdgapicenterssdo.com",
}
DOMAIN = "m.vak88z2.com"
SITEMAP = "/home/kzp/claude-red/lux-sitemap.json"
RESULTS = "/home/kzp/claude-red/data/json/probe_unknown_results.json"

def get_jwt():
    jwt_file = "/home/kzp/claude-red/.jwt.vak88z2"
    if os.path.exists(jwt_file):
        jwt = open(jwt_file).read().strip()
        if len(jwt) > 50:
            return jwt
    # Refresh
    r = cffi_requests.post(
        f"https://{TID}pbapi.asdgapicenterssdo.com/pb/authentication",
        json={"strategy":"local","username":"0811111111","password":"Pwned2026!"},
        impersonate="chrome124", timeout=15
    )
    token = r.json().get("accessToken","")
    if token:
        open(jwt_file,'w').write(token)
    return token

def probe(ep, jwt):
    host_key = ep.get("host")
    base = HOSTS.get(host_key)
    if not base:
        return None, None

    method = ep.get("method", "GET").upper()
    path = ep.get("path", "")
    auth = ep.get("auth", "")

    url = f"{base}{path}?domain={DOMAIN}"
    headers = {"template": "vn"}
    if auth in ("player_jwt", "player_jwt_bola") and jwt:
        headers["Authorization"] = f"Bearer {jwt}"

    try:
        r = cffi_requests.request(
            method, url, headers=headers,
            impersonate="chrome124", timeout=12
        )
        # Try to get response summary
        ct = r.headers.get("content-type","")
        body = ""
        if "json" in ct:
            try:
                j = r.json()
                if isinstance(j, list):
                    body = f"list[{len(j)}]"
                elif isinstance(j, dict):
                    body = f"dict:{list(j.keys())[:4]}"
            except:
                body = r.text[:80]
        else:
            body = r.text[:80]
        return r.status_code, body
    except Exception as e:
        return "err", str(e)[:60]

def main():
    with open(SITEMAP) as f:
        sitemap = json.load(f)

    unknowns = [ep for ep in sitemap["endpoints"] if ep.get("status") == "unknown"]
    print(f"Probing {len(unknowns)} unknown endpoints...", flush=True)

    jwt = get_jwt()
    print(f"JWT: {jwt[:20]}...", flush=True)

    results = {}
    errors = 0

    for i, ep in enumerate(unknowns):
        path = ep.get("path","")
        host = ep.get("host","")
        status, body = probe(ep, jwt)

        key = f"{host}:{path}"
        results[key] = {"status": status, "body": body}

        # Print progress
        marker = "!" if status == 200 else ("?" if status in (400,404) else ".")
        print(f"[{i+1:03d}/{len(unknowns)}] {marker} {status:>4} {host:6} {path[:60]}", flush=True)

        # Refresh JWT every 200 requests
        if (i+1) % 200 == 0:
            jwt = get_jwt()
            print(f"JWT refreshed", flush=True)

        # Small delay to avoid rate limiting
        time.sleep(0.05)

    # Save raw results
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, 'w') as f:
        json.dump(results, f, indent=2)

    # Update sitemap
    updated = 0
    for ep in sitemap["endpoints"]:
        if ep.get("status") == "unknown":
            key = f"{ep['host']}:{ep['path']}"
            if key in results:
                r = results[key]
                ep["status"] = r["status"]
                if ep.get("notes") == "extracted from bundle":
                    ep["notes"] = f"probed: {r['body'][:60]}"
                updated += 1

    sitemap["generated"] = time.strftime('%Y-%m-%dT%H:%M:%S+07:00')
    with open(SITEMAP, 'w') as f:
        json.dump(sitemap, f, indent=2, ensure_ascii=False)

    print(f"\nUpdated {updated} endpoints in sitemap")

    # Summary
    status_counts = {}
    for v in results.values():
        s = str(v["status"])
        status_counts[s] = status_counts.get(s,0) + 1
    print("Results:", status_counts)

    # Print 200s
    hits_200 = [(k,v) for k,v in results.items() if v["status"]==200]
    print(f"\n200 OK hits ({len(hits_200)}):")
    for k,v in sorted(hits_200):
        print(f"  {k}: {v['body'][:80]}")

if __name__ == "__main__":
    main()
