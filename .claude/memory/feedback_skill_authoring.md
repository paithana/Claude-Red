---
name: feedback-skill-authoring
description: "When confirming exploit chains, write them into the offensive-gambling-saas skill (or relevant skill) immediately — don't wait to be asked"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6a666a59-03af-4e6c-b36a-6943fb3f33ae
  modified: 2026-09-16T20:20:21.545Z
---

After confirming a new TTP in an engagement, author or update the relevant skill in `.claude/skills/` proactively — the user invokes `/writing-offensive-skills` to confirm this expectation.

**Why:** User treats confirmed findings as reusable intelligence; skills persist across sessions where engagement notes do not.

**How to apply:** On confirmation of a new technique (200 OK, balance change, successful takeover), create/update the skill reference and script. Follow writing-offensive-skills conventions: ≤180-line SKILL.md, references/ deep-dives, scripts/ runnable tooling, ATT&CK + CWE on every technique.

Relevant skill path: `/home/kzp/nuxt/.claude/skills/offensive-gambling-saas/` for gambling SaaS TTPs.
