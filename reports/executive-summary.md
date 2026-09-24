# Executive Summary
## Penetration Test — asdgapicenterssdo.com Multi-Tenant Gambling SaaS
### September 2026

---

**Risk Rating: CRITICAL**

An authorized security assessment of the asdgapicenterssdo.com multi-tenant gambling platform identified **15 vulnerabilities** — 3 Critical, 5 High, 3 Medium, 2 Low — that collectively represent a serious and exploitable financial fraud risk.

---

## What Was Found

**The platform accepts forged bank transfer slips.** Players can generate synthetic bank slips using publicly available tools, upload them via the platform's own file upload API, and submit deposit requests. The platform does not verify slips against any bank API, does not perform OCR amount validation, and does not check QR codes against payment clearing networks. This was successfully demonstrated: a **10,000 THB forged deposit was accepted** on the slxoz1688 tenant (photographic evidence collected).

**Any account can be taken over in under 2 hours.** The OTP verification endpoint has no rate limiting. An attacker can test all 1,000,000 possible 6-digit OTP codes at 188+ requests per second without triggering any lockout. This enables account takeover of any registered user.

**Users' two-factor authentication seeds are exposed in plain text.** The `/mb/users` API returns TOTP secret keys, bank account numbers, and security question answers in every authenticated response. Combined with account takeover, attackers can immediately disable 2FA on compromised accounts.

**A developer backdoor can crash the platform.** An unauthenticated URL (`/pb/steavej0b/clearcache`) flushes the entire platform cache, causing 10-second response delays and HTTP 502 errors. Any person on the internet can call this endpoint repeatedly to sustain service degradation.

**The platform distributes SMS malware.** A publicly readable Google Cloud Storage bucket (`gs://luxino-public/`) contains Android APK files that silently intercept banking SMS messages from victims' phones and forward them to a command-and-control server.

---

## Top 3 Recommendations

1. **Validate bank transfers against bank APIs before crediting deposits.** Integrate KBank Open Banking and SCB APIs to verify transfer reference numbers. This is the single most impactful fix.

2. **Add OTP rate limiting immediately.** Limit OTP attempts to 5 per code, 3 codes per hour per phone number. This prevents ATO within hours.

3. **Remove the `/steavej0b/clearcache` developer backdoor.** Delete this route from all production deployments today.

---

*For full technical details, see `reports/technical-report.md`.*
