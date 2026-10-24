---
name: project-cloudflare-account-sites
description: "kzp's Cloudflare account fda04665 holds several Khao Lak sites; three still auto-inject the Web Analytics beacon pre-consent, and khao-lak.net was down (521) on 2026-09-19"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2f71ff02-c8af-4bfa-85b2-148d826884c3
  modified: 2026-09-19T11:43:14.780Z
---

Cloudflare account `fda04665362efb5ecdaabe78743fa589` (Thanawatpootin@gmail.com)
carries at least four zones with Web Analytics sites: hotelkhaolak.com,
khao-lak.net, khaolaktrips.com and southerntourthailand.com. The second account
shown by the MCP connector (Info@khaolaklanddiscovery.com,
`0ec04f23485e82ad28da7e4c5ad8141e`) returns an authentication error with the
current token, so its zones cannot be read from a session.

On 2026-09-19 hotelkhaolak.com's beacon was switched off (zone RUM `manual`
plus `auto_install: false` — the zone toggle alone does not stop the
injection, and the edge takes minutes to catch up). **The other three still
have `auto_install: true`**, so each injects
`static.cloudflareinsights.com/beacon.min.js` into every browser-shaped HTML
response before any consent banner runs. If any of them ever needs the same
compliance treatment, that is the change, and it is invisible to a bare `curl`
— fetch with a browser User-Agent and `Accept: text/html`.

Noticed in passing the same day: **khao-lak.net answered 521**, i.e. Cloudflare
could not reach its origin. Nobody was asked to look at it, so it may still be
down.

See [[cloudflare-zerotrust-state]] for Zero Trust state on kzp's
other zone.
