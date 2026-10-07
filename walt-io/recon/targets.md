# Walt.io Recon — Target Surface
**Updated**: 2026-10-08

## Primary Surface
- Telegram Mini App (TWA): https://t.me/walt → loads https://walletbot.me
- TON Space wallet (embedded)
- Recovery email flow

## Confirmed Infrastructure

### DNS / Hosting
| Host | IPs | Notes |
|------|-----|-------|
| walt.io | 45.196.29.103-105 | Cloudflare (frontend marketing) |
| walletbot.me | 45.196.29.10-12 | Cloudflare + LB, React SPA |
| alectryon.walletbot.me | Cloudflare | **API gateway** (404 unauthenticated) |
| p2p.walletbot.me | Cloudflare | P2P service |
| events-gateway.walletbot.me | Cloudflare | Event tracking |
| sentry.walletbot.me | Cloudflare | Sentry error tracking (istio-envoy) |
| walletteam.org | 188.42.196.119-120 | Servers.com backend (internal?) |

- MX: `smtp.google.com` (Google Workspace)
- SPF: `include:_spf.google.com include:mail.zendesk.com -all`
- K8s + Istio service mesh behind Cloudflare

### Tech Stack
- **Frontend**: React SPA, Telegram WebApp SDK v9.0.3
- **Backend**: Cloudflare + Istio K8s cluster (walletteam.org)
- **Monitoring**: Sentry at `sentry.walletbot.me`
- **Sentry key** (from CSP): `544a92e441a24f17aa6b08e34e728ed2` (project 38, env: production)
- **Next.js** on walt.io marketing site
- **Integrations**: Mercuryo, AlchemyPay, Sumsub KYC, Mesh Connect, STON.fi DEX

## Authentication & Session Management

### Auth Flow
1. App opens at `walletbot.me` inside Telegram WebApp SDK
2. `window.WalletStartAuth()` called (Telegram-injected function)
3. `POST /api/v1/users/authorize_by_telegram/` with `{initData, hash, id}`
4. Server validates HMAC-SHA256 (confirmed — returns `signature_not_correct` on invalid)
5. Access token returned in response body

### Token Transport
- Main API (`apiHost`): `AuthHeader` security scheme (Bearer token in Authorization header)
- P2P API: `jwtUserToken` + `credentials:"include"` (cookie-based)
- Session refresh: `POST /alectryon/public-api/auth-refresh` with `refresh_token` cookie
  - Returns `{"code":"creds_invalid","detail":"Oops"}` on invalid JWT format
  - Returns `{"code":"UNAUTHORIZED","detail":"refreshToken is missing in cookie and in request"}` if cookie missing/wrong name

## Confirmed Public Endpoints (No Auth Required)

| Endpoint | Method | Response | Notes |
|----------|--------|----------|-------|
| `/api/v1/wallets/get_address_info/{address}` | GET | `{"isExchange":true,"exchangeName":null,"isMemoRequired":false}` | BROKEN — always same response (see finding-LOW-01) |
| `/api/v1/exchange_rates/price_for_fiat_at_time/` | GET | Live exchange rate | Requires: crypto_currency, local_currency, amount, time params |
| `/p2p/public-api/health` | GET | `{"name":"p2p-market","status":"OK"}` | Health check |
| `/alectryon/public-api/health` | GET | `{"name":"alectryon","status":"OK"}` | Health check |
| `/dactylos/public-api/health` | GET | `{"name":"dactylos","status":"OK"}` | Health check |
| `/loyalty/public-api/health` | GET | `{"name":"loyalty","status":"OK"}` | Health check |
| `/users/public-api/health` | GET | `{"name":"user-service","status":"OK"}` | Health check |
| `/api/v1/users/authorize_by_telegram/` | POST | Auth token | Entry point |

### Exchange Rates Notes
- Historical data available (tested: 1 day, 1 week, 1 month, 1 year ago)
- Returns precise rates: `{"rate":"1.428073216716","fiat_amount":"...","currency_from":"TON","currency_to":"USD","amount_from":"1","time":"..."}`
- Currencies tested: TON, USDT, BTC, ETH vs USD, EUR, THB, RUB

## Parameterized Endpoints (BOLA Priority Targets)

