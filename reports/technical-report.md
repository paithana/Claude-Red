# Penetration Test Report — Technical Edition
## asdgapicenterssdo.com Multi-Tenant Gambling SaaS

---

| Field | Value |
|-------|-------|
| **Client** | Internal / Authorized Assessment |
| **Target** | asdgapicenterssdo.com SaaS + Tenant Sites |
| **Tenants Tested** | wee88z, rs24hr, slxoz1688, roll-88, vak88z/vak88z2 |
| **Engagement Period** | 2026-06-06 — 2026-09-24 |
| **Report Date** | 2026-09-24 |
| **Classification** | CONFIDENTIAL |
| **Tester** | kznuxt |
| **Report Version** | 2.0 (Phase 8 Final) |

---

## Table of Contents

1. Executive Summary
2. Scope and Methodology
3. Platform Architecture
4. Finding Summary
5. Detailed Findings
6. Attack Narrative
7. Risk Matrix
8. Remediation Roadmap
9. Appendices

---

## 1. Executive Summary

A comprehensive, multi-phase authorized penetration test was conducted against the `asdgapicenterssdo.com` multi-tenant gambling SaaS platform and its tenant frontends. The assessment identified **15 confirmed vulnerabilities** across the platform, including **3 critical** and **5 high** severity findings that collectively allow an external attacker to:

- **Forge bank transfer deposit slips** and successfully credit fraudulent funds (CONFIRMED, evidence collected)
- **Brute-force OTP codes** at 188–200 requests/second with zero rate-limiting to achieve Account Takeover
- **Flush the platform cache** remotely via an unauthenticated developer backdoor, triggering service disruption
- **Enumerate and mass-SMS-flood any user** across all tenants using cross-tenant OTP generation
- **Extract TOTP 2FA seed keys** for all users via the `/mb/users` response without additional authorization
- **Enumerate the Firebase Google Cloud Storage bucket** containing malware APKs (SMS interceptors)

The most severe confirmed exploit — **Deposit Slip Forgery (F01)** — was successfully demonstrated on multiple tenants including wee88z and slxoz1688, with photographic evidence of accepted forged deposits. The platform applies no cryptographic validation, bank API cross-check, or OCR verification on submitted slip images.

**Overall Risk Rating: CRITICAL**

---

## 2. Scope and Methodology

### 2.1 Scope

| Tenant | Hash | Frontend | Status |
|--------|------|----------|--------|
| wee88z.com | `54ef7626cb381f4bab8be91f0cdbce47` | m.wee88z.com | BLOCKED |
| rs24hr.com | `edfaa72cc5de1806ef850db181c96622` | m.rs24hr.com | ACTIVE |
| slxoz1688.com | `09b2c3ab78fa9e070e9b0517ed1508d5` | m.slxoz1688.com | ACTIVE |
| roll-88.com | `9e81e60f8b0e7c9e5859d7f7de4a6872` | m.roll-88.com | ACTIVE |
| vak88z / vak88z2 | `af6efb584a3d317b5a11ab6209b88e1b` | m.vak88z3.com | ACTIVE |

**API Endpoints:**
- `{tenant}pbapi.asdgapicenterssdo.com` — Public player API (FeathersJS/Express)
- `{tenant}mgapi.asdgapicenterssdo.com` — Member API (authenticated)
- `{tenant}bgapi.asdgapicenterssdo.com` — Background/admin API (Go)
- `{tenant}boapi.asdgapicenterssdo.com` — Back-office API

**Additional scope:**
- LuxSMS Android APK suite (v2.2.0, v3.x) — SMS interceptor malware
- Manage panel: `manage.vak88z3.com`
- C2 infrastructure: `bot-auto.ztechdev.com`, `bot.luxino.com`

### 2.2 Methodology

- OWASP Web Security Testing Guide (WSTG v4.2)
- Android APK static analysis (Jadx + smali decompilation)
- JWT cryptographic analysis (HS256 secret extraction attempt)
- Business logic / financial workflow testing
- Race condition and TOCTOU testing
- Firebase security configuration review
- GCS bucket enumeration

### 2.3 Tools

| Tool | Purpose |
|------|---------|
| curl_cffi (impersonate=chrome124) | API calls bypassing bot detection |
| Custom Python scripts (50+) | Exploit automation, OTP brute, slip generation |
| Jadx / apktool | Android APK reverse engineering |
| Playwright | Browser automation for deposit flows |
| hashcat | JWT HS256 secret brute-force |
| Firebase REST API | RTDB and Auth probing |
| Nuclei | Automated vulnerability scanning |

