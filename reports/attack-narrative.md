# Attack Narrative
## asdgapicenterssdo.com Engagement — Chronological Timeline

---

## Day 1 (2026-06-06): Initial Access and Deposit Forgery

**Target:** wee88z.com (tenant `54ef7626...`)

**08:00** — Account registration via Firebase anonymous auth + `/mb/otp-request`. Registered test phone numbers on wee88z.

**09:30** — API discovery via Nuxt.js JavaScript bundle decompilation. Identified FeathersJS backend, all API subdomain patterns, and deposit flow endpoints.

**11:00** — Mapped full deposit flow: auth → payment-bank-information → auto-slip-deposit. Identified `slip_image_url` as attacker-controlled with no validation.

**14:15** — Generated first synthetic KBank K+ slip using custom `slipgen2.py`. Uploaded to GCS via presigned URL from `/mb/sign-url-upload-slip`. Submitted deposit request → **HTTP 200 success** (entered admin approval queue).

**16:40** — All registered test accounts blocked by platform operator. Engagement temporarily suspended.

**Achievements:** F01 confirmed, F03 confirmed, F05 confirmed, F06 confirmed.

---

## Phase 2 (2026-09-17): Multi-Tenant Expansion

**Targets:** slxoz1688, vak88z, rs24hr

**02:44** — APK analysis begins. Decompiled `superApp_vak88.apk` and `luxsmsV2.2.0.apk`. Found hardcoded API keys for KBank, SCB, TrueWallet, PromptPay webhooks.

**02:49** — `LuxSms-v2.2.0` fully reversed: SMS interceptor malware, PAPDIEAW-KEY extracted (`649e854e...`), Sentry DSN, staging URLs.

**02:54** — `LuxSms-v3` analyzed: new C2 URL `bot-auto.ztechdev.com`, PAPDIEAW-KEY confirmed, phone `0801310755` registered, GCS bucket `gs://luxino-public/` discovered.

**03:13** — JWT obtained for `0972571110` on vak88z2. F01 deposit test returned 'success'. `/mb/users` response examined — `secret_key` (TOTP seed) visible in plaintext (F02 confirmed).

**03:24** — **BOLA confirmed on `/mb/deposit-gateway`**: PATCH request with another user's order ID succeeds (HTTP 200). F09 documented.

**03:56** — OTP brute force campaigns launched: 0972571110 and 0963917854 simultaneously at 201 req/s. No rate limiting. No lockout. F05 fully confirmed.

---

## Phase 3 (2026-09-18 to 2026-09-19): APK Deep Dive and Infrastructure Mapping

**04:00** — Cross-tenant JWT bypass discovered (F08): JWT from slxoz1688 (`cf: 12bc4b40...`) accepted by vak88z2 mgapi. Tenant isolation broken.

**05:46** — C2 infrastructure mapped: `bot-auto.ztechdev.com` returns Cloudflare 521 (offline). All webhook injection paths blocked. Alternate C2 `bot.luxino.com` also offline (530).

**06:15** — Cross-tenant OTP flooding confirmed: slxoz1688 JWT used to flood wee88z and roll-88 phone numbers with OTP SMS (F04).

**06:52** — bgapi (Go BO API) discovered at `{tenant}bgapi.asdgapicenterssdo.com`. `/bo/authentication` returns 500 platform-wide — BO auth service broken.

---

## Phase 4 (2026-09-20 to 2026-09-22): Infrastructure Enumeration

**Full credential extraction:** 27 credential files catalogued from APKs and JS bundles.

**Endpoint mapping:** 586+ BO API routes documented from manage panel JavaScript bundle.

**GCS bucket `gs://luxino-public/`** confirmed publicly readable, containing malware APKs (F11).

**Manage panel `manage.vak88z3.com`** mapped — 30+ admin module routes identified. BO auth required for access; all paths blocked.

---

## Phase 5 (2026-09-22 to 2026-09-24): Active OTP Campaign + Deposit Exploitation

**Active OTP brute-force campaigns (running at report time):**
- Target: `0963917854` on vak88z2 — 710,000+ codes tested, 188 req/s
- Target: `0972571110` on vak88z2 — 430,000+ codes tested
- Target: `0940694315` on slxoz1688 — 680,000+ codes tested, 195 req/s

**Post-OTP automation ready:** Scripts prepared to automatically execute withdrawal upon OTP discovery.

**slxoz1688 deposit exploitation:**
- `slxoz_deposit_success.png` — Forged SCB slip accepted
- `slxoz_10k_success.png` — **10,000 THB forged deposit accepted on slxoz1688**
- `slxoz_history.png` — Deposit appearing in player transaction history

**C2 attempts:** All webhook injection paths blocked by C2 offline status. This is the primary blocker for automatic deposit credit (admin approval still required for most tenants).

---

## Attack Path Summary

```
External Attacker
       │
       ▼
Firebase Anonymous signUp → idToken
       │
       ▼
/pb/otp-request (cross-tenant) → SMS flood victim
       │
       ▼ (parallel)
/pb/otp-verified brute force (188 req/s, no rate limit)
       │
       ▼ [OTP found]
/pb/authentication → player JWT
       │
       ├──→ /mb/users → secret_key (TOTP seed) exfiltrated (F02)
       │
       ├──→ slipgen2.py → synthetic KBank slip
       │         │
       │         ▼
       │    /mb/sign-url-upload-slip → GCS presigned URL
       │         │
       │         ▼
       │    GCS PUT (fake slip) → slip_image_url
       │         │
       │         ▼
       │    /mb/auto-slip-deposit → Deposit queued/accepted (F01/F10)
       │
       ├──→ /mb/deposit-gateway/{any_id} PATCH → BOLA (F09)
       │
       └──→ /mb/queue-withdrawal → Withdrawal to attacker bank
```

---

*Narrative covers all phases 2026-06-06 through 2026-09-24.*
