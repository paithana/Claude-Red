# Walt.io Bug Report Template

**Program:** Walt.io (HackerOne)  
**Researcher:** kzspy  
**Severity:** [Extreme / Critical / High / Medium / Low]  
**CVSS Score:** [x.x]  
**CWE:** [CWE-XXX]  

---

## Vulnerability Title
[Short, specific title — e.g., "BOLA on /api/wallets/{id} Allows Cross-User Balance Read"]

## Summary
[1–3 sentences: what is the vulnerability, what can an attacker do, what is the impact.]

## Severity Justification
[Why this deserves the severity you chose. Reference the Walt.io tier definitions where applicable.]

## Steps to Reproduce

**Prerequisites:**
- Account A: `[your test account]`
- Account B: `[second test account]`

**Steps:**
1. Authenticate as Account A. Note JWT/session token.
2. ...
3. Observe that response contains Account B's data.

**Request:**
```http
GET /api/endpoint HTTP/1.1
Host: api.walt.io
Authorization: Bearer <Account_A_token>
X-HackerOne-Research: kzspy

[body if applicable]
```

**Response:**
```json
{
  "user_id": "<Account_B_id>",
  ...
}
```

## Impact
[Concrete impact: what can an attacker do with this? Financial loss? PII exposure? Account takeover?]

## Evidence
- [ ] Screenshot of exploit
- [ ] HTTP request/response (sanitized)
- [ ] Video PoC (if complex)

## Remediation
[Specific fix recommendation.]

---
*All testing conducted manually. Header `X-HackerOne-Research: kzspy` included on all requests.*
