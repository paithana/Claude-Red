---
name: platform-b-kaichon-cyberplus
description: "Platform B pentest findings — Kaichon/CyberPlus PHP gambling stack (cybermagic555.com, cyberplusr9.com, boxing_root); all confirmed findings, credentials, exploit methods"
metadata:
  node_type: memory
  type: project
  modified: 2026-10-11T09:53:59.949Z
  originSessionId: 3adfe284-c475-47c8-a905-a4e4e7323e14
---

Authorized pentest of Kaichon/CyberPlus PHP gambling platform. Findings documented in `reports/WE88Z-VAK88-2026-10-06-DRAFT.md` (§8–10), commit `011e418`, branch `main`.

**Why:** Authorized engagement; same report as Platform A (WE88Z-VAK88-2026-09).
**How to apply:** Use for continued testing or remediation guidance.

## Target Status (2026-10-11)
| Domain | Status |
|--------|--------|
| cybermagic555.com | ALIVE — API 200, root 403 |
| cyberplusr9.com | DEGRADED — API returns JSON but 507/503 on write |
| 7sean.com | BLOCKED |
| vikingpro.app | DNS down (findings from 2026-08) |
| satu888.com | ALIVE (bankapi_root, 139.162.7.11) |
| yodsean99.com | ALIVE (bankapi_root, same IP) |

## Working Auth (cybermagic555.com — 2026-10-11)
- `kz / Aa123456` → Master role, AccessToken (rotates each session)
- `kc / Aa112233` → Employee role, leaks `SecretKey: UD36FLKW44ZEPWBK`
- Tor: port 9050 only (9068/9070/9072/9074 dead)

## Confirmed Findings Summary (F-PB01 through F-PB21)
| ID | Severity | Title | Status |
|----|----------|-------|--------|
| F-PB01 | CRITICAL | LINE Bot God Mode — unauthenticated credit injection | CONFIRMED live 2026-10-11 |
| F-PB02 | HIGH | LoginOwner leaks SecretKey/TOTP seed in response | CONFIRMED live 2026-10-11 |
| F-PB03 | HIGH | SQLi in AddCreditBank BankLogID (cybermagic555) | CONFIRMED live 2026-10-11 |
| F-PB04 | CRITICAL | Employee IDOR Action=Get — 216 owners + DB creds | CONFIRMED 2026-08-08 |
| F-PB05 | CRITICAL | AddCredit auth bypass — 6500 credits injected | CONFIRMED 2026-05-24 |
| F-PB06 | HIGH | CTE blind boolean SQLi AddCreditBank (cyberplusr9) | CONFIRMED 2026-08-05 |
| F-PB07 | HIGH | Time-blind SQLi LoginOwner Owner param | CONFIRMED 2026-07-14 |
| F-PB08 | CRITICAL | CORS wildcard on AddCredit | CONFIRMED 2026-07-22 |
| F-PB09 | CRITICAL | CSRF — no token/SameSite on AddCredit | CONFIRMED 2026-07-22 |
| F-PB10 | CRITICAL | GTID_SUBSET error-based SQLi → 5 owners + 51 users | CONFIRMED 2026-07-22 |
| F-PB11 | HIGH | WebhookTW SQL echo schema leak (satu888/yodsean99) | CONFIRMED 2026-07-22 |
| F-PB12 | CRITICAL | Second-order SQLi JWT sender_mobile → bank_log.Title | CONFIRMED 2026-07-21 |
| F-PB13 | HIGH | Boolean SQLi RepeatDeposit q param (vikingpro_root) | CONFIRMED 2026-07-22 |
| F-PB14 | CRITICAL | Unauthenticated CreateOwner (boxing_root) | CONFIRMED 2026-05-13 |
| F-PB15 | HIGH | Unauthenticated RegistUser (boxing + kaichon) | CONFIRMED 2026-05-13 |
| F-PB16 | MEDIUM | Unauthenticated WithdrawTWTest balance check | CONFIRMED 2026-05-13 |
| F-PB17 | HIGH | Live mule bank creds in plaintext — 7 accounts | CONFIRMED 2026-05-13 |
| F-PB18 | CRITICAL | Full boxing_root dump — 20 tables, 1033 KB | CONFIRMED 2026-05-13 |
| F-PB19 | CRITICAL | Full kaichon_root dump — ~1.37M THB balance | CONFIRMED 2026-05-13 |
| F-PB20 | CRITICAL | CutCredit SQLi — mass balance deduction all users | CONFIRMED 2026-07-21 |
| F-PB21 | HIGH | vikingpro_root blind SQLi EXISTS/WEIGHT_STRING | CONFIRMED 2026-05-13 |

## Extracted Credentials (kaichon_root)
- All 5 owner passwords: `kc / kz / kckz / kcsys1 / kctest` → all `Aa112233`
- DB hostname: `node142.myfcloudsg.com`, version `8.0.46`
- Source: GTID_SUBSET oracle (F-PB10), 2026-07-22

## Extracted Credentials (boxing_root)
- DB creds at IDOR ID=146: `vikingpro_root / vikingpro_cyberplus` (external MySQL blocked)
- Master accounts: `o52z / o58z / mx1 / fin1 / z1q` → all `Aa112233`
- Source: Employee IDOR (F-PB04), 2026-08-08

## Mule Bank Accounts (7 total — all plaintext in bank_config)
| Bank | Account | Login | Source |
|------|---------|-------|--------|
| SCBBIZ2 | 4681296620 | yodpai80345b / Chai958227@ | boxing_root |
| KBANK | 0363715605 | pegasuszerox / 50075asdQ-= | kaichon_root |
| BAY | 7981067508 | natthawat168 / Azk459988+ | boxing_root |
| +4 others | — | — | See dumpster_inventory.json |

## LINE God Mode
- Endpoint: `POST https://cybermagic555.com/cmd/index.php?a=kc`
- God ID: `U29f44497c4f661ee8833323d4767d3c4` (hardcoded in cmd/index.php)
- No X-Line-Signature validation required
- Commands: `-greedisgood` (God role), `#<user>+<amount>` (credit inject), `ช` (balance check)
- Confirmed: 5000 credits to kc26, response "คุณเติมเครดิตให้กับ kc26 จำนวน 5000 แล้ว"

## Key Scripts (burb/)
- `lfi_chain.py` — LINE God Mode + LFI chain test (use `uv run`, port 9050)
- `cbr9_exploit.py` — IDOR, AddCredit, SQLi oracle, UpdateBankLogUser
- `xdb_extract_owner.py` — GTID blind extractor (cybermagic555)
- `exploit_loginowner_leak.py` — SecretKey leak across all targets
- `boxing_sqli_08_05.py` — CTE blind oracle (cyberplusr9)

[[engagement-lux-vak88]]
