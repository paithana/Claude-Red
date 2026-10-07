# Walt.io Bug Bounty — Engagement Notes

**Program:** https://hackerone.com/walt_io  
**Platform:** Telegram crypto wallet (TON blockchain)  
**Test app:** https://t.me/walt  
**Researcher:** kzspy  

## Bounty Table

| Tier | Range |
|------|-------|
| Extreme | $30,000 – $100,000 |
| Critical | $3,000 – $29,999 |
| High | $500 – $3,000 |
| Medium | $200 – $500 |
| Low | $100 – $200 |

## Required Header (ALL requests)
```
X-HackerOne-Research: kzspy
```

## Test Account Setup
1. Sign up at https://t.me/walt with Telegram account
2. Set recovery email to `kzspy@wearehackerone.com` in TON Space settings

## SLA
- First response: 2 days (actual avg 19h)
- Triage: 10 days (actual avg 1d 18h)
- Bounty: 14 days (actual avg 5d 7h)

## Key Out-of-Scope
- DoS / rate limiting on non-auth endpoints
- CORS, missing headers, SSL config
- UI/UX bugs without security impact
- Open redirect without chained impact
- **AI agents prohibited from scanning** — manual testing only

## High-Value Target Classes
- Extreme: wallet fund withdrawal without auth
- Critical: RCE, full wallet compromise, bulk PII
- High: privilege escalation, cross-user data access, BOLA

## Notes
- Gold Standard Safe Harbor (strong legal protection)
- 97% response rate — active program
- Private program — no public disclosure
