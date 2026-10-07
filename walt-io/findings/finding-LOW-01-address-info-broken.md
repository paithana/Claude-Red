# [POSSIBLE-LOW] Wallet Address Info Endpoint Returns Incorrect Data for All Inputs

**Program:** Walt.io (HackerOne)  
**Researcher:** kzspy  
**Severity:** Low (if used for memo warnings — fund loss risk)  
**CVSS Score:** 3.1 (AV:N/AC:H/PR:N/UI:R/S:U/C:N/I:L/A:N)  
**CWE:** CWE-840 (Business Logic Errors)  
**Status:** [POSSIBLE] — public endpoint confirmed broken; impact depends on how app uses the response  

---

## Summary

`GET /api/v1/wallets/get_address_info/{address}` is a publicly accessible endpoint that always returns `{"isExchange":true,"exchangeName":null,"isMemoRequired":false}` regardless of the input address — including invalid addresses, addresses from other blockchains, and single-character strings. This indicates the endpoint is either broken or returns a hardcoded default.

## Steps to Reproduce

```bash
# Valid TON address
curl "https://walletbot.me/api/v1/wallets/get_address_info/EQD2NmD_lH5f5u1Kj3KfGyTvhZSX0Eg6qp2a5IQUKXxOG3f"
# → {"isExchange":true,"exchangeName":null,"isMemoRequired":false}

# ETH address (wrong blockchain)
curl "https://walletbot.me/api/v1/wallets/get_address_info/0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
# → {"isExchange":true,"exchangeName":null,"isMemoRequired":false}

# Completely invalid input
curl "https://walletbot.me/api/v1/wallets/get_address_info/INVALID_NOT_A_TON_ADDRESS"
# → {"isExchange":true,"exchangeName":null,"isMemoRequired":false}

# Single character
curl "https://walletbot.me/api/v1/wallets/get_address_info/x"
# → {"isExchange":true,"exchangeName":null,"isMemoRequired":false}
```

All responses identical. Only empty path returns 404.

## Impact

The intended purpose of this endpoint appears to be: identify whether a destination TON address belongs to a centralized exchange that requires a memo/comment tag (e.g., OKX, Binance, Bybit on TON network — all require memo tags to correctly credit deposits).

**If the app uses `isMemoRequired` to decide whether to show a memo input field:**
- `isMemoRequired: false` for ALL addresses means users sending to exchanges that require a memo are NOT prompted to enter one
- Result: transaction sent without memo → exchange credits to unknown user → **permanent fund loss**

**If the app uses `isExchange` to show an "exchange address" warning:**
- `isExchange: true` for ALL addresses means non-exchange personal wallets are incorrectly flagged

## Evidence

- Confirmed 2026-10-07 via passive recon (no auth required)
- Endpoint is listed in the app's OpenAPI client bundle (`openapi.71515bb967.js`)
- No auth required: endpoint returns data to unauthenticated requests

## Remediation

1. Fix the backend data source for exchange address classification
2. If the database is empty/unavailable, fail open with `isMemoRequired: false` but `isExchange: false` (rather than always true)
3. For exchanges known to require memo on TON (OKX, Binance, Bybit, KuCoin, Gate.io), ensure these are explicitly listed with `isMemoRequired: true`

---
*Testing conducted manually without authentication. Header `X-HackerOne-Research: kzspy` included on all requests.*
