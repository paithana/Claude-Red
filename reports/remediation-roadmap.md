# Remediation Roadmap
## asdgapicenterssdo.com Multi-Tenant Gambling SaaS

**Report Date:** 2026-09-24

---

## Immediate Actions (0–48 hours)

These actions can be taken without code changes and stop active exploitation.

### P0-A: Remove Developer Backdoor [F03]
```bash
# Find and remove all instances of the steavej0b route
grep -r "steavej0b" /path/to/backend/src/
# Delete the route handler and restart all API instances
```
**Impact:** Eliminates unauthenticated DoS vector. Zero code risk.

### P0-B: Add OTP Rate Limiting [F05]
Add at the API gateway or middleware level:
```javascript
// FeathersJS hook — before otp-verified
app.service('pb/otp-verified').hooks({
  before: { create: [rateLimit({ max: 5, window: '60s', key: req => req.body.phoneNumber })] }
});
```
**Impact:** Raises ATO cost from 88 minutes to computationally infeasible.

### P0-C: Remove Sensitive Fields from /mb/users Response [F02]
```javascript
// FeathersJS service hook — after find/get
sanitizeUser: (context) => {
  const sensitiveFields = ['secret_key', 'answer', 'bank_no', 'password'];
  context.result.data = context.result.data.map(u => {
    sensitiveFields.forEach(f => delete u[f]);
    return u;
  });
}
```
**Impact:** Eliminates 2FA seed exposure and data leak.

### P0-D: Revoke and Rotate Secrets [F13]
1. Rotate `PAPDIEAW-KEY` (current: `649e854e...`) immediately
2. Regenerate Firebase API keys for all tenant projects
3. Rotate all HMAC webhook secrets
4. Remove APKs from `gs://luxino-public/` and set bucket to private

---

## Short-term Fixes (1–4 weeks)

### P1-A: Enforce cf Claim Validation [F08]
```javascript
// Backend middleware — validate tenant isolation
const validateTenant = (context) => {
  const jwtTenant = context.params.user?.cf;
  const requestTenant = extractTenantFromHost(context.params.headers?.host);
  if (jwtTenant !== requestTenant) {
    throw new Forbidden('Cross-tenant access denied');
  }
};
// Apply to ALL mgapi service hooks
```

### P1-B: Add Ownership Check on PATCH Endpoints [F09]
```javascript
// Before PATCH /mb/deposit-gateway/:id
const checkOwnership = async (context) => {
  const record = await context.service.get(context.id);
  if (record.user_id !== context.params.user.sub) {
    throw new Forbidden('Access denied');
  }
};
```

### P1-C: Replace CORS Wildcard [F06]
```javascript
// Express middleware
const corsOptions = {
  origin: (origin, callback) => {
    const allowed = [`m.${process.env.TENANT_DOMAIN}`, `manage.${process.env.TENANT_DOMAIN}`];
    callback(null, allowed.includes(origin));
  }
};
```

### P1-D: Disable Firebase Anonymous Auth [F12]
1. Go to Firebase Console → Authentication → Sign-in providers
2. Disable "Anonymous" for each project: vak88z, we88z, slxoz1688
3. Add Firebase App Check to prevent API key abuse

### P1-E: Integrate Bank API Deposit Validation [F01/F10]
Priority integration order:
1. **PromptPay** — Thai QR Payment clearing network callback (free, immediate)
2. **KBank Open API** — `/v1/transaction/{txRef}` validation
3. **SCB API** — transaction reference check

Minimum viable fix:
```python
# Before crediting any deposit
def validate_deposit(slip_ref: str, amount: float, bank: str) -> bool:
    if bank == 'KBANK':
        return kbank_api.verify_transaction(slip_ref, amount)
    elif bank == 'SCB':
        return scb_api.verify_transaction(slip_ref, amount)
    # Reject if bank API unavailable rather than auto-approve
    raise Exception("Bank API unavailable — deposit held for manual review")
```

---

## Long-term Strategic Improvements (1–6 months)

### P2-A: Real-time Payment Confirmation [F01]
Replace slip-upload model with PromptPay callback:
- Register PromptPay merchant account
- Receive real-time credit notifications via webhook
- Auto-approve deposits only when PromptPay confirms payment
- Eliminate slip forgery attack surface entirely

### P2-B: Database-Level Tenant Isolation [F08]
- Migrate to separate MongoDB databases per tenant
- Or add mandatory tenant_id field to all collections with compound indexes
- Enforce at ORM/ODM level, not application level

### P2-C: Decimal Arithmetic [F14]
```javascript
// Replace all financial calculations
const Decimal = require('decimal.js');
const result = new Decimal(rebate_total).plus(new Decimal(cashback)).toFixed(2);
```

### P2-D: Secret Management Infrastructure [F13]
- Deploy HashiCorp Vault or AWS Secrets Manager
- Remove all secrets from environment variables and JavaScript bundles
- Implement secret rotation with zero-downtime deployment

### P2-E: Conduct Follow-up Penetration Test
After implementing P0 and P1 fixes, engage a third-party security firm to validate:
- OTP rate limiting effectiveness
- Tenant isolation correctness
- CORS policy enforcement
- Bank API integration security

---

## Quick Wins vs Long-term Matrix

| Fix | Effort | Impact | Timeline |
|-----|--------|--------|---------|
| Remove `/steavej0b/clearcache` | 15 min | High (DoS eliminated) | Today |
| Rotate secrets | 1 hour | High (C2 re-auth blocked) | Today |
| Set GCS bucket private | 5 min | High (malware distribution stopped) | Today |
| Add OTP rate limiting | 2 hours | Critical (ATO prevented) | This week |
| Strip sensitive fields from API | 2 hours | Critical (2FA exposure fixed) | This week |
| Add cf claim validation | 1 day | Critical (tenant isolation) | This week |
| Add ownership checks | 2 days | High (BOLA fixed) | 2 weeks |
| Bank API integration | 2-4 weeks | Critical (deposit forgery fixed) | 1 month |
| PromptPay merchant | 1-3 months | Critical (eliminates F01 entirely) | 3 months |