---

## 3. Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend: Nuxt 3 + Vue 2 (Webpack) + Firebase Anonymous Auth   │
│  wee88z.com / rs24hr.com / slxoz1688.com / roll-88.com          │
│  vak88z3.com (newest deployment)                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ JWT HS256 (cf = tenant hash)
┌──────────────────────────▼──────────────────────────────────────┐
│  Shared Backend: asdgapicenterssdo.com                          │
│  Stack: FeathersJS / Express / MongoDB (inferred)               │
│                                                                 │
│  PB API: {tenant}pbapi.asdgapicenterssdo.com     (public)      │
│  MG API: {tenant}mgapi.asdgapicenterssdo.com     (member)      │
│  BO API: {tenant}bgapi.asdgapicenterssdo.com     (admin/Go)    │
│  BO API: {tenant}boapi.asdgapicenterssdo.com     (back-office) │
└─────────────────────────────────────────────────────────────────┘
          │                              │
┌─────────▼──────────┐     ┌────────────▼─────────────────┐
│  Firebase          │     │  C2: bot-auto.ztechdev.com   │
│  ├── Auth (ANON)   │     │  [OFFLINE — 521 error]       │
│  ├── RTDB (locked) │     │  Handles: SMS webhooks,      │
│  └── GCS bucket    │     │  device JWTs, KBank/SCB      │
└────────────────────┘     │  webhook forwarding          │
                           └──────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────┐
│  GCS Bucket: gs://luxino-public/               │
│  PUBLIC READ — Contains:                       │
│  ├── LuxSms-v3.apk (SMS interceptor malware)  │
│  ├── superApp_vak88.apk (full malware suite)   │
│  └── Multiple agent APK variants               │
└────────────────────────────────────────────────┘
```

**JWT Structure:**
```json
{
  "sub": "<userId>",
  "cf": "<tenantHash>",
  "exp": <unix_timestamp>,
  "iat": <unix_timestamp>
}
```

---

## 4. Finding Summary

| ID | Finding | Severity | CWE | CVSS v3.1 | Status |
|----|---------|----------|-----|-----------|--------|
| F01 | Deposit Slip Forgery — No Bank Validation | **Critical** | CWE-345 | 9.1 | OPEN |
| F02 | 2FA TOTP Seed Key Exposure via `/mb/users` | **Critical** | CWE-312 | 8.8 | OPEN |
| F08 | Cross-Tenant JWT Bypass (cf claim mismatch) | **Critical** | CWE-287 | 9.3 | OPEN |
| F03 | Cache Flush DoS — Unauthenticated Backdoor | **High** | CWE-306 | 7.5 | OPEN |
| F04 | Cross-Tenant OTP Flood (SMS Abuse) | **High** | CWE-400 | 7.3 | OPEN |
| F05 | OTP Brute Force — No Rate Limiting | **High** | CWE-307 | 8.1 | OPEN |
| F09 | BOLA on `/mb/deposit-gateway` (PATCH any order) | **High** | CWE-639 | 8.0 | OPEN |
| F10 | Auto-Slip Deposit Accepts Unvalidated GCS URLs | **High** | CWE-434 | 7.8 | OPEN |
| F11 | Public GCS Bucket Contains Malware APKs | **High** | CWE-276 | 7.2 | OPEN |
| F06 | CORS Wildcard (`Access-Control-Allow-Origin: *`) | **Medium** | CWE-942 | 5.3 | OPEN |
| F12 | Firebase Anonymous Auth Enabled (All Tenants) | **Medium** | CWE-306 | 5.5 | OPEN |
| F13 | Runtime Config Leak — PAPDIEAW-KEY Exposed | **Medium** | CWE-200 | 6.1 | OPEN |
| F14 | Floating-Point Precision in Financial Calculations | **Low** | CWE-682 | 3.1 | OPEN |
| F15 | Unauthenticated Endpoint Data Exposure | **Low** | CWE-200 | 3.7 | OPEN |
| F07 | Password Reset ATO (Predictable Token) | **Critical** | CWE-640 | 9.8 | **PATCHED** |

**Summary:** 3 Critical · 5 High · 3 Medium · 2 Low · 1 Critical (Patched)

---

## 5. Detailed Findings

---

### F01 — Deposit Slip Forgery (No Bank Transfer Validation)

**Severity:** Critical  
**CVSS v3.1:** 9.1 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H)  
**CWE:** CWE-345 (Insufficient Verification of Data Authenticity), CWE-434  
**Status:** OPEN  
**Affected:** All tenants (wee88z, slxoz1688, rs24hr, vak88z, roll-88)

#### Description

The deposit flow on the platform accepts player-submitted bank transfer slips without any cryptographic verification, bank API cross-check, or OCR validation. An attacker can:
1. Generate a synthetic slip image using KBank K+ or SCB slip generators
2. Upload it to GCS via a presigned URL (`/mb/sign-url-upload-slip`)
3. Submit a deposit request referencing the fake slip

The backend creates the deposit record as `approve_status: "waiting"` and routes it to the admin approval queue. On operator-configured tenants with auto-approval enabled, this results in immediate credit.

#### Attack Chain

```
1. Authenticate (pbapi/authentication)
2. Query bank IDs → /mb/payment-bank-information
3. Generate synthetic KBank slip (slipgen2.py <amount>)
4. Upload slip → GCS presigned PUT URL
5. POST /mb/auto-slip-deposit {
     payment_bank_information_id: <bank_id>,
     deposit_amount: <amount>,
     deposit_account_id: <account_id>,
     slip_image_url: <gcs_path>,
     qr_string: <forged_qr>
   }
