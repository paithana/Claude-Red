# [INFO] Historical Exchange Rate Endpoint Publicly Accessible

**Program:** Walt.io (HackerOne)  
**Researcher:** kzspy  
**Severity:** Informational  
**Status:** [INFO] — no direct exploitable impact; potential privacy concern
**CWE:** CWE-200 (Information Exposure)

---

## Summary

`GET /api/v1/exchange_rates/price_for_fiat_at_time/` is publicly accessible (no authentication required) and returns precise historical cryptocurrency exchange rates for any timestamp.

## Endpoint Details

**URL**: `https://walletbot.me/api/v1/exchange_rates/price_for_fiat_at_time/`

**Required parameters**: `crypto_currency`, `local_currency`, `amount`, `time` (Unix timestamp)

## Evidence

```bash
# Current rate (no auth)
curl "https://walletbot.me/api/v1/exchange_rates/price_for_fiat_at_time/?crypto_currency=TON&local_currency=USD&amount=1&time=$(date +%s)" -H "X-HackerOne-Research: kzspy"
# → {"rate":"1.428073216716","fiat_amount":"1.428073216716","currency_from":"TON","currency_to":"USD","amount_from":"1","time":"2026-10-07T18:25:04Z"}

# Historical rate (1 year ago, also works):
curl "https://walletbot.me/api/v1/exchange_rates/price_for_fiat_at_time/?crypto_currency=TON&local_currency=USD&amount=1&time=1759861511" -H "X-HackerOne-Research: kzspy"
# → {"rate":"2.775469634967",...,"time":"2025-10-07T18:25:11Z"}
```

Supported pairs tested: TON/USD, TON/RUB, USDT/THB, BTC/USD, ETH/EUR

## Potential Privacy Concern

If combined with publicly visible blockchain data (TON is a public ledger), an attacker could:
1. Observe a transaction on the TON blockchain at a known timestamp
2. Query the exchange rate at that timestamp
3. Correlate the fiat value with known payment amounts to link on-chain activity to walt.io users

In practice, this is an informational finding — the data is useful for user-facing features (showing historical values) and the risk is low because TON transactions are already public.

---
*Testing conducted manually. Header `X-HackerOne-Research: kzspy` included on all requests.*
