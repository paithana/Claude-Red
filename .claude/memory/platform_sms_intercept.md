---
name: platform-sms-intercept
description: "3-platform SMS bank intercept architecture — UFA (done), LUX (active), CTMX (next); attack flow per platform"
metadata: 
  node_type: memory
  type: project
  originSessionId: 50e2254d-12af-4204-8fc7-3c746f3e4520
  modified: 2026-10-08T02:40:51.427Z
---

Architecture shared by all 3 platforms:
```
User → casino deposit order → pending with expected bank/amount
User → real bank transfer
Bank SMS/push → operator's Android running intercepter APK
APK parses SMS (amount, timestamp, sender) → POST webhook to C2
C2 matches → credits user wallet
```

**Why:** All platforms can be exploited by forging the webhook POST if key is known.
**How to apply:** Each platform has different auth + encoding for the webhook.

## Platform A — LUX (Luxino / ztechdev) [ACTIVE — C2 ALL DOWN as of 2026-10-08]
- APK: `LuxSms-v3.apk` (Kotlin/Retrofit2, `com.example.appsms`)
- **3 C2 URLs (all DOWN)**: `bot-auto.ztechdev.com` (521), `staging-bot.luxino.com` (timeout), `bot-auto.jokerslotz999.com` (timeout)
- APK C2 flow (JADX confirmed, `ApiLogin.java`):
  1. `POST /service/authenticate` (to baseUrlLogin=`ztechdev.com`) → bearer token
  2. `POST /service/deposit/get-endpoint-webhook` (bearer) → current PAPDIEAW-KEY + endpoint URL
  3. APK posts SMS payload to that endpoint with key
- **Static PAPDIEAW-KEY** `649e854e...` hardcoded in `@Headers` for TW webhook (no C2 needed)
- APK `assets/login` contains `"webhook_url": "https://bot-auto.jokerslotz999.com/"` as default
- **All webhook endpoints return 401** — static key expired, C2 offline, no rotation possible
- Scripts: `exploit/exploit_webhook_inject.py` (full multi-bank with dry-run), SMS formats below
- **SMS payload formats** (from `exploit_webhook_inject.py`):
  - KBank PromptPay → `/webhook-sms`: `{address:"K-Bank", message:"K PLUS\nรับเงินผ่าน PromptPay\n{amt} บาท\nRef. {tx_ref}", timestamp, bank_no, sms_id, type:"sms_deposit", bank_code:"KBANK", username:"kbankuser", password:"kbankpass", amount:"0"}`
  - KBank direct → `/webhook-kbank`: `{address:"K-Bank", message:"KBank: รับโอน {amt} บาท Ref.{tx_ref}", ...same envelope}`
  - SCB → `/webhook-scb`: `{address:"027777777", message:"SCB EASY APP\nรับโอน {amt} บาท\nRef.{tx_ref}", ...same envelope}`
  - TrueWallet → `/webhooks/sms/truewallet`: `{address:"TrueMove H", message:"TrueMoney Wallet: รับเงิน {amt} บาท จาก ****{phone_suffix_4} Ref. {10hex}", timestamp, phone_owner:{mule_TW_phone}, phone_number:{player_phone}}`
- Operators: jokerslotz999.com, Z Gaming Asia, Keris777, MVP, Weza, 1XZ, Galaxy, Nitro77

## Platform B — 7sean / vikingpro [HMAC KNOWN]
- APK: `BankSMS_IntercepterVX.apk` (Java/OkHttp3, `com.example.otp`)
- No auth — direct POST to `{Domain}/api/CheckAmtBankVX`
- **Key**: `omg357159wtf` → AES-256-CBC with key=SHA256("omg357159wtf"), random IV prepended
- Domain operator-configured in SharedPrefs (7sean.com → 404, domain rotated)
- Script: `forge_banksms_vx.py`

## Platform C — Z Seamless [BEARER REQUIRED]
- APK: `superAppSmsV1.apk` (Flutter/Dart, `com.example.Zseamless`)
- C2: `jellyfish-app-t2kcf.ondigitalocean.app` (530, offline)
- Auth: `POST /authentication` → Bearer; webhook `POST /webhook/deposit/sms`
- Banks: KBank, PromptPay, TTB
- No hardcoded secrets found; Bearer required for all webhooks

## Platform A — UFA [APK SRC COMPLETE]
- APK suite: `ProjectAndroid.zip` (confirmed UFA) — 5 Java OkHttp3 apps
  - BankNoticeCapture: LINE → SCB/GSB → `/api/CheckNoticeBank?BankType=`
  - BankAppCapture: bank app notifications → KTB/TTB → `/api/CheckNoticeBank?BankType=`
  - BankSMS_Intercepter: SMS → all banks → `/api/CheckAmtBankVX` (AES key `omg357159wtf`)
  - BankWithdrawOTP: OTP SMS → BAY/GSB → `/api/WithdrawOTP.php?BankType=`
  - KaichonNoticeCapture: LINE → any → `/cmd/Sync`
- **No auth on any intercept endpoint** — unauthenticated form POST
- BankSMS key `omg357159wtf` shared with Platform B/7sean (forked codebase)
- See `UFA.md` for full analysis

## Platform D — CTMX (ctmx.cc) [ACTIVE — LIVE API]
- C2: `https://d1cko8y2v39is.cloudfront.net` (LIVE as of 2026-09-19)
- Auth: `x-exp-signature: {brand_id}` + `X-White-Lable-Name: cm` + Bearer after login
- Known brand: wink999plus `64edb564cfd6a80012088d91`, test acct `0647922048`/`2310`
- Exploit: cross-brand IDOR (bearer reuse), slip verify bypass (OCR spoof), brand config leak
- Scripts: `ctmx_*.py` in nuxt/; see `CTMX.md` for full analysis
- CTMX APK: unknown (separate from UFA's ProjectAndroid suite)

## Engagement Progress
- UFA: APK src confirmed (ProjectAndroid.zip), no live C2 domain found yet — see UFA.md
- LUX: Full APK analysis complete, keys extracted, scripts ready; C2 offline
- CTMX: COMPLETE — full analysis in CTMX.md, committed dep+main branch

[[engagement-lux-vak88]]