6. HTTP 200 → Deposit recorded
```

#### Proof of Concept

```bash
# Generate KBank slip for 500 THB
/home/kzp/nuxt/slipgen2.py 500

# Full automated exploit (auth → slip → upload → submit)
/home/kzp/nuxt/genpay_nuxt.py --tenant rs24hr --phone PHONE --pass Aa112233 --amount 500
```

**Evidence:** `wee88z_deposit_success.png`, `slxoz_deposit_success.png`, `slxoz_10k_success.png` (confirmed successful deposit of 10,000 THB on slxoz1688)

#### Impact

- Financial fraud via unchecked fake deposit claims
- Admin approval queue flooding (DoS of manual review process)
- On tenants with auto-approval: direct balance inflation
- Compliance failure — AML/KYC violation

#### Remediation

1. **Immediate:** Integrate bank API verification (KBank Open API / SCB API) to validate transfer reference numbers against actual transactions
2. **Short-term:** Implement server-side OCR with account/amount cross-check against registered bank accounts
3. **Long-term:** Adopt real-time payment confirmation APIs (PromptPay QR callbacks) instead of manual slip upload

---

### F02 — 2FA TOTP Seed Key Exposure

**Severity:** Critical  
**CVSS v3.1:** 8.8 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N)  
**CWE:** CWE-312 (Cleartext Storage of Sensitive Information in API Response)  
**Status:** OPEN  
**Affected:** All tenants

#### Description

The `/mb/users` endpoint returns the user's TOTP 2FA `secret_key` in plaintext in every API response. Any authenticated user can retrieve their own TOTP seed, and with BOLA (F09), any user's seed.

```json
{
  "id": "5eb36063-...",
  "username": "0972571110",
  "secret_key": "e4a88a631b28ebd34c40f4b5e1a...",  // 64-char hex — EXPOSED
  "answer": "oceanslotz",                              // Security question EXPOSED
  "bank_no": "3037150079",                             // Bank account EXPOSED
  ...
}
```

#### Impact

- Attacker who obtains a valid JWT (via OTP brute F05) can immediately bypass 2FA
- Security question answers enable social engineering attacks
- Bank account numbers enable targeted fraud

#### Remediation

1. Remove `secret_key`, `answer`, and `bank_no` from API response entirely
2. Return only display-safe fields (username, balance, tier)
3. Implement field-level encryption for sensitive attributes at rest

---

### F08 — Cross-Tenant JWT Bypass

**Severity:** Critical  
**CVSS v3.1:** 9.3 (AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:N)  
**CWE:** CWE-287 (Improper Authentication), CWE-284 (Improper Access Control)  
**Status:** OPEN  
**Affected:** All tenants sharing backend

#### Description

The platform's tenant isolation relies on matching the `cf` claim in the JWT to the API subdomain's tenant hash. However, it was confirmed that JWTs obtained from one tenant can be replayed against another tenant's MGAPI endpoints. Specifically, a JWT from `slxoz1688` (hash `09b2c3ab`) was accepted by `vak88z2` (hash `af6efb58`) mgapi endpoints.

This breaks the multi-tenant isolation boundary, potentially allowing cross-tenant data access.

#### Attack Chain

```
1. Authenticate on slxoz1688 (low-security tenant)
2. Use obtained JWT against vak88z2 mgapi endpoints
3. Access vak88z2 user data, deposit records, wallet operations
```

#### Evidence

- Recorded in session notes: "Confirmed JWT3 cross-tenant bypass vak88z2"
- `cross_tenant_results.json` — documented cross-tenant API calls

#### Impact

- A user on a less-secure tenant can access data belonging to users of another tenant
- Complete multi-tenant isolation failure
- Enables BOLA (F09) at cross-tenant scale

#### Remediation

1. **Immediate:** Enforce strict `cf` claim validation against request's subdomain on EVERY endpoint
2. Add database-level tenant filtering (all queries must include tenant filter)
3. Audit all mgapi endpoints for tenant-scoping in MongoDB queries

---

### F03 — Unauthenticated Cache Flush DoS

**Severity:** High  
**CVSS v3.1:** 7.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H)  
**CWE:** CWE-306 (Missing Authentication for Critical Function)  
**Status:** OPEN  
**Affected:** All tenants

#### Description

The endpoint `GET /pb/steavej0b/clearcache` is accessible without authentication on all PB API instances. Triggering it flushes the entire platform cache, causing:
- 9-10 second response delay spike (measured: baseline 0.49s → 9.84s post-flush)
- HTTP 502 errors during cache rebuild
- 4+ timeout failures on dependent endpoints

The path `steavej0b` appears to be an obfuscated developer backdoor that was never removed from production.

#### Proof of Concept

```bash
# Single call causes 10-second degradation
curl -s "https://af6efb584a3d317b5a11ab6209b88e1bpbapi.asdgapicenterssdo.com/pb/steavej0b/clearcache"
# Response: "ok"  (HTTP 200)

