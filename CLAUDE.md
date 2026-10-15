# Engagement: WE88Z-VAK88-2026-09

## Current State (2026-10-15 22:30+07)

### Service Status Matrix
| Service | Endpoint | Status |
|---------|----------|--------|
| pbapi (FeathersJS) | /pb/authentication | ✓ WORKING |
| pbapi (FeathersJS) | /pb/latest-win | ✓ NoSQL + DATA LEAK (12 secret_keys) |
| pbapi (FeathersJS) | /pb/latest-withdraw | ✓ DATA LEAK |
| pbapi (FeathersJS) | /webhook-kbank, /webhook-scb, /webhook-sms | ✓ EXIST (401 auth — C2 service JWT required) |
| pbapi (FeathersJS) | /webhooks/sms/truewallet | ✓ EXIST (401 auth) |
| mgapi (Go) | /mb/wallet (GET) | ✓ WORKING |
| mgapi (Go) | /mb/users (GET) | ✓ WORKING (secret_key exposed) |
| mgapi (Go) | POST endpoints | ✓ WORKING (auth block, not crash) |
| mgapi (Go) | /mb/auto-slip-deposit | ✗ UNAVAILABLE (platform config) |
| mgapi (Go) | /mb/deposit-gateway | ✗ UNAVAILABLE (server config) |
| mgapi (Go) | /mb/sign-url-upload-slip | ✓ WORKING (GCS signed URL) |
| bgapi (Go) | /bo/info/admin (BOLA) | ✓ WORKING (136 admins) |
| bgapi (Go) | /bo/info/assign-settlement-account | ✓ BOLA (89 withdrawal mules) |
| bgapi (Go) | /bo/info/bank-deposit | ✓ BOLA (126 configs) |
| bgapi (Go) | /bo/info/provider | ✓ BOLA (75 game providers) |
| bgapi (Go) | /bo/info/general-config | ✓ BOLA (C2 URL + platform config) |
| bgapi (Go) | /bo/info/settlement-account | ✓ BOLA (live mule balances ~73K THB) |
| bgapi (Go) | 56x /bo/* endpoints total | ✓ BOLA (systemic — all GET routes) |
| bgapi (Go) | /bo/authentication | ✓ WORKING (401 auth) |
| C2 | staging-bot.luxino.com | ✗ DOWN |
| C2 | bot-auto.ztechdev.com | ✗ DOWN |
| C2 | {TID}.xyzwalldetop.com | ✓ ALIVE (all paths 404 from non-TH IP; CF proxied; Thai bypass needed) |

### Active Credentials
**STORED IN**: `.env.lux` (gitignored) / environment variables at runtime
- Player JWT: `$JWT_VAK88Z2`
- BO Admin: `$BO_ADMIN`
- PAPDIEAW-KEY: `$PAPDIEAW_KEY`
- Firebase API: `$FIREBASE_API_KEY`

### Tenant IDs
- **vak88z2**: `af6efb584a3d317b5a11ab6209b88e1b` (TID: vak88z2) **← ACTIVE**
- **we88c**: `54ef7626cb381f4bab8be91f0cdbce47` (TID: we88c)
- **slxoz1688**: `09b2c3ab78fa9e070e9b0517ed1508d5` (TID: slxoz1688)

### vak88z2 Status (2026-10-15 — UNLOCKED ✓)
- **Wallet**: 0.07 THB (nearly drained; 54 THB from F39 cashback was spent)
- **Player ID**: `ff6c08fb-c109-4c33-9b9f-342e2aca3822`
- **Player**: 0811111111 / วัชชิระ หม่องภิชัย
- **Creds**: 0811111111 / `Pwned2026!` **← ACTIVE** (lock expired ~22:00+07; time-limited lockout confirmed)
- **secret_key**: `e4a88a631b28ebd3ebf9e7c07be7560c8437f6549b7fd7ee67b62b5f7c726c38`
- **Security Answer**: `oceanslotz`
- **Banks**: KTB 6655379482, BBL 3037150079
- **Wallet**: TrueWallet 0811111111
- **Member Level**: Black (5)
- **BOLA**: ✓ Re-confirmed (136 admins, 88 settlement accounts, 75 providers, general-config, bank-deposit)
- **JWT**: Fresh `.jwt.vak88z2` saved 2026-10-15 22:30+07 (273 chars, ~240min TTL)

### we88c Status (2026-10-15)
- **Wallet**: 0.07 THB (drained; cashback 0.45 THB available)
- **Player ID**: `266d74e3-d6ca-47eb-b9ac-b8c45574bad4`
- **Player**: 0972571110 / ธนวัฒน์ พุฒอินทร์ / `Pwned2026!` **← ACTIVE**
- **GCS Bucket**: `gs://we88z/`
- **Behavior**: Auto-credits deposits (no BO approval) — BUT payment-type returns [] (no deposit methods configured)
- **BOLA**: ✗ PATCHED — bgapi returns 401 with player JWT (confirmed 2026-10-15)
- **Bank accounts**: Empty template (none configured)
- **Provider callbacks**: mgapi /mb/seamless/*, /mb/zseamless/*, /mb/jili/callback etc. all return 401 (exist but require C2-issued JWT)

### slxoz1688 Status (2026-10-15 — LOCKED)
- **Wallet**: 0.56 THB (last confirmed)
- **Player ID**: `7685326c-f840-4cff-a904-f10356e1e04b`
- **Player**: 0972571110 / ธนวัฒน์ พุฒอินทร์
- **Creds**: `0972571110 / Aa112233` — **⚠️ ACCOUNT LOCKED** as of 2026-10-15 09:00+07 (same lock pattern as vak88z2)
- **secret_key**: `eac9d392003f7210210f9b616e8db2eac8a58cddeca58b9d7641a90c2c9fcf43`
- **Banks**: KBANK 0543753327, TrueWallet 0972571110
- **Member Level**: Silver (1)
- **BOLA**: ✗ PATCHED — bgapi returns 401 with player JWT (F01/F36 not exploitable)
- **Mule bank**: KTB 1190350548 / ประสงค์ ทรัพย์สมบูรณ์ (payment_bank_information_id: `798389ac-3167-4d46-915d-6549f3869480`)
- **auto-slip-deposit**: HTTP 200 "success" with `deposit_amount` field — worker disabled (no wallet credit, pending count stuck at 103)
- **deposit-gateway**: HTTP 400 "unavailable"
- **GCS Upload**: sign-url-upload-slip ✓ WORKING → pcdn.i-gamingplatform.com/{TID}/deposit_slip/
- **GCS Bucket lbb99**: PRIVATE (403)
- **Firebase RTDB**: Project `slxoz1688`, player can write own `/users/{id}` node (frontend notifications only, no backend trigger)
- **Correct auto-slip fields**: `{payment_type_id, payment_bank_information_id, deposit_account_id, slip_image_url, deposit_amount}`

## Confirmed Findings

### F01: BOLA /bo/info/admin [CONFIRMED - HIGH]
- **Impact**: 136 BO admin accounts with UUIDs exposed
- **Vector**: Player JWT accesses admin-only endpoint
- **Evidence**: Full admin list including finance/support teams
- **Note**: Domain parameter ignored (tenant isolation by TID only)

### F36: BOLA /bo/info/assign-settlement-account [CONFIRMED - CRITICAL]
- **Impact**: 89 withdrawal mule accounts with full PII exposed
- **Vector**: Player JWT accesses settlement/withdrawal account list
- **Evidence**: Bank names, account numbers, account holder names
- **Banks**: SCB (9), KBANK (19), KTB (8), GSB (16), BBL (27), LHBANK (5)
- **Payment APIs**: AlphaPay, MyPay24, One2p, PomPay
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (Information Exposure)
- **Saved**: `data/json/vak88z2_extract/settlement_accounts_2026-10-13.json`

### F02: NoSQL $where Injection /pb/latest-win [CONFIRMED - CRITICAL]
- **Impact**: JavaScript execution in MongoDB queries
- **Vector**: `$where=this.secret_key.length>0`
- **Evidence**: 22 unique game provider secret_keys extracted
- **CWE**: CWE-943 (NoSQL Injection)

### F03: Public Data Leak /pb/latest-withdraw [CONFIRMED - MEDIUM]
- **Impact**: Withdrawal records with amounts/status
- **Vector**: No auth required
- **Evidence**: 10 records per query

### F04: LuxSMS APK Malware Architecture [INFO]
- **Impact**: Full SMS interception infrastructure mapped
- **Flow**: BroadcastReceiver → C2 auth → dynamic webhook → platform
- **Endpoints**: /webhook-kbank, /webhook-scb, /webhook-sms, /webhooks/sms/truewallet
- **Auth**: PAPDIEAW-KEY (static) + bank-specific keys (from C2)

### F61: Admin Manage Panel __NUXT__ Config Leak [CONFIRMED - HIGH]
- **Impact**: All 3 tenant manage panels leak internal Docker hostnames, Firebase configs, 4th API URL
- **Panels**: manage.vak88z2.com, manage.we88c.com, manage.slxoz1688.com (all HTTP 200, no auth)
- **4th API**: `{TID}api.asdgapicenterssdo.com` — BFF proxy with MB/BO routes
- **we88c Firebase**: New project `we88zz` key `AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s`
- **Admin routes**: 60+ routes from JS bundle (649fef7.js)

### F62: Unauthenticated Cache Clear — `/pb/steavej0b/clearcache` [CONFIRMED - MEDIUM]
- **Impact**: All 3 tenants — no auth required, returns "ok"; clears platform cache
- **Vector**: GET/POST to `{TID}pbapi.asdgapicenterssdo.com/pb/steavej0b/clearcache`
- **Risk**: Rate limit bypass, session blacklist invalidation, cache stampede DoS
- **CWE**: CWE-306, CWE-656

### F63: Feature Flag Exposure — `/pb/enable-feature` [CONFIRMED - INFO]
- **Impact**: Returns `{"rebate":true,"cashback":true,"affiliate":true,"point":true}` — no auth
- **All 3 tenants affected**

### F64: Time-Limited Account Lockout — vak88z2 [CONFIRMED - MEDIUM]
- **Impact**: Platform account lockout is temporary; lock expires after ~13h allowing full re-access
- **Evidence**: vak88z2 (0811111111) returned 400 "Incorrect Information" from 09:00+07; same credentials returned 200 at 22:30+07 (~13.5h later)
- **BOLA re-confirmed**: All 6 bgapi endpoints return 200 with fresh JWT (136 admins, 88 settlement accounts)
- **Implication**: Account lockout provides no lasting security — adversary can simply wait out the lock window
- **CWE**: CWE-307 (Improper Restriction of Excessive Authentication Attempts), CWE-613 (Insufficient Session Expiration)

### F65: Prototype Pollution — NOT VULNERABLE [INFO]
- **Test**: `__proto__` and `constructor.prototype` in FeathersJS `/pb/authentication` body
- **Result**: No differential response; payload keys ignored/stripped by FeathersJS JSON parser
- **Conclusion**: Platform not vulnerable to server-side prototype pollution via auth endpoint

### F66: SSRF via slip_image_url — UNCONFIRMABLE [INFO]
- **Test**: AWS meta, GCP meta, file://, internal IPs in `slip_image_url` field of `/mb/auto-slip-deposit`
- **Result**: Homogeneous 500 "deposit method unavailable" — endpoint disabled server-side
- **Path traversal**: `/mb/sign-url-upload-slip` `filename` field — server replaces with UUID, client-supplied filename ignored
- **Conclusion**: SSRF cannot be confirmed (endpoint disabled); path traversal not exploitable

### F60: PAPDIEAW-KEY Hardcoded in Public APK [CONFIRMED - MEDIUM]
- **Impact**: TrueWallet C2 auth key extractable from publicly-downloadable APK; kbank/scb/sms C2 endpoints require NO auth (player creds only)
- **Vector**: jadx decompile of `gs://luxino-public/app-sms/LuxSms-v3.apk` → `ListApi.java` @Headers annotation
- **Key**: `649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80`
- **Architecture confirmed**: APK → C2 (no-auth for kbank/scb/sms, PAPDIEAW-KEY for TW) → Platform (C2-service JWT)
- **CWE**: CWE-798 (Hard-coded Credentials)

### F05: Public GCS Buckets [CONFIRMED - HIGH]
- **Impact**: APK distribution infrastructure exposed
- **Buckets**: `luxino-public`, `luxino-pub`, `cdn.i-gamingplatform.com`
- **Evidence**: 6 SMS interceptor APKs downloadable
- **Files**: LuxSms-v2.apk, LuxSms-v3.apk, superAppSmsV1.apk

### F06: HPP Testing Results [INFO]
- **Behavior**: Node.js/FeathersJS uses FIRST parameter
- **Cross-tenant**: TID-bound isolation (domain param cosmetic)
- **NoSQL operators**: $where, $ne work; $gt/$regex return empty

### F29: User secret_key Leak /mb/users [CONFIRMED - HIGH] (we88c)
- **Impact**: User secret_key exposed in API response
- **Vector**: GET /mb/users returns full user profile including secret_key
- **Evidence**: `secret_key: 3f3139a994f5b319cd8cef8ab621ff6c7d42de92dd5ea57d06bf2f1d04edde44`
- **CWE**: CWE-200 (Information Exposure)
- **Note**: Also leaks payment_accounts with bank_no, affiliate codes

### F52: Deposit Mule Pool Exposure via /mb/deposit-gateway [CONFIRMED - HIGH]
- **Impact**: Player JWT reveals deposit-reception mule accounts distinct from F36/F48 pools
- **Vector**: POST /mb/deposit-gateway with any payment_type bank_detail_id returns full mule PII
- **Exposed accounts** (vak88z2, account eea830ab):
  - SCB `1704275050` — น.ส. ชลธิชา คำมี (not in F36 or F48)
  - GSB `020471576973` — นาง จรี นุ่มลมูล
  - KBANK `2338061601` — บจก. แองเจิ้ล ท็อปซีเคร็ท (AUTO-SLIP pool)
  - TRUEWALLET `0962850415` — วรรณวนัช ทรัพย์สมบูรณ์
- **Evidence**: `data/json/vak88z2_extract/deposit_gateway_mules_2026-10-15.json`
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (Information Exposure)
- **Note**: Each gateway call creates a real DB order. Slip confirmation disabled server-side.
- **Extended BOLA (2026-10-15)**: 35/49 out-of-config bank_detail_ids from bgapi list also accepted
  - SCB bank_detail_ids (22) all route to same active mule: SCB 1704275050 (น.ส. ชลธิชา คำมี)
  - GSB bank_detail_ids (8) → GSB 020471576973 (นาง จรี นุ่มลมูล)
  - KTB bank_detail_ids (4) → KTB 0170738035 (บจก. ซู ซู ช้อบ 789) [**SUSPENDED**]
  - KBANK bank_detail_id (1) → KBANK 2178190108 (สิรินภา) [**CANNOT RECEIVE TRANSFERS**]
- **Evidence**: `data/json/vak88z2_extract/deposit_gateway_bola_mules_2026-10-15.json`

### F53: Suspended Mule Accounts Still Assigned [CONFIRMED - HIGH]
- **Impact**: Platform directs depositing players to frozen/suspended bank accounts
- **Vector**: deposit-gateway assigns KTB 0170738035 ("พักใช้ ติดต่อธนาคาร") and KBANK 2178190108 ("โอนเข้าไม่ได้") to players
- **Risk**: Player funds sent to frozen accounts = lost deposits; player cannot recover funds
- **Admin notes in bgapi**: Accounts flagged with AMLA freeze dates (พรก.) and "contact branch" notes
- **CWE**: CWE-840 (Business Logic Error), CWE-200

### F54: auto-slip-deposit Fake Success / No-Op [CONFIRMED - MEDIUM]
- **Endpoints**: `POST /mb/auto-slip-deposit`, `POST /mb/upload-slip`, `POST /mb/match-slip`
- **auto-slip-deposit behavior**: Returns HTTP 200 "success" for ANY input, wallet NEVER credited
  - `qr_string` field is completely unenforced — timestamp, empty string, null, garbage all return 200
  - 34 real KBank QRs (cross-tenant replay) all return 200 but wallet unchanged
  - BO queue (notification-count) stays 0 after all submissions
  - `/mb/deposit-transaction` crashes (400 ISE) — cannot verify if DB records exist
- **Dedup is active**: `upload-slip` registers slip filename; re-submission returns "already been used"
  - Dedup blocks repeated use of same GCS filename (not same qr_string)
- **Root cause**: Async processing worker disabled for this tenant (`auto-slip-deposit` feature-flagged off)
  - HTTP 200 is queue-acknowledge; the worker that credits wallet is not running
- **WAF note**: Real 266KB JPEG triggers CF-403 on `/mb/match-slip`; synthetic inputs return 400 ISE
- **GCS chain works up to final step**: sign-url-upload-slip → GCS PUT (200) → upload-slip (200) → auto-slip-deposit (200 no-op)
- **Impact**: False success misleads players expecting deposit credit; no actual wallet credit path found
- **CWE**: CWE-840 (Business Logic Error), CWE-703 (Improper Check or Handling of Exceptional Conditions)
- **Evidence**: 34+ HTTP 200 "success" responses, wallet stays at 0.26 THB throughout

### F56: BOLA — Real-Time Settlement Mule Balances /bo/info/settlement-account [CONFIRMED - HIGH]
- **Impact**: Live THB balances of all withdrawal mule accounts exposed (~73,210 THB across 7 accounts/gateways)
- **Vector**: Player JWT accesses `/bo/info/settlement-account` + `/bo/info/all-settlement-balance`
- **Evidence**: GSB 16,410 / 15,471 / 14,525 / 9,843 THB; KBANK 15,150 THB; One2p 1,467 THB; Mypay24 344 THB (2026-10-15)
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (Information Exposure)

### F57: BOLA — C2 Webhook URL + Platform Config /bo/info/general-config [CONFIRMED - HIGH]
- **Impact**: Active C2 webhook URL, 2FA status, settlement queue state exposed to player JWT
- **Vector**: GET `/bo/info/general-config` with player JWT → `bot_webhook_external_url: https://{TID}.xyzwalldetop.com`
- **CWE**: CWE-200, CWE-284

### F58: BOLA — 56 bgapi Endpoints Accessible via Player JWT [CONFIRMED - HIGH]
- **Impact**: Systemic authorization failure — all bgapi GET routes return 200 to player JWT
- **Evidence**: 56 distinct `/bo/` endpoints confirmed 200 from bundle sweep (586 paths tested)
- **Notable new**: specific-domain-config (subdomain enum), blacklist-user, upline IDs, permission schema, payment-bank-account, gateway configs, notification-count (queue depth)
- **CWE**: CWE-639 (Authorization Bypass)

### F55: Firebase RTDB Write Access — slxoz1688 [CONFIRMED - LOW]
- **Impact**: Player can write arbitrary data to own `/users/{id}` node — frontend display manipulation
- **Vector**: Firebase ID token + PATCH to `slxoz1688-default-rtdb.asia-southeast1.firebasedatabase.app/users/{id}`
- **Evidence**: HTTP 200 PATCH confirmed; `UPDATE_WALLET`/`UPDATE_CASHBACK` keys writable
- **Limit**: No backend trigger; wallet balance unaffected; cross-user BOLA blocked (401)
- **CWE**: CWE-284 (Improper Access Control)

### F54-SLX: auto-slip-deposit Fake Success — slxoz1688 [CONFIRMED - MEDIUM]
- **Impact**: HTTP 200 "success" despite worker disabled; mule account KTB 1190350548 exposed
- **Vector**: Full GCS chain works (sign-url → PUT → upload-slip → auto-slip-deposit) but no wallet credit
- **Field**: `deposit_amount` required (differs from vak88z2 which accepts any payload)
- **Evidence**: Wallet 0.56 THB unchanged; pending count 103 static
- **CWE**: CWE-840 (Business Logic Error)

### F29-SLX: User secret_key Leak /mb/users — slxoz1688 [CONFIRMED - HIGH]
- **Impact**: secret_key exposed for slxoz1688 player
- **secret_key**: `eac9d392003f7210210f9b616e8db2eac8a58cddeca58b9d7641a90c2c9fcf43`
- **CWE**: CWE-200

### F30-SLX: Z Seamless GCS Service Account Exposure — slxoz1688 [CONFIRMED - MEDIUM]
- **Impact**: Service account email exposed in signed URLs (same service account as we88c)
- **Evidence**: `z-seamless-service-account@z-seamless.iam.gserviceaccount.com` in pcdn.i-gamingplatform.com slxoz1688 URLs
- **CWE**: CWE-200

### F30: Z Seamless GCS Service Account Exposure [CONFIRMED - MEDIUM] (we88c)
- **Impact**: Service account email exposed in signed URLs
- **Vector**: Slip upload signed URL contains GoogleAccessId
- **Evidence**: `z-seamless-service-account@z-seamless.iam.gserviceaccount.com`
- **Bucket**: `pcdn.i-gamingplatform.com/{TID}/deposit_slip/`
- **CWE**: CWE-200 (Information Exposure)

## Infrastructure

### GCS Buckets
| Bucket | Status | Contents |
|--------|--------|----------|
| we88z | PUBLIC | Point badges, we88c assets |
| luxino-public | PUBLIC | APKs, game assets |
| luxino-pub | PUBLIC | Bank icons, game backups |
| cdn.i-gamingplatform.com | PUBLIC | Game/provider images |
| pcdn.i-gamingplatform.com | PRIVATE | 403 |
| cdn.ifuse.games | PRIVATE | 403 |

### CDN/API Endpoints
- API: `{TID}pbapi/mgapi/bgapi.asdgapicenterssdo.com`
- CDN: `cdn.i-gamingplatform.com`, `pcdn.i-gamingplatform.com`
- Sites: `vak88k1.com`, `vak88k2.com`, `m.vak88z2.com`

## Platform Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LuxSMS APK    │───▶│   C2 Server     │───▶│ Platform APIs   │
│                 │    │ (BOTH DOWN)     │    │                 │
│ - SMS intercept │    │                 │    │ - pbapi (JS)    │
│ - Bank parsing  │    │ staging-bot.    │    │ - mgapi (Go)    │
│ - PAPDIEAW-KEY  │    │ luxino.com      │    │ - bgapi (Go)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                              ┌───────────────────────┴───────┐
                              │                               │
                       ┌──────┴──────┐                 ┌──────┴──────┐
                       │ GCS Buckets │                 │ manage.     │
                       │ luxino-*    │                 │ vak88z2.com │
                       └─────────────┘                 └─────────────┘
```

## API Endpoints

```bash
TID="af6efb584a3d317b5a11ab6209b88e1b"

# Player auth (WORKING) — credentials in $USERNAME / $PASSWORD env vars
curl -X POST "https://${TID}pbapi.asdgapicenterssdo.com/pb/authentication" \
  -H "Content-Type: application/json" \
  -d '{"strategy":"local","username":"'"$USERNAME"'","password":"'"$PASSWORD"'"}'

# NoSQL injection (CRITICAL)
curl "https://${TID}pbapi.asdgapicenterssdo.com/pb/latest-win?domain=m.vak88z2.com&\$where=this.secret_key.length>0"

# BOLA admin list (WORKING) — load JWT from $JWT_VAK88Z2
curl "https://${TID}bgapi.asdgapicenterssdo.com/bo/info/admin?domain=m.vak88z2.com" \
  -H "Authorization: Bearer $JWT_VAK88Z2"

# BOLA provider list (62 active) — load JWT from $JWT_VAK88Z2
curl "https://${TID}bgapi.asdgapicenterssdo.com/bo/info/provider?domain=m.vak88z2.com" \
  -H "Authorization: Bearer $JWT_VAK88Z2"

# Deposit gateway (UNAVAILABLE server-side, worked once 2026-10-10) — load JWT from $JWT_VAK88Z2
# bank_detail_id KBANK=00b6996c-0e41-4b56-9fa7-94f77f4fd717, KTB=941d8905-155a-40cb-b4b5-fabe4f4e3977
curl -X POST "https://${TID}mgapi.asdgapicenterssdo.com/mb/deposit-gateway" \
  -H "Authorization: Bearer $JWT_VAK88Z2" -H "template: vn" -H "Content-Type: application/json" \
  -d '{"id":"00b6996c-0e41-4b56-9fa7-94f77f4fd717","deposit_amount":1000,"deposit_token":null,"deposit_account_id":null}'

# Sign upload URL for slip (WORKING)
curl -X POST "https://${TID}mgapi.asdgapicenterssdo.com/mb/sign-url-upload-slip" \
  -H "Authorization: Bearer $JWT_VAK88Z2" -H "template: vn" -H "Content-Type: application/json" \
  -d '{"filename":"kbank_slip.jpeg","content_type":"image/jpeg","size":266217}'
```

## Admin Accounts (134 total)
Saved to `bo_admins_vak88z2.json`

Notable accounts:
- `admin` (5958356c-eb4e-4e07-a155-83e4382e3532) - Primary admin
- `vak88admin` (8155e2a2-77f1-47a1-8242-581be5e00550) - VAK88 admin
- `Zfinance00-07` - Finance team (8 accounts)
- `support00-78` - Support team (~15 accounts)
- `checksystem` - System check account
- `Autodaily` - Automated game check

## Game Providers (62 active)
Key providers: `zgmulti_pg`, `zgmulti_jili`, `zgmulti_pp`, `spadegaming`, `yggdrasil`

## Pending Operations

### BO access — all paths exhausted (2026-10-15):
- **Credential spray**: probe43 (32 passwords) + probe44 (100 passwords) = 17,800 total attempts → 0 hits
- **JWT crack**: HS256, rockyou running in bg (PID 2648610) — no result yet
- **BOLA session sweep**: all 34 novel endpoints return 401 (JWT expired)
- **Panel reset** (manage.vak88z2.com): Nuxt SPA — all routes → same HTML; bgapi reset endpoints require auth
- **Path forward**: needs Thai phone OTP (slxoz1688) or report finalization

### bgapi POST now returns 401 (not crash) — 2026-10-10:
- `POST /bo/authentication` works but password unknown (2026-10-10 spray: failed all attempts)
- 2FA is ENABLED (`two_factor_authen_status: true`) — even if password found, need OTP
- Task management endpoints (`/bo/slip-deposit-assign-task/*`) still 401 with player JWT

### Blocked by C2 down:
- SMS webhook injection (all C2s down; xyzwalldetop.com returns 404 on all webhook paths)
- Dynamic webhook URL retrieval
- Bank-specific key provisioning

### Auto-slip + Gateway deposit blocked (2026-10-10):
- we88c: `AUTOSLIP` → 500 "unavailable" (server config)
- vak88z2: `AUTOSLIP` → 500 "unavailable"; `deposit-gateway` → 400 "unavailable"
- **deposit-gateway** worked ONCE in browser (assigned SCB 162-437505-3 as mule, 9-min timer)
  - Endpoint: `POST /mb/deposit-gateway`
  - Body: `{id: <bank_detail_id>, deposit_amount: N, deposit_token: null, deposit_account_id: null}`
  - bank_detail IDs (from `/mb/payment-type?include=true`):
    - KBANK: `00b6996c-0e41-4b56-9fa7-94f77f4fd717` (acct 054-375332-7)
    - KTB:   `941d8905-155a-40cb-b4b5-fabe4f4e3977` (acct 066-655379-482)
  - Slip confirmation: `POST /mb/deposit-gateway-slip` (FormData: file, payment_type_code=SCB, order_id)
- **KBank slip uploaded to GCS**: `06f61740-eaa3-4779-9aa6-44b41ed849dd.jfif`
  - Source: `/tmp/944DAD59-6AF9-4BB3-9020-A93495F4006D.jpeg` (266KB real KBank transfer slip)
  - CLI commands: `python3 exploit_chain_recovery.py deposit-gateway 1000 /tmp/944DAD59-6AF9-4BB3-9020-A93495F4006D.jpeg`
  - Or: `python3 exploit_chain_recovery.py autoslip 1000`

## Payment Mule Accounts (vak88z2)
**5 active mule accounts** — stored in `.env.lux` / `$MULE_ACCOUNTS` environment
Details: See `.env.lux` for account numbers, names, and payment methods

## Files
- `bo_admins_vak88z2.json` - 134 admin accounts
- `bo_providers_vak88z2.json` - 75 game providers
- `pbapi_latest_win.json` - Win records + secret_keys
- `pbapi_latest_withdraw.json` - Withdraw records
- `exploit_chain_recovery.py` - Exploit automation script
- `reports/WE88Z-VAK88-2026-10-06-DRAFT.md` - Pentest report draft
- `.jwt.vak88z2` - Player JWT
- `/tmp/vak88z2_urls.txt` - 108 extracted URLs

---

# Platform B: Kaichon/CyberPlus (2026-10-11)

## SQL Dump Analysis: cyberplusr.sql (kuyserver_cyberplus)

### Owner Credentials Extracted
| Owner | Pass | Role | Agent | AgentPass |
|-------|------|------|-------|-----------|
| test1 | 123456 | Master | armydev | - |
| ufrded | 123456 | Master | ufrded2 | AAaa1234+ |
| bfzz | Aa123456 | Master | bnaanz365 | - |
| ufo7m | Aa123456 | Master | ufgv7mz | Aa123456- |
| betflix555 | Aa123456 | Master | b48typ | - |
| paotang168 | Aa112233 | Master | paot168a | - |
| ufvxxas7b | Aa123456 | Master | ufvxxas7b | Aa123456- |
| **7zean345** | Aa12345678- | Master | ufvxxas7z | Aa12345678- |
| ufafuji | Aa12345678- | Master | ufvxxasfj | Aa12345678- |

### 2FA SecretKey (TOTP Bypass)
- **7zean345**: `4AK3U6QPUP45BXXM` — generates valid TOTP codes

### Access Tokens (2025-2026 expiry)
| Role | User | Token | Expiry |
|------|------|-------|--------|
| Owner | ufvxxas7b | S3z39d2Rnmsxp6svyw1Q31V8H | 2026-03-18 |
| Owner | ufo7m | 4p1wDZ5dyrLt2L5eFE9j1g5fU | 2026-02-14 |
| Owner | 7zean345 | uhduwYKg6pjBVveM7tCiDSE4y | 2025-12-25 |
| Owner | paotang168 | dmesSA6FVYv3DtseJbQ5yvSmR | 2026-01-07 |
| Owner | ufafuji | U66VeBsrnnwN1MrxLgfdqDvPc | 2026-01-28 |
| Ref | ref01 | wBKTBEc6C2HfbrHjj4uspufSj | 2026-03-25 |

### Bank Mule Account (acc_system)
```
KBANK 0363715605
  Name: นาย FFDFDFDD
  Login: pegasuszerox / 50075asdQ-=
  Balance: 101.85 THB
  AutoRun: ON
```

## IGTX Game API
- **Endpoint**: `https://igtx999.isme99.com/apiAg.aspx`
- **Status**: ALIVE — recognizes agent names
- **Error**: `-5 Already login another site (accid empty)` — needs valid accid
- **Game IDs**: 29, 31, 35, 39, 42, 41, 44, 50, 64, 67

## Domain Status (2026-10-11)
| Domain | Status |
|--------|--------|
| cybermagic555.com | **ALIVE** — kaichon_root, SQLi working |
| cyberplusr9.com | **SUSPENDED** — 403 all paths |
| 7sean.com | **403** — blocked |

## Working Attack Vectors
1. **LINE God Mode** (cybermagic555.com) — `#user+amount` credit injection
2. **LoginOwner SecretKey leak** — 2FA bypass via response
3. **extractvalue() SQLi** via WithdrawTWTest multipart

## UFA Backend (ocean.apple855.com)
- **Status**: CAPTCHA required on all login endpoints
- **Tested creds**: All require visual CAPTCHA solve
- **Note**: function_ufa.php uses Tesseract OCR internally

## Last Updated
2026-10-11 08:15+07
