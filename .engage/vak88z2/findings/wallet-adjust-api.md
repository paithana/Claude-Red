# VAK88Z2 Wallet Adjustment API

**Finding ID:** VAK88Z2-ADJUST-001  
**Date:** 2026-10-28  
**Status:** [POSSIBLE] — JWT expired, needs fresh auth to test

## API Endpoints

### GET Balance View
```
GET /bo/member-adjust-wallet/{user_id}
Authorization: Bearer <jwt>
```
Returns: `SET_ADJUST_VIEW_DATA` — current wallet state

### POST Balance Adjustment
```
POST /bo/member-adjust-wallet
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "user_id": "<target_user_id>",
  "adjust_amount": 500,           // positive = credit, negative = debit
  "adjust_remark": "test",
  "slip_image_url": "",           // optional receipt image
  "incl_report": 0,               // 0 = exclude from reports, 1 = include
  "slip_datetime": "",            // optional timestamp
  "user_payment_account_id": "",  // optional payment account ref
  "tx_id": "",                    // optional transaction ID
  "crypto_token": ""              // optional crypto token ref
}
```

## Vuex State Shape (adjust_form)
```javascript
{
  username: "",
  user_id: "",
  include_report: "",      // 0 or 1
  before_balance: "",      // pre-adjust balance
  adjust_amount: "",       // delta (+/-)
  after_balance: "",       // computed post-adjust
  adjust_remark: "",
  image_file: null,
  is_adjust_config: false,
  adjust_config: {},
  slip_datetime: "",
  user_payment_account_id: "",
  tx_id: "",
  crypto_token: "",
  bank_code: "",
  tax_amount: 0,
  actual_adjust_amount: 0
}
```

## Related Routes
| Route | Purpose |
|-------|---------|
| `/report/adjust-user-wallet` | View adjustment history |
| `/deposit/all-deposit/adjust-transaction` | Deposit adjustments |
| `/member/adjust-free-spins/management` | Free spin credits |

## Batch Import Endpoints
```
/bo/batch-import-wallet-adjust-balance  — bulk CSV import
/bo/batch-import-adjust-freespin        — bulk free spin import
```

## Test Requirements
- Fresh JWT with backoffice access
- Valid user_id target
- Permission: likely MODULE_MEMBER_ADJUST_WALLET or similar

## Auth Attempts (2026-10-28)
- Firebase refresh token → ID token: **SUCCESS** (user ff6c08fb)
- ID token → `/bo/authentication`: **FAIL** (401 - user may be disabled)
- Direct creds `0811111111:Pwned2026!` via web: **FAIL** (Error - invalid creds)

## External API Endpoints Discovered
```
ex_api_url:    https://af6efb584a3d317b5a11ab6209b88e1bapi.asdgapicenterssdo.com
ex_api_url_bo: https://af6efb584a3d317b5a11ab6209b88e1bbgapi.asdgapicenterssdo.com (Go)
ex_api_url_pb: https://af6efb584a3d317b5a11ab6209b88e1bpbapi.asdgapicenterssdo.com (public)
```

## Notes
- `incl_report: 0` may hide adjustment from standard reports
- Exchange rate conversion shown for certain bank_codes
- Tax calculation path exists for some adjustments