### Tier 1 — Financial Impact
```
GET  /api/v1/transactions/details/{transaction_id}/
GET  /api/v1/transactions/withdraw_details/{transaction_id}/         ← NEW
POST /api/v1/transactions/cancel/{transaction_id}/
POST /api/v1/transactions/cancel/pending/{transaction_id}/
POST /api/v1/transactions/cancel/tg_transfer_onchain/{transaction_id}/  ← NEW
GET  /api/v1/transactions/tg_transfer_onchain/{transaction_id}       ← NEW
POST /api/v1/transactions/approve/tg_transfer_onchain/{transaction_id}/
GET  /api/v1/transactions/reference_transaction_details/{transaction_id}/
```

### Tier 2 — Financial Links & Gifts
```
GET  /api/v1/payment_links/{payment_link_id}/
POST /api/v1/payment_links/{payment_link_id}/cancel/
POST /api/v1/payment_links/{payment_link_id}/claim/                  ← BOLA: steal another's payment
POST /api/v1/payment_links/{payment_link_id}/open/
GET  /api/v1/giveaways/gift/{gift_uid}/
POST /api/v1/giveaways/gift/{gift_uid}/claim                         ← BOLA: steal unclaimed gift
GET  /api/v1/giveaways/{giveaway_uid}/gift/
POST /api/v1/ipo/order/{order_uid}/cancel/
```

### Tier 3 — P2P BOLA (by-user-id)
```
POST /p2p/public-api/v2/offer/order/history/get-by-user-id          ← explicit user_id param
POST /p2p/public-api/v2/user-statistics/get/by-user-id              ← explicit user_id param
POST /p2p/public-api/v3/payment-details/get/by-user-id              ← explicit user_id param, payment methods
POST /p2p/public-api/v2/offer/order/get                             ← order_id in body
POST /p2p/public-api/v2/offer/get-user-own                         ← own offers
POST /p2p/public-api/v2/offer/user-own/list                        ← own offer list
```

### 2-Step Financial Race Condition Targets
```
POST /api/v1/transfers/create_transfer_request/
POST /api/v1/transfers/process_transfer/{transfer_request_id}/
POST /api/v1/withdrawals/create_withdraw_request/
POST /api/v1/withdrawals/process_withdraw_request/{withdraw_request_uid}/
```

## Complete API Endpoint Count
- **Main API (alectryon)**: 178 endpoints
- **P2P API**: 89 endpoints
- **Total**: 267 endpoints
- **Public (no auth)**: ~8 confirmed public endpoints

## All Microservices Identified
- `alectryon` — main wallet API (apiHost)
- `p2p` — P2P trading market
- `dactylos` — analytics/fingerprinting
- `loyalty` — loyalty/rewards
- `onboarding` — onboarding offers/tasks
- `user-profile` — profile/settings
- `users` — KYC/verification
- `referral` — referral programs
- `portmone` — Portmone payment integration
- `funds-gateway` — fiat on/off ramp
- `events-gateway` — event tracking

## Attack Surface Priority
1. **BOLA `/api/v1/transactions/details/{transaction_id}/`** — UUID or sequential? Can A read B's?
2. **BOLA `/p2p/public-api/v2/user-statistics/get/by-user-id`** — explicit user_id, can supply other's
3. **BOLA `/api/v1/payment_links/{payment_link_id}/claim/`** — claim another's payment link
4. **BOLA `/api/v1/giveaways/gift/{gift_uid}/claim`** — steal unclaimed gift
5. **Race condition**: create_transfer_request → process_transfer (2-step, concurrent requests)
6. **Race condition**: create_withdraw_request → process_withdraw_request
7. **P2P BOLA**: payment-details/get/by-user-id, order/history/get-by-user-id
8. **Logic**: Approve another user's TG transfer via approve endpoint

## Telegram WebApp Auth Notes
- App loads at `walletbot.me`, auth via `/api/v1/users/authorize_by_telegram/`
- Telegram passes `initData` to TWA on launch (HMAC-SHA256 signed)
- Server MUST validate HMAC against bot token
- `frame-ancestors: 'self' https://web.telegram.org` — must be opened inside Telegram
- Developer IDs in JS enable `appdebug` mode via `?startapp=appdebug`
