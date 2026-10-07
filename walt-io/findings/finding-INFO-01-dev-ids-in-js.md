# [INFO] Developer Telegram IDs Hardcoded in Client-Side JavaScript

**Program:** Walt.io (HackerOne)  
**Researcher:** kzspy  
**Severity:** Informational  
**CVSS Score:** 0.0 (no direct exploitability)  
**CWE:** CWE-615 (Information Exposure Through Comments)  
**Status:** [INFO] — no exploitable impact without privileged access  

---

## Finding

The Walt.io web app (`walletbot.me`) contains a hardcoded allowlist of Telegram user IDs in client-side JavaScript that enables `appdebug` mode. These IDs belong to internal developers/staff.

**File**: `https://walletbot.me/static/js/app.b8f7999214.js`

**Code snippet** (minified, from bundle):
```javascript
return y()?.startsWith("appdebug") && !!e?.id && 
  [456401, 167654279, 5317744882, 7572185079, 520637635, 76448586,
   1247695932, 56385792, 280251525, 6912598872, 6951839816, 246993787,
   7578960231, 9208155, 127014428, 31366184, 22338948, 114400088,
   7794837372, 1597447129, 481175323, 7431589169, 7508783262, 432438204,
   80771003, 649797243, 550608692].includes(e.id)
```

**Debug mode activation**: Navigate to `https://t.me/walt?startapp=appdebug`

## Impact

- 27 Telegram user IDs of internal staff are publicly enumerable
- Each ID can be reverse-looked-up via Telegram to identify staff members (social engineering surface)
- Debug mode (Eruda console) is activated for these accounts — unclear if debug mode exposes additional attack surface without one of these accounts
- Not directly exploitable without possessing one of these accounts

## Evidence
- Confirmed by fetching `https://walletbot.me/static/js/app.b8f7999214.js` (2026-10-07)
- IDs listed above

## Remediation
- Move debug-user allowlist to server-side (environment config or database)  
- Debug mode activation should be controlled server-side, not client-side
- Consider server-sent feature flags instead of hardcoded user IDs

---
*Testing conducted manually. Header `X-HackerOne-Research: kzspy` included on all requests.*
