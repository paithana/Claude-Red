---
name: reference-nuxt-workspace
description: Key paths and resources in the /home/kzp/nuxt pentest workspace
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6a666a59-03af-4e6c-b36a-6943fb3f33ae
  modified: 2026-09-16T20:20:29.694Z
---

**Engagement artifacts:**
- `/home/kzp/nuxt/.engage/weaponize/exploit-blueprint.md` — 5-chain exploit blueprint (live doc)
- `/home/kzp/nuxt/.engage/scope/scope.json` — ROE and in/out-of-scope targets

**Skills:**
- `/home/kzp/nuxt/.claude/skills/offensive-gambling-saas/` — confirmed TTPs for gambling SaaS (ATO, deposit forgery, webhook, backdoor, cross-tenant JWT)
- `/home/kzp/nuxt/.claude/skills/offensive-business-logic/SKILL.md` — general business logic methodology

**Session state:**
- `/home/kzp/nuxt/.remember/now.md` — current handoff note (updated each session via `/remember`)
- Background poll scripts in `/home/kzp/.claude/jobs/*/tmp/` — wallet monitoring

**Exploit scripts (root of workspace):**
- `wee88z_ato_exploit.py` — mass ATO for we88z
- `wee88z_deposit_final.py` — deposit forgery analysis
- `dep_nuxt.py`, `depflow.py` — deposit flow automation
