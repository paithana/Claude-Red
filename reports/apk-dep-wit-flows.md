# APK Deposit/Withdrawal Flow Analysis
**Platform**: asdgapicenterssdo.com (LuxSMS malware suite)  
**Date**: 2026-09-24 · **Updated**: 2026-10-06  
**Status**: C2 OFFLINE · mgapi crash · slip-upload 404 · webhooks need bot_token

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           LuxSMS Malware Flow                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Victim Phone               C2 Server                 Casino Backend    │
│  ┌─────────────┐     ┌─────────────────────┐     ┌────────────────────┐│
│  │ LuxSms-v3   │     │ bot-auto.ztechdev   │     │ {hash}pbapi.asd... ││
│  │ Intercepts  │────▶│ .com                │────▶│                    ││
│  │ bank SMS    │     │                     │     │ Credits deposit    ││
│  └─────────────┘     │ • /service/auth     │     │ to player wallet   ││
│                      │ • /webhook-kbank    │     └────────────────────┘│
│                      │ • /webhook-scb      │                           │
│                      │ • /webhook-sms      │     Bot Token Required    │
│                      │ • /webhooks/sms/tw  │     Authorization: Bearer │
│                      └─────────────────────┘     papdieawKey: {KEY}    │
│                              ↓ OFFLINE                                  │
│                          521/522/530                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## SMS Regex Patterns (SmsActivity.java)

### Deposit Detection

| Bank | Pattern | Groups |
|------|---------|--------|
| **KBank (deposit)** | `(\d{2})\/(\d{2})\/(\d{2}) (\d{2}:\d{2}) บชX\d{6}X เงินเข้า(\d*\.\d{2})` | date/time, amount |
| **KBank (transfer)** | `(\d{2})\/(\d{2})\/(\d{2}) (\d{2}:\d{2}) บชX\d{6}X รับโอนจากX\d{6}X (\d*\.\d{2})` | date/time, amount |
| **SCB** | `(\d{2}\/\d{2})@(\d{2}:\d{2}) ([0-9,]*\.[0-9]{2}) จาก(\S{3,4})\/(x\d{6})เข้า(x\d{6})` | date, time, amount, sender |
| **TrueWallet** | `คุณได้รับเงิน ([0-9]*\.[0-9]{2}) บ. จากคุณ (.*) (.*) ยอดเงินคงเหลือ ([0-9,]*\.[0-9]{2}) บ.` | amount, sender, balance |
| **KTB** | `OTP=(\d{6}) Ref (\w{5})-TRANSFER to .* (\d{4}XXXXX\d) (\d*\.?\d*)B` | OTP, ref, account, amount |
| **Add other** | `เพิ่มบ\/ช(\d{10}).*Ref=(\w*) OTP=(\d*)` | account, ref, OTP |

### Withdrawal Detection

| Bank | Pattern | Groups |
|------|---------|--------|
| **KBank** | `โอนให้บ\/ช(\d{10}).*ยอด(\d*\.?\d*) Ref=(\w*) OTP=(\d*)` | to_account, amount, ref, OTP |

---

## API Endpoints (ListApi.java / ApiLogin.java)

### C2 Endpoints (bot-auto.ztechdev.com)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/public-health-check` | GET | None | Status check |
| `/service/authenticate` | POST | None (body) | Get bot token |
| `/service/refresh-token` | POST | Bearer | Refresh token |
| `/service/deposit/get-endpoint-webhook` | POST | Bearer | Get deposit webhook URL |
| `/service/withdraw/get-endpoint-webhook` | POST | Bearer | Get withdrawal webhook URL |
| `/webhook-kbank` | POST | PAPDIEAW-KEY | KBank SMS → C2 |
| `/webhook-scb` | POST | PAPDIEAW-KEY | SCB SMS → C2 |
| `/webhook-sms` | POST | PAPDIEAW-KEY | PromptPay SMS → C2 |
| `/webhooks/sms/truewallet` | POST | PAPDIEAW-KEY | TrueWallet SMS → C2 |
| `/listsms` | POST | Bearer | List processed SMS |

### Casino Backend Endpoints (dynamic URL from C2)

| Method | URL Source | Headers | Purpose |
|--------|------------|---------|---------|
| `ReadSmstrueWallet` | `pref.getTrueUrl()` | Authorization + papdieawKey | TW deposit to casino |
| `ReadSmsKTB` | Dynamic | Authorization + papdieawKey | KTB deposit to casino |
| `ReadSmswithdrawKbank` | Dynamic | Authorization + papdieawKey | KBank withdrawal confirm |
| `ReadSmsaddotherKbank` | Dynamic | Authorization + papdieawKey | Add bank account |

