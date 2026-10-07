# Walt.io Recon — Target Surface

## Primary Surface
- Telegram Mini App (TWA): https://t.me/walt
- TON Space wallet (embedded)
- Recovery email flow

## Known API Patterns (to enumerate manually)
- Telegram WebApp API bridge (`window.Telegram.WebApp`)
- TON Connect protocol endpoints
- Balance / transaction history endpoints
- Withdrawal / transfer endpoints
- KYC / identity verification flow

## Attack Surface Priority
1. **TON wallet API** — authentication, authorization, transaction signing
2. **Cross-account access** — BOLA/IDOR on wallet IDs or user IDs
3. **Recovery flow** — password reset, email verification bypass
4. **Telegram auth handoff** — `initData` validation, HMAC bypass
5. **WebApp postMessage** — origin validation, data injection

## Telegram WebApp Auth Notes
- Telegram passes `initData` to TWA on launch (HMAC-SHA256 signed)
- Server MUST validate HMAC against bot token
- Common vuln: server accepts unsigned or self-signed initData
- Test: modify `user` field in initData, check if server rejects

## Recon Commands (manual — no AI scanning per policy)
```bash
# DNS enumeration
dig walt.io ANY
dig api.walt.io
dig app.walt.io

# Certificate transparency
curl -s "https://crt.sh/?q=%25.walt.io&output=json" | jq '.[].name_value' | sort -u

# Headers baseline (add H1 header)
curl -sI "https://app.walt.io" -H "X-HackerOne-Research: kzspy"
```
