# Walt.io Recon — Target Surface

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

## Discovered API Endpoints (from openapi.e66d0a28ee.js)

### Core API (`alectryon.walletbot.me/api/v1/`)
```
/api/v1/accounts/                          ← BOLA candidate: user account data
/api/v1/accounts/frozen
/api/v1/currencies/local_currency/
/api/v1/currencies/set_new_currency_seen/
/api/v1/exchange/amount_interval/
/api/v1/exchange/convert/
/api/v1/exchange/create_exchange/
/api/v1/exchange/get-available-exchanges/
/api/v1/forced_exchange/convert/
/api/v1/giveaways/gift/available
/api/v1/ipo/info/list/
/api/v1/ipo/order/
/api/v1/notifications/
/api/v1/notifications/update
/api/v1/payment_links/                     ← BOLA: payment link ownership
/api/v1/payment_links/enabled/
/api/v1/payment_links/validate_amount/
/api/v1/scw_coins/list/
/api/v1/transactions/                      ← BOLA candidate: tx history
/api/v1/transactions/crypto/
/api/v1/transactions/single-account/
/api/v1/transactions/tg_transfer_onchain
/api/v1/transactions/unconfirmed/
/api/v1/transfers/create_transfer_request/ ← Financial logic target
/api/v1/transfers/price_for_fiat/
/api/v1/users/authorize_by_telegram/       ← Auth entry point (initData)
/api/v1/users/available_networks/
/api/v1/users/set-visitor-id/
/api/v1/withdrawals/by_intention/          ← Financial logic target
/api/v1/withdrawals/validate_amount/
```

### Microservices (routed via alectryon)
```
/alectryon/public-api/auth-refresh         ← Token refresh
/dactylos/public-api/v1/data               ← Unknown microservice (analytics?)
/dactylos/public-api/v1/user
/loyalty/public-api/v1/availability
/loyalty/public-api/v1/tooltip/ack
/loyalty/public-api/v1/tooltip/claim
/onboarding/public-api/v1/offers/
/onboarding/public-api/v1/offers/dry_run
/onboarding/public-api/v1/target/
/p2p/public-api/health
```

## Parameterized Endpoints (BOLA Priority Targets)
```
/api/v1/accounts/{crypto_currency}/                              ← per-currency balance
/api/v1/transactions/details/{transaction_id}/                   ← BOLA: read other tx
/api/v1/transactions/cancel/{transaction_id}/                    ← BOLA: cancel other tx
/api/v1/transactions/cancel/pending/{transaction_id}/
/api/v1/transactions/approve/tg_transfer_onchain/{transaction_id}/  ← BOLA: approve other tx
/api/v1/transactions/reference_transaction_details/{transaction_id}/
/api/v1/payment_links/{payment_link_id}/                         ← BOLA: read other links
/api/v1/payment_links/{payment_link_id}/cancel/
/api/v1/payment_links/{payment_link_id}/claim/
/api/v1/payment_links/{payment_link_id}/open/
/api/v1/giveaways/gift/{gift_uid}/                               ← BOLA: gift info
/api/v1/giveaways/gift/{gift_uid}/claim                          ← BOLA: steal gift
/api/v1/giveaways/{giveaway_uid}/gift/
/api/v1/ipo/info/{ipo_id}/
/api/v1/ipo/order/{order_uid}/cancel/                            ← BOLA: cancel others' orders
/api/v1/exchange/submit_exchange/{exchange_uid}/
/api/v1/coins/catalog/{fiat_currency}
/api/v1/coins/list/{fiat_currency}/
/api/v1/coins/trending/{fiat_currency}/
```

## Known Public Endpoints (no auth)
```
POST /api/v1/users/authorize_by_telegram/  ← auth entry, validates HMAC (confirmed)
GET  /p2p/public-api/health                ← {"name":"p2p-market","status":"OK"}
```

## Attack Surface Priority
1. **`/api/v1/users/authorize_by_telegram/`** — initData replay (old auth_date accepted?); server validates HMAC ✓
2. **`/api/v1/transactions/details/{transaction_id}/`** — BOLA: can A read B's transaction?
3. **`/api/v1/transactions/approve/tg_transfer_onchain/{transaction_id}/`** — BOLA: approve another user's transfer
4. **`/api/v1/payment_links/{payment_link_id}/claim/`** — BOLA: claim another user's payment link
5. **`/api/v1/giveaways/gift/{gift_uid}/claim`** — BOLA: steal unclaimed gift
6. **`/api/v1/transfers/create_transfer_request/`** — race condition / negative amount
7. **`/api/v1/withdrawals/by_intention/`** — withdrawal without sufficient balance

## Telegram WebApp Auth Notes
- App loads at `walletbot.me`, auth via `/api/v1/users/authorize_by_telegram/`
- Telegram passes `initData` to TWA on launch (HMAC-SHA256 signed)
- Server MUST validate HMAC against bot token
- **Test**: POST `{"initData": "<modified user_id>"}` to auth endpoint
- `frame-ancestors: 'self' https://web.telegram.org` — must be opened inside Telegram

## Recon Commands (manual — no AI scanning per policy)
```bash
# Headers baseline (add H1 header)
curl -sI "https://walletbot.me" -H "X-HackerOne-Research: kzspy"
curl -sI "https://alectryon.walletbot.me/api/v1/accounts/" -H "X-HackerOne-Research: kzspy"

# Auth test (no initData → should return 401/403)
curl -s "https://alectryon.walletbot.me/api/v1/users/authorize_by_telegram/" \
  -H "Content-Type: application/json" \
  -H "X-HackerOne-Research: kzspy" \
  -d '{"initData": "test"}'

# Check JS bundles for more endpoints
curl -s "https://walletbot.me/static/js/openapi.e66d0a28ee.js" | strings | grep '"/'
```
