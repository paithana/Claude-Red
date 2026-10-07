# Security Policy

`claude-red` is an offensive security tooling library. Its content describes attack methodologies for use by authorized red team operators, penetration testers, and security researchers.

## Intended Use

These skills are intended for:

- Authorized penetration testing engagements with documented scope and rules of engagement
- Bug bounty programs with explicit written permission for the techniques described
- CTF competitions and security training environments
- Independent vulnerability research with responsible disclosure

These skills are **not** intended for unauthorized access to systems you do not own or do not have explicit, written permission to test. Misuse may violate computer-misuse laws in your jurisdiction (CFAA in the US, Computer Misuse Act in the UK, equivalent statutes elsewhere).

## Reporting a Vulnerability in claude-red Itself

If you discover a security issue in this repository — for example a malicious payload accidentally committed, a credential leaked in an example, a typosquat-prone install path, or an unsafe shell command in `install.sh` — please report it privately rather than opening a public issue.

**Contact:** security@snailsploit.com

Please include:

- Affected file(s) and commit hash
- A description of the issue and its impact
- Reproduction steps if applicable
- Any suggested remediation

We aim to acknowledge reports within 72 hours and resolve confirmed issues within 14 days.

## Reporting a Vulnerability Found Using This Library

If you discover a vulnerability in a third-party product or service while using `claude-red`'s methodologies, follow that vendor's responsible disclosure process. The [`offensive-reporting`](Skills/utility/offensive-reporting/SKILL.md) skill includes guidance on responsible disclosure, evidence handling, and report writing.

If the vendor has no published security contact:

- Try `security@<vendor-domain>`, then their PSIRT page, then `report` mailing addresses
- For ICS/OT vendors, escalate via [CISA ICS-CERT](https://www.cisa.gov/uscert/ics)
- For broad-impact bugs, request a CVE via [MITRE CNAs](https://www.cve.org/PartnerInformation/ListofPartners)
- Allow at least 90 days before public disclosure unless the vulnerability is being actively exploited

## Supply Chain Integrity

This repository is signed by SnailSploit. Verify commit signatures with:

```bash
git log --show-signature
```

If you receive a `claude-red` archive from a third party (mirror, pastebin, package manager), verify it against the upstream repository before using.

## Scope

| In scope | Out of scope |
|---|---|
| Issues in repository content (skills, scripts, install logic) | Vulnerabilities in third-party tools mentioned in skills |
| Malicious payloads in examples | The Claude platform itself (report to Anthropic) |
| Unsafe installation defaults | Bugs in tools you find using this library |
| Leaked credentials in example traffic | Bugs in your own implementation of techniques described |

## Acknowledgements

We credit researchers who report security issues responsibly in the project [CHANGELOG](CHANGELOG.md). Let us know if you'd prefer to remain anonymous.

---

## Security Research Portfolio — Engagement WE88Z-VAK88-2026-09

**Target:** Multi-tenant gambling SaaS platform (`asdgapicenterssdo.com`)  
**Engagement Period:** 2026-09-17 to 2026-10-06  
**Engagement ID:** WE88Z-VAK88-2026-09  
**Classification:** Authorized Penetration Test  
**Researcher:** kzspy (HackerOne: https://hackerone.com/kzspy)

### Summary

Authorized security assessment of a multi-tenant gambling SaaS platform identified **19 vulnerabilities** across Critical, High, Medium, and Low severity tiers. Full technical report and evidence available in `reports/`.

### Confirmed Findings

| ID | Title | Severity | CWE | CVSS |
|----|-------|----------|-----|------|
| F01 | Deposit Slip Forgery — No Bank Validation | Critical | CWE-345 | 9.1 |
| F08 | Cross-Tenant JWT Bypass (`cf` claim mismatch) | Critical | CWE-287 | 9.3 |
| F14b | BOLA — Player JWT Reads Backoffice Admin Config | Critical | CWE-639 | 9.0 |
| F02 | 2FA TOTP Seed Key Exposure via `/mb/users` | Critical | CWE-312 | 8.8 |
| F05 | OTP Brute Force — Zero Rate Limiting | High | CWE-307 | 8.1 |
| F09 | BOLA on `/mb/deposit-gateway` | High | CWE-639 | 8.0 |
| F10 | Auto-Slip Accepts Unvalidated GCS URLs | High | CWE-434 | 7.8 |
| F11 | Public GCS Bucket Contains Malware APKs | High | CWE-276 | 7.2 |
| F03 | Cache Flush DoS — Unauthenticated Backdoor | High | CWE-306 | 7.5 |
| F04 | Cross-Tenant OTP Flood (SMS Abuse) | High | CWE-400 | 7.3 |
| F15b | Firebase RTDB — Unauthenticated Write Access | High | CWE-306 | 7.0 |
| F16 | Admin Account Mass Enumeration via BOLA | High | CWE-639 | 6.8 |
| F12b | NoSQL Injection → Game Provider Secret Key Extraction | Medium | CWE-943 | 6.5 |
| F13 | Runtime Config Leak — Static API Key Exposed | Medium | CWE-200 | 6.1 |
| F12 | Firebase Anonymous Auth Enabled (Unauthenticated Access) | Medium | CWE-306 | 5.5 |
| F06 | CORS Wildcard (`Access-Control-Allow-Origin: *`) | Medium | CWE-942 | 5.3 |
| F14a | Floating-Point Precision in Financial Calculations | Low | CWE-682 | 3.1 |
| F15a | Unauthenticated Endpoint Data Exposure | Low | CWE-200 | 3.7 |

### Key Technical Findings

**F01 — Deposit Slip Forgery (Critical, CWE-345)**  
The platform accepts synthetic bank transfer slips without validating against KBank/SCB/KTB clearing networks. No OCR amount validation, no QR code verification against PromptPay network. Exploitation requires a player JWT and produces a deposit credited to the attacker's account.

**F08 — Cross-Tenant JWT Bypass (Critical, CWE-287)**  
JWT `cf` claim is not enforced against the API subdomain's tenant ID. A JWT issued for tenant A is accepted by tenant B's API, breaking the multi-tenant isolation model.

**F14b — BOLA: Backoffice Admin Endpoint (Critical, CWE-639)**  
`/bo/info/admin` and `/bo/info/provider` return full admin account lists and game provider configurations to any player JWT. 134 admin accounts and 62 provider records confirmed extracted.

**F12b — NoSQL Injection (Medium, CWE-943)**  
`/pb/latest-win` accepts MongoDB `$where` operator in query parameters, enabling arbitrary JavaScript execution in MongoDB context. 22 game provider `secret_key` values extracted using `$where=this.secret_key.length>0`.

**F11 — Public GCS Malware Distribution (High, CWE-276)**  
`gs://luxino-public/` is publicly readable and contains 6 Android APK files (`LuxSms-v2.apk`, `LuxSms-v3.apk`, `superAppSmsV1.apk`) that intercept banking SMS messages and forward to a C2 server.

### Disclosure Status

Full technical report (`reports/WE88Z-VAK88-2026-10-06-DRAFT.md`) and evidence artifacts have been prepared for coordinated disclosure to the platform operator. Disclosure timeline follows 90-day standard from assessment completion (2026-10-06 → 2027-01-04).

### Tools and Methodology

- Web API testing: custom Python scripts using `curl_cffi` with Chrome impersonation
- BOLA/IDOR discovery: manual endpoint enumeration + JWT manipulation
- NoSQL injection: parameter fuzzing with MongoDB operator variants
- APK analysis: static decompilation + dynamic C2 traffic analysis
- Infrastructure recon: GCS bucket enumeration, DNS history, certificate transparency
