# Memory Index (Consolidated)

## Pentest (Platform A/B)
- [Engagement: WE88Z-VAK88-2026-09](engagement_lux.md) — Platform A (Luxino/vak88z); **133 findings** (F01–F133, F130 retracted); report at `reports/WE88Z-VAK88-2026-10-06-DRAFT.md`; F133: LuxSms-v3 APK full SMS exfil architecture; active 2026-10-23
- [Platform B: Kaichon/CyberPlus](platform_b_kaichon.md) — 21 confirmed Platform B findings (F-PB01–F-PB21); LINE God Mode, GTID SQLi, full DB dumps, mule creds; cybermagic555.com alive
- [Platform Architecture](platform_sms_intercept.md) — 3-platform SMS intercepter architecture (LUX/UFA/CTMX); attack flows per platform
- [Feedback: Worktree Bash Restrictions](feedback_worktree.md) — Complex heredoc/inline Python blocked in worktree isolation; write scripts to scratchpad first
- [EMVCo2 / Thai QR Format](EMVCo2_ref.md) — KBANK QR format decoded: 59-char, CRC-16/CCITT confirmed, ts9 structure, replay attack results
- [CVE-2026-87902 rs24hr](cve_2026_87902_rs24hr.md) — WordPress page-template LFI; rs24hr not exploitable (Bricks theme + Cloudflare WAF)
- [Auth: pb/authentication local strategy](feedback_auth_local_strategy.md) — Use `username` field (not `phone`) for strategy:local on pbapi; bypasses mgapi auth crash; 240min JWT
- [Domain Change: wee88z → we88c.com](domain_change_wee88z_we88c.md) — Tenant migration 2026-10-07; TID unchanged, infrastructure impact TBD

## Home/Cloudflare
- [Cloudflare Zero Trust state](project_cloudflare_zerotrust_gap.md) — kz/kzvnc/kzssh/rea.thinkweb.me behind owner-only Access + origin JWT checks; exposed API token still active (2026-10-18)
- [Cloudflare account sites](project_cloudflare_account_sites.md) — three of kzp's other zones still inject the Web Analytics beacon before consent; khao-lak.net was 521 on 2026-09-19
- [Ship proven fixes immediately](feedback_ship_immediately.md) — offer merge-and-deploy, not a commit or a PR, once a change is verified
- [remember plugin v0.33.0 restored](project_remember_plugin.md) — reinstalled 2026-09-22 after being broken; session memory capture is working again

## Nuxt
- [User profile](user_profile.md) — offensive security researcher, red team operator, Python/web/API, Kali workstation
- [Execution style](feedback_execution_style.md) — autonomous proactive execution; skip plan mode; confirm only destructive irreversible actions
- [Skill authoring](feedback_skill_authoring.md) — write confirmed TTPs into .claude/skills/ immediately after confirmation; follow writing-offensive-skills conventions
- [Nuxt workspace reference](reference_nuxt_workspace.md) — key paths: exploit-blueprint.md, .engage/, .remember/now.md, offensive-gambling-saas skill
