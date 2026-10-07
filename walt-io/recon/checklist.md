# Walt.io Manual Testing Checklist

## Setup
- [ ] Create Telegram account for testing
- [ ] Sign up at t.me/walt
- [ ] Set recovery email to `kzspy@wearehackerone.com`
- [ ] Set up Burp Suite proxy for Telegram WebApp traffic
- [ ] Confirm `X-HackerOne-Research: kzspy` header on all requests

## Authentication
- [ ] Telegram `initData` HMAC validation — send modified user_id
- [ ] initData replay attack (old timestamp accepted?)
- [ ] Recovery email flow — OTP brute force / predictable token
- [ ] Session token entropy and expiry
- [ ] Cross-device session invalidation

## Authorization (BOLA/IDOR)
- [ ] Wallet ID enumeration — increment/GUID swap
- [ ] Transaction history of other users (`/transactions?wallet_id=X`)
- [ ] Beneficiary/contact list of other users
- [ ] Admin or internal role escalation
- [ ] TON address → user account mapping (reverse lookup IDOR)

## Financial Logic
- [ ] Withdrawal without sufficient balance (race condition / negative amount)
- [ ] Duplicate transaction submission (replay)
- [ ] Floating point precision in balance calculations
- [ ] Currency conversion manipulation
- [ ] Transfer to self (infinite balance loop?)
- [ ] Pending transaction cancellation after credit

## TON Connect
- [ ] dApp connection — malicious dApp can drain wallet?
- [ ] Transaction approval bypass
- [ ] Signing arbitrary messages

## WebApp / Client
- [ ] postMessage origin validation
- [ ] Sensitive data in localStorage / sessionStorage
- [ ] Deep link parameter injection
- [ ] CSP bypass leading to script execution

## Infrastructure
- [ ] Subdomain enumeration (crt.sh, amass)
- [ ] Admin panels on non-obvious subdomains
- [ ] S3 / GCS bucket misconfiguration
- [ ] GraphQL introspection enabled
- [ ] Debug endpoints (`/debug`, `/health`, `/metrics` — check for data leaks only, not DoS)
