# Luxino APK — Attack Surface Analysis

**Date**: 2026-09-17  
**Source files**: `claude-red/nuxt/luxino_apks/`, `nuxt/data/apk/luxino_main/`, `nuxt/data/apk/luxino_public/`  
**APKs analyzed**: `luxino_app.apk`, `LuxSms-v3.apk`, `superAppSmsV1.apk`, `luxapp2.0.0.apk`

---

## 🔴 Critical

### Unauthenticated TrueWallet Webhook
- **Endpoint**: `POST /webhooks/sms/truewallet`
- **Auth**: Static 64-char hex key hardcoded in `@Headers` annotation — no per-session auth
- **Impact**: Anyone with the APK can replay or inject arbitrary SMS deposit events
- **Source**: `LuxSms-v3/sources/com/example/appsms/api/ListApi.java`
- **Key type**: Static API key (`PAPDIEAW-KEY` header) — value redacted; see ListApi.java

### Firebase DEV Environment Exposed
- **Project**: `luxino-dev-gs` (dev, still live)
- **RTDB URL**: `https://luxino-dev-gs-default-rtdb.asia-southeast1.firebasedatabase.app`
- **Firebase API key**: Hardcoded in `superAppSmsV1.apk` raw binary — enables direct REST API calls, FCM token enumeration
- **App ID**: `1:876442233489:android:d2e4768e9bbc4d94456d30`
- **Storage bucket**: `luxino-dev-gs.appspot.com`
- **Quick check**: `curl https://luxino-dev-gs-default-rtdb.asia-southeast1.firebasedatabase.app/.json` — open rules = full DB read

---

## 🔴 High

### Dynamic Webhook Takeover
- `POST /service/authenticate` — returns Bearer token
- `POST /service/deposit/get-endpoint-webhook` — returns live deposit webhook URL (Bearer required)
- `POST /service/withdraw/get-endpoint-webhook` — returns live withdrawal webhook URL (Bearer required)
- `POST /service/refresh-token`
- **Impact**: Operator credential compromise → redirect all bank SMS to attacker-controlled endpoint
- **Source**: `LuxSms-v3/sources/com/example/appsms/api/ApiLogin.java`

### KBank GCM Impersonation
- **Package spoofed**: `com.kasikorn.retail.mbanking.wap` (real KBank app)
- **Methods**: `registerGCM`, `registerStep1`, `registerStep2` in `kplus/libkplusgenerator`
- **Source**: `luxino_main/resources/lib/arm64-v8a/libgojni.so`
- **Impact**: Clone KBank app's FCM registration → intercept push notifications

### KBank Internal API Cloning
All relative to `https://rt10.kasikornbank.com/kplus-service`:
- `/security/exchangeKeyAndConfigV2` — key exchange
- `/security/checkAuthenIDAndProfile` — auth check
- `/security/createAuthenID` — register auth ID
- `/mobileUtility/listOwnAccount` — account enumeration
- `/mobileUtility/unlockOnline` — online unlock trigger
- **Source**: `libgojni.so`

---

## 🟡 Medium

### C2 Backend Hardcoded
- **URL**: `https://bot-auto.ztechdev.com/`
- **Source**: `LuxSms-v3/sources/com/example/appsms/pref/PrefUtil.java:516`

### Webhook Endpoints (all banks)
- `POST /webhook-kbank` — KBank deposit SMS
- `POST /webhook-scb` — SCB deposit SMS
- `POST /webhook-sms` — PromptPay / generic SMS
- `POST /webhooks/sms/truewallet` — TrueWallet (unauthenticated — see Critical above)
- `GET /public-health-check`
- **Source**: `ListApi.java`

### Bank Credentials in SharedPreferences
Populated from C2 post-auth; stored locally:
`kbankToken`, `kbankWithdrawToken`, `scbToken`, `ktbToken`, `trueToken`,
`usernameKBank`, `passwordKBank`, `usernameSCB`, `passwordSCB`
- **Source**: `PrefUtil.java`

### Cleartext HTTP Fallback
- `http://rt10.kasikornbank.com/kplus-serviceinterrupted` — error/interrupt flow over HTTP

---

## 🔵 Info / OPSEC

- **Developer OPSEC leak**: Build path `/Users/codecracker/go/pkg/mod/` embedded in `libgojni.so`
- **Custom header** `papdieawKey`: per-request param for KTB, KBank, TrueWallet, withdrawal hooks — value fetched from Firebase/remote config at runtime
- **GCM security token**: `security_token` protobuf field in Go binary → `https://android.clients.google.com/checkin`

---

## Live Probe Results — 2026-09-18T02:40 UTC

**Script**: `nuxt/lux_probe.py` → `nuxt/lux_probe_20260918_094008.json`

| Target | Result | Severity | Notes |
|--------|--------|----------|-------|
| C2 `bot-auto.ztechdev.com` (all endpoints) | **HTTP 521** | — | Cloudflare: origin down / connection refused |
| TW webhook no-key | **521** | — | Origin offline; auth bypass inconclusive |
| TW webhook with-key | **521** | — | Origin offline; key acceptance inconclusive |
| Firebase RTDB (no-auth) | **401** Permission denied | Medium | Rules active — confirmed not open-read |
| Firebase RTDB (api_key) | **401** Permission denied | Medium | API key does not grant RTDB read |
| Firebase Remote Config | **401** UNAUTHENTICATED | Low | Requires OAuth2 bearer, not API key |
| Firebase Storage | **403** AccessDenied | Low | Private bucket |

**Status**: No live exploitable vectors confirmed at scan time. C2 offline (521). All Firebase surfaces gated.

---

## Recommended Next Steps

1. **Re-probe C2 when live** — `uv run lux_probe.py` once `bot-auto.ztechdev.com` recovers; TW webhook injection is primary target
2. **payloads.py ready** — `uv run payloads.py --curl` or `--nuclei` for full injection suite
3. **Firebase OAuth2 escalation** — test if hardcoded API key can exchange for ID token via anonymous sign-in, then re-test RTDB
4. **Deep mobile** — Frida + SSL-pinning bypass on `LuxSms-v3.apk` for runtime credential extraction

---

*Generated from subagent APK analysis — see `nuxt/luxino_apks/luxino-webhook.yaml` for nuclei test vectors.*
