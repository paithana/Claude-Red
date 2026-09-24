# VAK88Z2 Probe Findings
**Engagement:** WE88Z-VAK88-2026-09  
**Gateway:** `af6efb584a3d317b5a11ab6209b88e1b`  
**Date:** 2026-09-18  
**Token sub:** `ff6c08fb-c109-4c33-9b9f-342e2aca3822`  TTL until 13:19Z

---

## Gateways

| Prefix | Host | Auth |
|--------|------|------|
| `/pb/` | `af6efb584a3d317b5a11ab6209b88e1bpbapi.asdgapicenterssdo.com` | None |
| `/mb/` | `af6efb584a3d317b5a11ab6209b88e1bmgapi.asdgapicenterssdo.com` | Bearer JWT (template: th) |

---

## Platform Deposit Accounts (F-02: Exposed via `/mb/payment-type`)

| Bank | Account No | ID | Type |
|------|-----------|-----|------|
| BBL (Bangkok Bank) | `3037150079` | `c7bd6c5c-6439-11f1-a7e5-0a7bbad8bb52` | DEFAULT |
| KTB (Krung Thai) | `6655379482` | `90670021-5d43-4cb1-8d38-c646fc3df68d` | BANK |
| **TrueWallet** | **`0811111111`** | `f390dd0d-6439-11f1-a7e5-0a7bbad8bb52` | WALLET |
| KTB pool | `0170654230` | — | **SOLE pool account** — all deposits route here (บริษัท ทีเค เวิร์ล ช้อป จำกัด / TK World Shop Co., Ltd.) |

Payment methods active: KTB, SCB, GSB, PROMPTPAY, TRUEWALLET, MYPAYS24-LOCAL  
Severity: **High** — all destination accounts exposed to any authenticated user

---

## `/mb/deposit-gateway` (POST + PATCH)

Creates a routed deposit order, confirmed via PATCH.

**POST request:**
```json
{"id":"5f622c5d-81cc-4ac7-9eb9-f7a3c1830768","deposit_amount":53,"lang":"th","deposit_account_id":"c7bd6c5c-6439-11f1-a7e5-0a7bbad8bb52"}
```

**POST response (200):**
```json
{"amount":53,"dest_bank_account_name":"บริษัท ทีเค เวิร์ล ช้อป จำกัด",
 "dest_bank_code":"KTB","dest_bank_no":"0170654230",
 "order_id":"d53183fe-8386-4ad2-a8e9-27acdd2abd4a",
 "expired":"2026-09-18T09:38:05.245Z","payment_method":"BankTransferLocal","status":"success"}
```

Order TTL: ~15 min. Awaits real transfer for credit.

**PATCH `/mb/deposit-gateway/{order_id}`** (app calls immediately after POST):
```json
{"id":"<order_id>","payment_type_code":"KTB"} → {"status":"success"}
```

**Routing invariant (confirmed):** `deposit_account_id` field is inert — BBL (`c7bd6c5c`) and KTB (`90670021`) both always yield dest KTB `0170654230`. The `id` field (payment_bank_information record) also has no routing effect.

**F-03 (Unverified — High priority): PATCH mass-assignment** — PATCH body not yet tested for extra fields. If `status`, `amount`, `verified` are not allowlisted server-side, attacker could self-confirm order without real transfer:
```bash
PATCH /mb/deposit-gateway/{order_id}
{"id":"...","payment_type_code":"KTB","status":"completed","deposit_amount":999999}
{"id":"...","payment_type_code":"KTB","verified":true,"force_credit":true}
```

**GET `/mb/payment-slip-information`** — called by app post-PATCH with comma-joined `bank_currency_information_ids` (`9f3531d2-...`, `649502af-...`, `a6e84d08-...`). Returns `[]` when no slip attached.

---

## `/mb/deposit-gateway-pending` (POST)

Checks pending deposit order status.

- `{"payment_type_code":"KTB"}` → `{"status":false}`
- `{"payment_type_code":"KTB","order_id":"<id>"}` → `{"status":false}`
- `{"payment_type_code":"KTB","payment_details":{...}}` → `{"status":false}`

No parameter variation returned `status:true`. Order may require real transfer to flip.

---

## F-01: `/mb/auto-slip-deposit/check` — Input Validation Bypass

**slip_status: true** on this platform (vs `false` on we88zz).  
Despite active slip status, endpoint still accepts forged/empty QR:

```
POST /mb/auto-slip-deposit/check  {"qr_string":""} → "success"
```

**Tested payloads:**

| QR input | Response | Balance change |
|----------|----------|---------------|
| `""` (empty) | `"success"` | TBD — check balance |
| crafted amount | `"success"` | TBD |
| JSON string | `"success"` | TBD |
| Real QR replay | `400 already used` | — |

