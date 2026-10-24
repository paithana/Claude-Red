---
name: feedback-ship-immediately
description: "kzp wants proven fixes merged and deployed straight away — offer the deploy, do not stop at a commit or a PR"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2f71ff02-c8af-4bfa-85b2-148d826884c3
  modified: 2026-09-19T11:43:16.487Z
---

Across one long session on hotelkhaolak.com (2026-09-18/19) kzp chose the
shipping option every time it was offered: "merge back to master locally", then
"push master now — deploys", then "merge and deploy now" for the flights fix,
then "turn it off now" for a Cloudflare zone setting. A draft PR left for review
was merged within the hour instead.

**Why:** the point is a working production site, not a tidy branch. Leaving a
verified fix sitting on a branch reads as unfinished work, and a PR that only
Claude has read adds a step without adding a reviewer.

**How to apply:** when a change is proven — tests green, behaviour measured —
offer merge-and-deploy as the first option rather than ending at a commit, and
say plainly what the deploy publishes. Still ask once per deploy: each is a
separate outward-facing action, and this preference is not standing
authorisation. Exception worth keeping: legal or public-facing copy that a
human has not read is worth flagging in the same breath, because kzp will
deploy it anyway and should know what goes out.

Related: [[project-cloudflare-account-sites]] — the beacon switch-off is one of
the changes shipped this way.