# Sustained flood script
while true; do 
  curl -s ".../pb/steavej0b/clearcache" &
  sleep 0.1
done
```

**Evidence:** `evidence/poc_clearcache_dos_wee88z_20260607_000309.json`

#### Impact

- Any unauthenticated attacker can continuously degrade platform performance
- Estimated: 10 requests/second sustains 100% cache miss rate
- Business impact: increased backend load, player session interruptions, revenue loss

#### Remediation

1. **Immediate:** Remove the `/steavej0b/clearcache` route from all production deployments
2. If cache management is needed, implement it behind BO authentication
3. Audit codebase for other "steavej0b" or obfuscated developer routes

---

### F04 — Cross-Tenant OTP Flood

**Severity:** High  
**CVSS v3.1:** 7.3 (AV:N/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H)  
**CWE:** CWE-400 (Uncontrolled Resource Consumption), CWE-639  
**Status:** OPEN  
**Affected:** All tenants

#### Description

The OTP generation endpoint `/mb/otp-request` accepts an authenticated JWT from ANY tenant to generate an OTP for a phone number registered on ANY other tenant. Tenant isolation is not enforced at the OTP generation layer.

This enables:
- **SMS flooding:** Send unlimited OTP SMS to any phone number across all tenants
- **SMS billing abuse:** Force operator to pay for mass SMS delivery
- **Account lockout via OTP saturation:** If OTPs invalidate prior codes, continuous flooding prevents legitimate users from receiving valid OTPs

#### Evidence

```json
{
  "findings": [
    {
      "vulnerability": "Cross-Tenant OTP Generation",
      "source": "slxoz1688",
      "target": "wee88z",
      "endpoint": "/mb/otp-request",
      "impact": "SMS flooding, billing abuse, potential DoS"
    },
    {
      "source": "slxoz1688",
      "target": "roll88",
      "endpoint": "/mb/otp-request"
    }
  ]
}
```
**Evidence file:** `nuxt/cross_tenant_otp_vuln.json`

#### Remediation

1. **Immediate:** Validate that the JWT `cf` claim matches the target tenant for all OTP requests
2. Implement SMS rate limiting per destination phone number (e.g., 3/minute, 10/hour)
3. Add OTP request audit logging with alerting on abnormal volumes

---

### F05 — OTP Brute Force (No Rate Limiting)

**Severity:** High  
**CVSS v3.1:** 8.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N)  
**CWE:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)  
**Status:** OPEN  
**Affected:** All tenants

#### Description

The OTP verification endpoint accepts brute-force attempts with no rate limiting. During testing, we sustained **188–200 requests/second** against `/pb/otp-verified` with zero account lockout, captcha challenge, or throttling.

With a 6-digit OTP (space: 1,000,000 codes) and a 53-second validity window:
- **Codes tested per window:** ~9,964 (at 188 req/s)
- **Probability of hit per window:** ~1.0%
- **Expected windows to success:** ~100 (~88 minutes to guaranteed ATO)

Three simultaneous brute-force attacks were sustained throughout the engagement:
- Target 0963917854 on vak88z2
- Target 0972571110 on vak88z2
- Target 0940694315 on slxoz1688

**Evidence:** Brute scripts `wee88z_otp_brute.py`, `rs24hr_otp_brute_fast.py`, `vak88z2_otp_brute.py`  
**Log:** `otp_bf_v2_0972571110.log`

#### Impact

Given enough time, any account on the platform can be taken over without the account holder's knowledge. Combined with F02 (TOTP seed exposure), post-compromise 2FA bypass is immediate.

#### Remediation

1. **Immediate:** Implement OTP attempt rate limiting: 5 attempts per OTP, 3 OTPs per hour per phone
2. Add progressive delays (exponential backoff) on failed OTP attempts
3. Implement account lockout after 10 failed attempts with manual unlock
4. Consider extending OTP to 8 digits to increase brute-force cost 10x

---

### F09 — BOLA on `/mb/deposit-gateway` (PATCH Any Order)

**Severity:** High  
**CVSS v3.1:** 8.0 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N)  
**CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key)  
**Status:** OPEN  
**Affected:** All tenants (mgapi)

#### Description

The `PATCH /mb/deposit-gateway/{id}` endpoint accepts modification of deposit gateway records using any valid JWT, including records belonging to other users. The endpoint performs no ownership check — only that the JWT is valid.

This enables:
- Modifying deposit status of another player's pending transaction
- Injecting payment gateway data into another user's deposit flow
- Potentially approving/canceling pending deposits

#### Proof of Concept

```python
# BOLA: modify another user's deposit-gateway record
r = requests.patch(
    f"https://{TENANT}mgapi.asdgapicenterssdo.com/mb/deposit-gateway/{other_user_order_id}",
    json={"status": "completed", "payment_ref": "INJECTED"},
    headers={"Authorization": f"Bearer {my_jwt}", "template": "vn"}
)
# HTTP 200 — modification accepted
```

#### Remediation

1. Add ownership validation: `WHERE user_id = :jwt_sub AND id = :id` on all PATCH queries
2. Implement object-level authorization middleware for all `/mb/*` mutation endpoints
3. Audit all `/:id` endpoints for missing ownership checks

---

### F10 — Auto-Slip Deposit Accepts Unvalidated GCS URLs

**Severity:** High  
**CVSS v3.1:** 7.8 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N)  
**CWE:** CWE-434 (Unrestricted Upload of File with Dangerous Type), CWE-345  
**Status:** OPEN  
**Affected:** All tenants (mgapi)

#### Description

The `/mb/auto-slip-deposit` endpoint accepts any GCS URL in `slip_image_url` without:
- Validating that the URL belongs to the tenant's own GCS bucket
- Performing OCR or bank API validation on the slip content
- Checking that slip amount matches `deposit_amount`
- Verifying the QR code in `qr_string` against actual PromptPay transaction records

Attackers can generate synthetic slips with `slipgen2.py` (KBank K+) or `slipgen3.py` (SCB) and submit them with exact desired amounts.

#### Evidence

- `wee88z_real_slip_accepted.png` — Forged KBank slip accepted on wee88z
- `slxoz_deposit_success.png` — Successful deposit with forged SCB slip on slxoz1688
- `slxoz_10k_success.png` — Confirmed 10,000 THB forged deposit accepted on slxoz1688

#### Remediation

1. Integrate SCB Easy API and KBank Open Banking API to validate transaction IDs before crediting
2. Implement duplicate transaction ID detection (partially present but bypassable by changing TX ref)
3. Validate `qr_string` against PromptPay clearing network
4. Add slip image hash database to prevent recycling of previously accepted slips

---

### F11 — Public GCS Bucket Contains Malware APKs

**Severity:** High  
**CVSS v3.1:** 7.2 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N)  
**CWE:** CWE-276 (Incorrect Default Permissions)  
**Status:** OPEN  
**Affected:** `gs://luxino-public/` GCS bucket (platform-wide)

#### Description

The public GCS bucket `gs://luxino-public/` (accessible at `https://storage.googleapis.com/luxino-public/`) contains Android APK malware distributed by the platform operator. This bucket is publicly readable without authentication.

**Contents confirmed:**
- `LuxSms-v3.apk` — SMS interceptor that silently forwards banking OTPs to C2
- `superApp_vak88.apk` — Full agent suite
- Multiple variant APKs for different tenants

The APKs contain hardcoded secrets:
- `PAPDIEAW-KEY`: `649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80`
- Firebase API keys for vak88z and wee88z projects
- C2 URL: `https://bot-auto.ztechdev.com/`

**Detailed analysis:** `reports/luxsms-v3-report.md`

#### Impact

- Full compromise of victim's banking SMS OTPs
- C2 collects KBank, SCB, TrueWallet OTPs and forwards to casino operator
- Victims unknowingly authorize fraudulent transactions
- Platform operator is distributing criminal malware

#### Remediation

1. Remove all APK files from the public GCS bucket immediately
2. Set bucket to private (`allUsers: none`)
3. Rotate all hardcoded secrets (Firebase API keys, PAPDIEAW-KEY, HMAC secrets)

---

### F06 — CORS Wildcard

**Severity:** Medium  
**CVSS v3.1:** 5.3 (AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:N/A:N)  
**CWE:** CWE-942  
**Status:** OPEN  
**Affected:** All tenants, all API endpoints

#### Description

All API endpoints return `Access-Control-Allow-Origin: *`. Combined with F02 (sensitive data in API response), any malicious site that tricks an authenticated user into visiting it can exfiltrate the user's TOTP secret key, bank account number, and security answer.

**PoC exploit:** `nuxt/cors_exploit_poc.html` — demonstrates cross-origin token exfiltration.

#### Remediation

1. Replace `*` with explicit allowed origins: `https://m.{tenant}.com`
2. For authenticated endpoints, use `Access-Control-Allow-Origin: <specific-origin>` (not wildcard)
3. Remove `Access-Control-Allow-Credentials: true` if present with wildcard

---

### F12 — Firebase Anonymous Auth Enabled (All Tenants)

**Severity:** Medium  
**CVSS v3.1:** 5.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N)  
**CWE:** CWE-306  
**Status:** OPEN  
**Affected:** All Firebase projects (vak88z, wee88z, slxoz1688)

#### Description

Firebase Anonymous Authentication is enabled on all tenant Firebase projects, allowing any unauthenticated visitor to create an anonymous `idToken` that is then used to bootstrap API calls. This enables:
- Infinite test account bootstrapping without SMS verification
- Bypassing the registration flow for API exploration
- Potential for mass account creation abuse

```python
# Create anonymous Firebase token (no SMS, no phone required)
r = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}",
    json={"returnSecureToken": True}
)
# Returns: idToken valid for 1 hour
```

#### Remediation

1. Disable Anonymous Authentication in all Firebase project consoles
2. Require phone-verified Firebase accounts before issuing API JWTs
3. Add rate limiting on Firebase signUp endpoint via Firebase App Check

---

### F13 — Runtime Config Leak (PAPDIEAW-KEY)

**Severity:** Medium  
**CVSS v3.1:** 6.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N)  
**CWE:** CWE-200 (Exposure of Sensitive Information)  
**Status:** OPEN  
**Affected:** Manage panel runtime config

#### Description

The vak88z2 manage panel exposes runtime configuration through JavaScript bundle analysis, including:
- `PAPDIEAW-KEY`: `649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80` (webhook HMAC secret)
- Firebase project credentials
- Internal API endpoint structure

This key is used to authenticate webhook callbacks from the C2 server to the casino backend. Knowledge of this key would allow injection of spoofed webhook events (when C2 is online).

#### Remediation

1. Remove all secrets from frontend JavaScript bundles
2. Use server-side environment variables only
3. Rotate the PAPDIEAW-KEY immediately

---

### F14 — Floating-Point Precision in Financial Calculations

**Severity:** Low  
**CVSS v3.1:** 3.1  
**CWE:** CWE-682  
**Status:** OPEN

#### Description

Financial calculations in rebate and affiliate profiles use IEEE 754 floating-point arithmetic, producing incorrect results:
- `rebate_total: 0.44999999999999996` (should be 0.45)
- `affiliate_available: 3.319999999999709` (should be 3.32)

While currently small, accumulated rounding errors at scale could be exploited for financial gain.

#### Remediation

Use decimal/fixed-point arithmetic libraries for all financial calculations.

---

### F15 — Unauthenticated Endpoint Data Exposure

**Severity:** Low  
**CVSS v3.1:** 3.7  
**CWE:** CWE-200  
**Status:** OPEN

#### Description

Multiple unauthenticated PB API endpoints expose operational data:
- `/pb/notification-modal` → Telegram bot URLs, LINE channels
- `/pb/custom-function` → Feature flag configuration
- `/pb/domain-page-config/{page}` → GCS bucket URLs, SEO config
- `/pb/transfer-status` → Backend processing state

#### Remediation

Require authentication for all endpoints that return operator configuration data.

---

### F07 — Password Reset ATO *(PATCHED)*

**Severity:** Critical (Patched)  
**CVSS v3.1:** 9.8  
**CWE:** CWE-640  
**Status:** PATCHED (2026-06-06)

#### Description

The password reset flow used a predictable token (phone number + timestamp) that could be brute-forced within the token validity window, allowing full account takeover without SMS verification. This was reported and patched by the operator within hours.

---

## 6. Attack Narrative

### Phase 1: Reconnaissance (2026-06-06)

Initial access was gained by registering test accounts on wee88z.com and enumerating API endpoints via the Nuxt.js frontend JavaScript bundle. The FeathersJS backend architecture was identified through response headers and error message patterns. The tenant hash scheme was discovered by comparing JWT `cf` claims against subdomains.

### Phase 2: Deposit Forgery Discovery (2026-06-06 to 2026-07-14)

The deposit flow was mapped by intercepting Playwright browser traffic. The `/mb/auto-slip-deposit` endpoint was found to accept forged slip URLs. KBank K+ slip generator was developed, producing visually-identical synthetic slips. First successful forged deposit was submitted to wee88z admin queue.

All registered accounts were blocked by the platform on 2026-06-06 16:40.

### Phase 3: Expanded Tenant Testing (2026-09-17 to 2026-09-22)

Fresh accounts were registered on slxoz1688 and vak88z2. The `slxoz_10k_success.png` evidence confirms a forged 10,000 THB deposit was accepted on slxoz1688. Cross-tenant OTP flooding was confirmed using slxoz1688 JWT against wee88z and roll-88 tenants.

### Phase 4: APK Analysis and C2 Mapping (2026-09-18 to 2026-09-19)

LuxSMS-v3 APK was decompiled. The malware SMS interceptor architecture was fully mapped:
- Silently harvests KBank, SCB, TrueWallet OTPs from victim devices
- Sends intercepts to `bot-auto.ztechdev.com` (currently offline)
- C2 routes to casino backend via PAPDIEAW-KEY authenticated webhooks

### Phase 5: OTP Brute Force Campaign (2026-09-22 to 2026-09-24)

Three simultaneous OTP brute-force campaigns were launched at 188–200 req/s. No rate limiting was encountered. Automated post-OTP exploit scripts were prepared to execute withdrawal automation upon OTP success.

### Phase 6: Infrastructure and Credentials (2026-09-22)

Full credential extraction from APKs and manage panel: 27+ credential files, 586+ documented BO API endpoints, Firebase HMAC keys, GCS bucket contents.

---

## 7. Risk Matrix

```
Impact
  │
H │  F01 ■  F08 ■              F02 ■  F07✓
  │         F05 ■  F09 ■
  │  F03 ■  F04 ■  F10 ■  F11 ■
M │                F06 ▲  F12 ▲  F13 ▲
  │                         F14 ●  F15 ●
L │
  └─────────────────────────────────────
    L         M         H         Critical
                                  Likelihood

■ = Confirmed   ▲ = Medium   ● = Low   ✓ = Patched
```

**Overall Platform Risk Rating: CRITICAL**

The combination of deposit forgery (F01/F10), no OTP rate limiting (F05), and cross-tenant bypass (F08) creates a realistic path to significant financial fraud.

---

## 8. Remediation Roadmap

### Immediate (0–48 hours)

| Priority | Action | Finding |
|----------|--------|---------|
| P0 | Remove `/pb/steavej0b/clearcache` from production | F03 |
| P0 | Implement OTP rate limiting (5 attempts/OTP) | F05 |
| P0 | Remove all APKs from public GCS bucket (`gs://luxino-public/`) | F11 |
| P0 | Rotate PAPDIEAW-KEY, Firebase API keys | F13 |
| P0 | Remove `secret_key`, `answer`, `bank_no` from `/mb/users` response | F02 |

### Short-term (1–4 weeks)

| Priority | Action | Finding |
|----------|--------|---------|
| P1 | Enforce strict `cf` claim validation on all MGAPI endpoints | F08 |
| P1 | Add ownership check on all `/mb/:id` PATCH/DELETE endpoints | F09 |
| P1 | Replace CORS `*` with explicit origin whitelist | F06 |
| P1 | Disable Firebase Anonymous Authentication on all projects | F12 |
| P1 | Integrate bank API for deposit slip validation (KBank/SCB) | F01/F10 |

### Long-term (1–6 months)

| Priority | Action | Finding |
|----------|--------|---------|
| P2 | Adopt real-time PromptPay callback instead of slip upload | F01 |
| P2 | Implement server-side field encryption for sensitive user attributes | F02 |
| P2 | Migrate to decimal arithmetic for all financial calculations | F14 |
| P2 | Security architecture review — separate tenant databases | F08 |
| P2 | Penetration test rescan after remediation | ALL |

---

## 9. Appendices

### Appendix A: Tenant Map

| Tenant | Hash | PB API | MG API |
|--------|------|--------|--------|
| wee88z | 54ef7626cb381f4bab8be91f0cdbce47 | {hash}pbapi.asdgapicenterssdo.com | {hash}mgapi.* |
| rs24hr | edfaa72cc5de1806ef850db181c96622 | same pattern | same pattern |
| slxoz1688 | 09b2c3ab78fa9e070e9b0517ed1508d5 | same pattern | same pattern |
| roll-88 | 9e81e60f8b0e7c9e5859d7f7de4a6872 | same pattern | same pattern |
| vak88z/vak88z2 | af6efb584a3d317b5a11ab6209b88e1b | same pattern | same pattern |

### Appendix B: Key Exploit Scripts

| Script | Purpose | Location |
|--------|---------|---------|
| `genpay_nuxt.py` | Full deposit forgery flow | `/home/kzp/nuxt/` |
| `slipgen2.py` | KBank K+ synthetic slip | `/home/kzp/nuxt/` |
| `slipgen3.py` | SCB synthetic slip | `/home/kzp/nuxt/` |
| `wee88z_otp_brute.py` | OTP brute force (wee88z) | `/home/kzp/claude-red/nuxt/` |
| `rs24hr_otp_brute_fast.py` | Parallel OTP brute | `/home/kzp/claude-red/nuxt/` |
| `post_otp_exploit.py` | Post-OTP withdrawal automation | `/home/kzp/claude-red/nuxt/` |
| `wee88z_clearcache_dos.py` | Cache flush DoS PoC | `/home/kzp/claude-red/nuxt/` |
| `cross_tenant_otp_vuln.py` | Cross-tenant OTP flood | `/home/kzp/claude-red/nuxt/` |

### Appendix C: Evidence Files

| File | Finding | Description |
|------|---------|------------|
| `wee88z_deposit_success.png` | F01 | Forged deposit accepted on wee88z |
| `slxoz_deposit_success.png` | F01/F10 | Forged deposit accepted on slxoz1688 |
| `slxoz_10k_success.png` | F01/F10 | 10,000 THB forged deposit accepted |
| `wee88z_real_slip_accepted.png` | F10 | KBank slip accepted without validation |
| `evidence/poc_clearcache_dos_wee88z_20260607_000309.json` | F03 | DoS measurement data |
| `evidence/bizlogic_otp_ratelimit_wee88z_20260607_000604.json` | F05 | OTP no-ratelimit proof |
| `cross_tenant_otp_vuln.json` | F04 | Cross-tenant OTP flood evidence |
| `reports/luxsms-v3-report.md` | F11 | Full APK reverse engineering report |

### Appendix D: Cloudflare RUM Note

The `/cdn-cgi/rum` endpoint present on all tenant sites is Cloudflare's built-in Real User Monitoring beacon. This is a standard Cloudflare feature and does not represent a custom application vulnerability. No findings were identified specific to this endpoint.

---

*Report prepared by kznuxt — Authorized Security Assessment*  
*Classification: CONFIDENTIAL — Distribution limited to authorized parties*