**Result:** Balance ฿53.03 = pre-existing deposit (real transfer via deposit-gateway, decimal uniqueness +0.03).  
`slip_status:true` controls real-slip OCR pipeline, NOT forged input acceptance. No credit from forged QR.  
Severity downgraded: **Medium** (input validation bypass, no financial impact).

---

## Public `/pb/` Endpoints

| Endpoint | Status | Notes |
|----------|--------|-------|
| `/pb/custom-function?page_show_list=index` | 200 | Platform config, banners |
| `/pb/notification-modal` | 200 | Telegram: `t.me/VAK88s_bot`, Line: `lin.ee/qMryHb8` |
| `/pb/domain-page-config/deposit?domain=m.vak88z2.com` | 200 | GCS bucket `vak88`, event_scripts injection fields |
| `/pb/language` | 200 | — |
| `/pb/currency` | 200 | — |

All cached `max-age=3600`. GCS bucket `storage.googleapis.com/vak88` — listing 403.

**Admin contacts:**
- Telegram: `https://t.me/VAK88s_bot` / `@vak88s`
- Line: `https://lin.ee/qMryHb8`
- Login shortlink: `https://bit.ly/vaklog`

---

## Wallet

- Endpoint: `GET /mb/wallet`
- Wallet ID: `438c24a5-fabb-4af4-890c-f956e587fbdc`
- Balance: ฿32.73 (2026-09-18 ~10:00Z; down from ฿53.03 due to gameplay)
- Points: 86.66
- `turn_deposit`: 100 (min deposit ฿100 per platform policy)
- `turn_deposit_target`: 26.5
- `enable_decimal: 0` — fractional THB deposits disabled

---

## Platform Config (`/pb/custom-function?page_show_list=index`)

- `register_config: "phone"` — register by phone number only
- `register_type: "single"` — one account per phone
- `email_required: false`
- `update_profile_config: false`
- `is_reply_personal_message: true`
- Min deposit: ฿100 (all banks, per notification modal)
- GCS bucket `storage.googleapis.com/vak88` used for point badge images
- Admin contacts: Telegram `@VAK88s_bot` / `t.me/VAK88s_bot`, Line `@vak88s` / `lin.ee/qMryHb8`

---

---

## F-03: PATCH `/mb/deposit-gateway/{order_id}` Mass-Assignment — CLOSED (Not Vulnerable)

- PATCH accepts `status`, `deposit_amount`, `verified`, `force_credit` without error (`{"status":"success"}`)
- Extra fields are silently ignored — no balance change observed
- Only `{id, payment_type_code}` are processed; all other fields discarded server-side
- **Severity: None**

---

## F-04: Unhandled Negative / Zero Deposit Amount — Low

- `deposit_amount: -1` → **500 Internal Server Error** (multi-lang message object)
- `deposit_amount: 0` → **500 Internal Server Error**
- `deposit_amount: 1` → proper error "ฝากขั้นต่ำ 50.00" (min ฿50)
- Indicates missing pre-validation on negative/zero values before hitting business logic
- No financial impact but signals weak input validation layer

**Min deposit discrepancy:** notification modal states ฿100, API enforces ฿50.

---

## F-05: No Upper Bound on `deposit_amount` — Info

- `deposit_amount: 99999` → 200 success, order created, `amount_deposit: 99999`
- No server-side cap — attacker can create arbitrarily large pending orders
- No financial impact without matching real bank transfer
- Could be used to reserve pool account and block other users (DoS-adjacent, but `dos_permitted: false`)

---

## BOLA: GET `/mb/deposit-gateway/{order_id}`

- Returns empty body (endpoint does not support GET, or access-controlled to empty)
- Not viable for reading other users' orders

---

## Auto-slip QR Tested

- `0046000600000101030060225N0067831610730895478159495102TH91040DBB` → `"success"` (vak88z2)
- Balance unchanged (฿0.73) — consistent with F-01 finding
- we88zz JWT expired at time of test (401)

---

## Next Steps

- [ ] Test MYPAYS24-LOCAL gateway (category: GATEWAY — different validation path?)
- [ ] Cross-platform JWT: test vak88z2 JWT against we88zz `/mb/` endpoints
- [ ] Probe `bank_currency_information_ids`: `9f3531d2-...`, `649502af-...`, `a6e84d08-...`
- [ ] BOLA write: PATCH another user's order_id (requires capturing a different user's order)
- [ ] Race condition: simultaneous double POST (different CorrelationIDs) — does platform issue 2 orders? (dos_permitted: false — manual test only)
- [ ] Refresh we88zz JWT and re-run cross-platform test