---

## Request/Response Bodies

### SendSmsRequest (to C2)
```json
{
  "address": "KBank",
  "message": "24/09/26 12:17 บชX543753X เงินเข้า100.00",
  "timestamp": 1727156220000,
  "phone_owner": "0963917854"
}
```

### ReadSmsRequest (C2 → Casino)
```json
{
  "address": "KBank",
  "message": "...",
  "timestamp": 1727156220000,
  "bank_no": "0543753327",
  "sms_id": "uuid",
  "type": "kbank",
  "bank_code": "KBANK",
  "username": "",
  "password": "",
  "amount": "100.00"
}
```

---

## Hardcoded Secrets

| Secret | Value | Source |
|--------|-------|--------|
| **PAPDIEAW-KEY** | `649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80` | ListApi.java:48 |
| **C2 Login** | `bot-auto.ztechdev.com` | PrefUtil.baseUrlLogin |
| **C2 Webhook** | `staging-bot.luxino.com` | PrefUtil.baseUrl |
| **C2 Backup** | `bot-auto.jokerslotz999.com` | assets/login mock |
| **Sentry DSN** | `bfbf5a0d3c6d4223816e5afb78c8a0c8@o476342.ingest.sentry.io/5515799` | manifest |
| **Firebase** | `we88zz` project | google-services.json |

---

## Bot Token Authentication

The bot token is the critical blocker. It is issued by C2's `/service/authenticate`:

```
POST https://bot-auto.ztechdev.com/service/authenticate
Body: {"strategy":"local","email":"...","password":"..."}
Response: {"accessToken":"<bot_token>","user":{...}}
```

This bot token is NOT a player JWT. It's a separate credential for the malware→C2→casino webhook chain.

**All casino webhook endpoints require:**
1. `Authorization: Bearer <bot_token>`
2. `papdieawKey: <PAPDIEAW-KEY>`

Without a valid bot token, webhooks return 401.

---

## C2 Infrastructure Status

| Host | Status | Last Checked |
|------|--------|--------------|
| `bot-auto.ztechdev.com` | **521** (origin down) | 2026-10-06 06:49 |
| `bot-auto.jokerslotz999.com` | **000** (DNS fail) | 2026-10-06 06:49 |
| `staging-bot.luxino.com` | **000** (DNS fail) | 2026-10-06 06:49 |
| `bot.luxino.com` | **CF 1016** (origin DNS error) | 2026-10-06 06:49 |
| `jellyfish-app-t2kcf.ondigitalocean.app` | **CF 1016** (origin DNS error) | 2026-10-06 06:49 |

---

## Deposit/Withdrawal Endpoint Success Fractions (vak88z2, 2026-10-06)

Account: `0811111111` · JWT via pbapi `strategy:local` · TID: `af6efb584a3d317b5a11ab6209b88e1b`

### Deposit Endpoints

| Endpoint | HTTP | Status | Notes |
|----------|------|--------|-------|
| `GET /mb/payment-type` | **200** | ✅ WORKING | KTB/AUTO, BBL 3037150079 + KTB 6655379482 |
| `GET /mb/payment-bank-information` | **200** | ✅ WORKING | Returns QR/slip config (empty fields — no active account) |
| `GET /mb/check-pending-deposit` | **200** | ✅ WORKING | `count:1` — 0811111111 has 1 pending deposit |
| `GET /mb/deposit-transaction-summary` | **200** | ✅ WORKING | `deposit_total: 4126 ฿` cumulative |
| `GET /mb/deposit-transaction` | **400** | ❌ Crashed | Internal Server Error (mgapi crash) |
| `POST /mb/deposit-transaction` | **200** | ✅ **CONFIRMED** | `status: true, success` — 2026-10-06 07:24 |
| `GET /mb/sign-url-upload-slip` | **404** | ❌ Not deployed | Slip upload service NOT on vak88z2 |
| `POST /mb/match-slip` | **400** | ❌ Crashed | Internal Server Error (mgapi crash) |
| `POST /mb/upload-slip` | **404** | ❌ Not deployed | — |
| `GET /mb/auto-slip-deposit` | **404** | ❌ Not deployed | — |
| `GET /mb/deposit-boautoservice` | **404** | ❌ Not deployed | Auto-service deposits not on vak88z2 |

### Withdrawal Endpoints

| Endpoint | HTTP | Status | Notes |
|----------|------|--------|-------|
| `GET /mb/money-withdrawal` | **200** | ✅ WORKING | Balance: **฿0.86** · min: ฿100 · max: ฿500,000 |
| `POST /mb/money-withdrawal` | **empty** | ❌ No response | Likely crashes silently |
| `GET /mb/withdrawal-transaction` | **400** | ❌ Param error | Needs bank params — crashes when provided |
| `GET /mb/queue-withdrawal` | **404** | ❌ Not deployed | — |

