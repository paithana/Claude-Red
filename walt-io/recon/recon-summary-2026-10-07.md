# Walt.io Passive Recon Summary — 2026-10-07

**Researcher**: kzspy  
**Scope**: walletbot.me, walt.io, *.walletbot.me  
**Method**: Passive (DNS, HTTP headers, JS bundle analysis)  

---

## Infrastructure Map

| Host | IPs | Notes |
|------|-----|-------|
| walt.io | 45.196.29.103-105 (CF) | Marketing/landing (Next.js) |
| walletbot.me | 45.196.29.10-12 (CF) | **TWA app host** — React SPA |
| alectryon.walletbot.me | Cloudflare | Referenced in JS preconnect |
| p2p.walletbot.me | Cloudflare | P2P service (404 root) |
| events-gateway.walletbot.me | Cloudflare | Event tracking |
| sentry.walletbot.me | CF + istio-envoy | Sentry error tracking |
| walletteam.org | 188.42.196.119-120 (Servers.com) | Internal backend |

- **Backend**: Kubernetes + Istio service mesh (confirmed via `server: istio-envoy`)
- **CDN**: Cloudflare everywhere, with `__cflb` cookie indicating load balancing
- All API requests go to `https://walletbot.me` (base URL from JS bundle)

## Authentication Flow

1. App opens at `https://walletbot.me` inside Telegram WebApp SDK v9.0.3
2. `window.Telegram.WebApp.initData` provides HMAC-signed user data
3. `POST /api/v1/users/authorize_by_telegram/` with `{hash, id, initData}`
4. Server **validates HMAC** (confirmed — returns `signature_not_correct` on invalid hash)
5. Session token returned for subsequent API calls

## API Surface (202 endpoints discovered from openapi.e66d0a28ee.js)

### High-Value Targets (require auth — all return 401 unauthenticated)

| Endpoint | BOLA Risk | Notes |
|----------|-----------|-------|
| `GET /api/v1/transactions/details/{transaction_id}/` | HIGH | Sequential or UUID IDs? |
| `POST /api/v1/transactions/cancel/{transaction_id}/` | HIGH | Cancel other user's tx? |
| `POST /api/v1/transactions/approve/tg_transfer_onchain/{transaction_id}/` | HIGH | Approve other's transfer? |
| `GET /api/v1/payment_links/{payment_link_id}/` | HIGH | Read/claim other's links |
| `POST /api/v1/giveaways/gift/{gift_uid}/claim` | HIGH | Steal gift |
| `GET /p2p/public-api/v2/offer/order/history/get-by-user-id` | HIGH | User ID param explicit |
| `GET /p2p/public-api/v2/user-statistics/get/by-user-id` | HIGH | User ID param explicit |
| `GET /p2p/public-api/v3/payment-details/get/by-user-id` | HIGH | Payment methods by user |

### Public Endpoints (no auth required)

| Endpoint | Response |
|----------|----------|
| `POST /api/v1/users/authorize_by_telegram/` | Auth entry (validates HMAC) |
| `GET /p2p/public-api/health` | `{"name":"p2p-market","status":"OK"}` |
| `GET /users/public-api/health` | `{"name":"user-service","status":"OK"}` |

## Findings (Passive Phase)

### [INFO] Developer Telegram IDs in Client-Side JS
- 27 developer Telegram IDs hardcoded for `appdebug` mode in `app.*.js`
- Debug mode loaded via `?startapp=appdebug` — Eruda console
- See `findings/finding-INFO-01-dev-ids-in-js.md`

### [INFO] Sentry DSN Exposed in CSP Header
- Key: `544a92e441a24f17aa6b08e34e728ed2`, Project: 38, Env: production
- `https://sentry.walletbot.me/api/38/security/?sentry_key=...`
- Could allow error injection or event flooding (out of scope per program policy)

## Next Steps (Require Account)

1. Register Telegram account → open t.me/walt  
2. Capture initData via Burp proxy  
3. Test BOLA on `transaction_id`, `payment_link_id`, `gift_uid` params  
4. Test `by-user-id` endpoints with another test account's ID  
5. Test initData replay with old `auth_date`  
6. Test race condition on transfers  

## Notes

- **App redeployed mid-recon** (bundle hashes changed; openapi.js stable)
- All `by-user-id` endpoints return 401 without auth (correct behavior for now)
- P2P market depth / currency list also 401 (unusual — usually public in P2P markets)
