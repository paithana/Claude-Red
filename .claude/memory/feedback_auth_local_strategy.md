---
name: feedback-auth-local-strategy
description: pb/authentication uses username (not phone/phoneNumber) field for strategy:local on asdgapicenterssdo.com platform
metadata:
  node_type: memory
  type: feedback
  originSessionId: 37429e79-31e3-46f6-85ec-59c8af804bdc
  modified: 2026-10-05T23:37:25.749Z
---

`/pb/authentication` `strategy:local` requires `username` field (not `phone` or `phoneNumber`).

**Why:** Tried all field variations — only `{"strategy":"local","username":"<phone>","password":"<pw>"}` returns a JWT. `phone` and `phoneNumber` return 400 "Incorrect Information".

**How to apply:** When authenticating to pbapi on asdgapicenterssdo.com platform with `strategy:local`, always use `username` as the phone field name. This bypasses the mgapi total auth crash since pbapi is a separate service. Works even when mgapi `/authentication` crashes with "Internal Server Error".

Example:
```
POST /pb/authentication
{"strategy":"local","username":"0811111111","password":"Pwned2026","domain":"m.vak88z2.com"}
→ {"accessToken":"...", "thrillToken":"...", "expire_in":"240m"}
```

Auth crash isolation: mgapi/bgapi `/authentication` crash (401 "Internal Server Error") does NOT affect pbapi `/pb/authentication`. pbapi issues JWTs independently.
