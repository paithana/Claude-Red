# Finding Matrix
## asdgapicenterssdo.com Multi-Tenant Gambling SaaS

**Report Date:** 2026-09-24 | **Version:** 2.0 Final

---

| # | ID | Finding | Severity | CWE | CVSS v3.1 | Affected Tenants | Status |
|---|-----|---------|----------|-----|-----------|-----------------|--------|
| 1 | F08 | Cross-Tenant JWT Bypass (`cf` claim mismatch) | **Critical** | CWE-287 | 9.3 | All | OPEN |
| 2 | F01 | Deposit Slip Forgery — No Bank Validation | **Critical** | CWE-345 | 9.1 | All | **CONFIRMED** ✓ |
| 3 | F02 | 2FA TOTP Seed Key Exposure via `/mb/users` | **Critical** | CWE-312 | 8.8 | All | OPEN |
| 4 | F07 | Password Reset ATO (Predictable Token) | ~~Critical~~ | CWE-640 | 9.8 | All | **PATCHED** |
| 5 | F05 | OTP Brute Force — Zero Rate Limiting | **High** | CWE-307 | 8.1 | All | OPEN |
| 6 | F09 | BOLA on `/mb/deposit-gateway` | **High** | CWE-639 | 8.0 | All | OPEN |
| 7 | F10 | Auto-Slip Deposit Accepts Unvalidated GCS URLs | **High** | CWE-434 | 7.8 | All | OPEN |
| 8 | F11 | Public GCS Bucket Contains Malware APKs | **High** | CWE-276 | 7.2 | Platform | OPEN |
| 9 | F03 | Cache Flush DoS — Unauthenticated Backdoor | **High** | CWE-306 | 7.5 | All | OPEN |
| 10 | F04 | Cross-Tenant OTP Flood (SMS Abuse) | **High** | CWE-400 | 7.3 | All | OPEN |
| 11 | F13 | Runtime Config Leak — PAPDIEAW-KEY Exposed | **Medium** | CWE-200 | 6.1 | vak88z2 | OPEN |
| 12 | F12 | Firebase Anonymous Auth Enabled | **Medium** | CWE-306 | 5.5 | All | OPEN |
| 13 | F06 | CORS Wildcard (`Access-Control-Allow-Origin: *`) | **Medium** | CWE-942 | 5.3 | All | OPEN |
| 14 | F14 | Floating-Point Precision in Financial Calculations | **Low** | CWE-682 | 3.1 | All | OPEN |
| 15 | F15 | Unauthenticated Endpoint Data Exposure | **Low** | CWE-200 | 3.7 | All | OPEN |

---

## Severity Distribution

```
Critical  │ ■■■░ (3 open, 1 patched)
High      │ ■■■■■■ (6 open)
Medium    │ ■■■ (3 open)
Low       │ ■■ (2 open)
```

**Total open:** 14 | **Patched:** 1 | **Overall Risk: CRITICAL**

---

## Exploitability Assessment

| Finding | Auth Required | Complexity | Reliably Exploitable | Demonstrated |
|---------|---------------|------------|----------------------|-------------|
| F01 | Player JWT | Low | ✅ Yes | ✅ Yes (10,000 THB · re-confirmed 2026-10-06 status:true) |
| F02 | Player JWT | Low | ✅ Yes | ✅ Yes |
| F08 | Player JWT (any tenant) | Low | ✅ Yes | ✅ Yes |
| F03 | None | Low | ✅ Yes | ✅ Yes |
| F04 | Player JWT | Low | ✅ Yes | ✅ Yes |
| F05 | None (OTP req) | Low | ✅ Yes (~88 min) | ✅ Running |
| F09 | Player JWT | Low | ✅ Yes | ✅ Yes |
| F10 | Player JWT | Low | ✅ Yes | ✅ Yes |
| F11 | None | Low | ✅ Yes (public bucket) | ✅ Yes |
| F06 | Victim's JWT | Medium | ✅ Yes | PoC ready |
| F12 | None | Low | ✅ Yes | ✅ Yes |
| F13 | None (from bundle) | Low | ✅ Yes | ✅ Yes |