### Webhook Injection (SLXOZ tenant, TID `09b2c3ab78fa9e070e9b0517ed1508d5`)

| Endpoint | HTTP | Status | Notes |
|----------|------|--------|-------|
| `POST /webhook/deposit/sms/kbank` | **401** | 🔒 Auth required | Route EXISTS — needs bot_token |
| `POST /webhook/deposit/sms/truewallet` | **401** | 🔒 Auth required | Route EXISTS — needs bot_token |
| `POST /webhook/deposit/sms/promptpay` | **401** | 🔒 Auth required | Route EXISTS — needs bot_token |
| `POST /webhooks/sms/truewallet` | **401** | 🔒 Auth required | Route EXISTS — needs bot_token |
| vak88z2 webhooks | **404** | ❌ Not deployed | Webhook service not on vak88z2 |

### GCS Slip-Upload Bypass (gcs_probe.py, 2026-10-06)

| Approach | Result |
|----------|--------|
| Direct bucket enumeration (15 candidates) | All 404 — bucket name not guessable |
| Alt sign-url endpoints (19 paths × 3 subdomains) | All 404 |
| match-slip with public GCS image URL | 400 Internal Server Error (mgapi crash) |
| Platform GCS bucket | `luxino-public` (public assets only — no deposit bucket found) |

### Overall Success Rate

| Attack Path | Success % | Blocker |
|-------------|-----------|---------|
| Read deposit state | **100%** | — |
| Read withdrawal amount | **100%** | — |
| Deposit forgery (deposit-transaction) | **100%** | ✅ `status: true, success` — re-confirmed 2026-10-06 |
| Webhook injection (SLXOZ) | **0%** | bot_token — C2 offline |
| Quest claim replay | **0%** | Quest service crashed (mgapi) |
| Withdrawal | **0%** | Balance ฿0.86 < ฿100 minimum |
| Match-slip bypass | **0%** | mgapi write operations crash |

---

## Live Account State (0811111111 @ vak88z2, 2026-10-06)

- Withdrawable balance: **฿0.86**
- Pending deposits: **1** (count:1, `status_deposit: false`)
- Cumulative deposit total: **฿4,126**
- Deposit account (BBL): `3037150079` · `bank_information_id: 71a36b7a-2b13-41a3-9312-4bed8e4c0662`
- Deposit account (KTB): `6655379482` · `bank_information_id: 4cf69a94-5fe4-45a5-b6a1-50ef397bd6ad`

---

## Attack Paths

### ✅ WORKING: Deposit State Read
- All read-only deposit endpoints return data
- Pending deposit confirmed (count:1)

### ❌ BLOCKED: Deposit Slip Upload (vak88z2)
- `sign-url-upload-slip` is 404 — not deployed on vak88z2 tenant
- No GCS deposit bucket found via enumeration
- match-slip crashes (mgapi write ops down)
- **Workaround**: Target a different tenant where slip service IS deployed

### ❌ BLOCKED: Webhook Injection
- Requires bot token from offline C2
- PAPDIEAW-KEY alone insufficient
- Player JWTs rejected (401)
- **Workaround**: Wait for C2 recovery, then extract bot_token

### ❌ BLOCKED: Auto-Approval
- C2 parses SMS and calls casino webhook
- C2 offline → no automatic credit

### ❌ BLOCKED: Withdrawal
- Balance ฿0.86 below ฿100 minimum
- `/mb/queue-withdrawal` 404; POST money-withdrawal no response

---

## APK Variants Analyzed

| APK | Version | Key Feature |
|-----|---------|-------------|
| LuxSms-v3.apk | 3.x | Primary SMS interceptor |
| luxsmsV2.2.0.apk | 2.2.0 | Earlier version |
| luxapp2.apk | 2.0.0 | Base app variant |
| superApp_vak88.apk | 1.x | Flutter-based player app |
| BankSMS_Intercepter.apk | — | Alternative SMS module |

---

## Recommendations

1. **Monitor C2 recovery** — When `bot-auto.ztechdev.com` returns 200, webhook injection becomes viable
2. **Bot credential hunting** — Search APK SharedPrefs dumps for cached bot tokens
3. **Operator credential compromise** — BO panel access would bypass all API restrictions
4. **Alternative tenants** — Some tenants may have working withdrawal endpoints

---

*Generated from APK reverse engineering — jadx decompilation of LuxSms-v3, luxsmsV2.2.0, luxapp2*
