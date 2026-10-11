# AGENTS.md — claude-red Engagement

## Active Agents (`.claude/agents/`)

| Agent | Role |
|-------|------|
| **`kzp`** | Primary pentest agent — Platform A (we88c/vak88z2) + Platform B (Kaichon/CyberPlus). Entry point for all engagement work. |
| `finding-checker` | Blind adversarial checker — refutes findings before `[CONFIRMED]` |
| `finding-validator` | Exploitability judge — PASS / KILL / DOWNGRADE / CHAIN-REQUIRED |
| `exploit-researcher` | CVE lookup, PoC research, attack chain mapping |
| `security-reviewer` | OWASP / MITRE / CWE audit pass |
| `network-analyst` | Packet/protocol analysis, IDS rule creation |
| `redteam-planner` | Attack path design, C2 infrastructure, OPSEC |
| `reverse-engineer` | Binary/APK analysis, decompilation, protocol RE |
| `ai-researcher` | ML model analysis (if needed) |

---

## Key Skills (`/offensive-claude:*`)

### Discipline (run before any action)
| Skill | When |
|-------|------|
| `/offensive-claude:scope-discipline` | Before touching any target — confirm in-scope |
| `/offensive-claude:finding-discipline` | Before recording `[CONFIRMED]` |
| `/offensive-claude:opsec-discipline` | Before outward action |
| `/offensive-claude:engagement-flow` | Full kill-chain orchestration |

### Domain (by current targets)
| Skill | Relevant to |
|-------|-------------|
| `/offensive-claude:web-pentest` | pbapi/mgapi/bgapi endpoints |
| `/offensive-claude:offensive-sqli` | Platform B Kaichon SQLi |
| `/offensive-claude:offensive-idor` | BOLA findings (F01, bgapi) |
| `/offensive-claude:offensive-business-logic` | Deposit/credit injection |
| `/offensive-claude:offensive-race-condition` | Balance manipulation |
| `/offensive-claude:offensive-jwt` | JWT HS256 analysis |
| `/offensive-claude:mobile-pentest` | LuxSMS APK RE |
| `/offensive-claude:offensive-api-abuse` | Rate bypass, quota exhaustion |
| `/offensive-claude:offensive-waf-bypass` | Platform B Monarx / BlockSQLInject |
| `/offensive-claude:offensive-reporting` | Evidence handling, disclosure |

---

## Current Engagement

**Report**: `reports/WE88Z-VAK88-2026-10-06-DRAFT.md` (commit `011e418`)

**Platform A** — we88c (PRIMARY), vak88z2 (ACTIVE)
- Auth: `uv run probe_we88c_pbapi_auth.py` → `.jwt.we88c`
- Creds in `.env.lux` (`source .env.lux`)

**Platform B** — cybermagic555.com (`kaichon_root`)
- LINE God Mode, GTID SQLi, TOTP bypass (7zean345 / `4AK3U6QPUP45BXXM`)

**Scope**: `scope.json` — do NOT add `royalflush888.com`

---

## graphify

Rules:
- Before architecture questions, read `graphify-out/GRAPH_REPORT.md`
- After modifying code files, run `graphify update .`
