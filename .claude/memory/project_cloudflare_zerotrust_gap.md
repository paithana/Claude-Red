---
name: cloudflare-zerotrust-state
description: kzp-net Zero Trust state 2026-10-18 — kz/kzvnc/kzssh/rea.thinkweb.me now behind owner-only Access apps with cloudflared origin JWT checks; driver public by choice; exposed CF API token still active
metadata:
  node_type: memory
  type: project
  originSessionId: 3b5e4db0-fe21-4892-b9e9-ba08a6045cf1
  modified: 2026-10-18T12:36:08.284Z
---

Re-verified through the Cloudflare API on 2026-10-18. Account
`fda04665362efb5ecdaabe78743fa589`, Access team `thinkweb`
(`thinkweb.cloudflareaccess.com`); the only identity provider is One-time PIN.

Tunnel `kzp-net` (`21c3a7f5-39f5-49d8-aa5f-2a369a656762`) is locally managed:
`~/.cloudflared/config.yml`, run by `cloudflared.service`. It does **not**
hot-reload, so an ingress edit needs `sudo systemctl restart cloudflared`, which
drops every tunnel hostname (live VNC/SSH included) for about 5 s.

| Hostname | Origin | Access (all self_hosted, OTP only, 24h) |
|---|---|---|
| kz.thinkweb.me | nginx `kzp` :80 → Webmon :8899 (502 on 2026-10-18), `/vnc/`, `/ssh/` ttyd | app `kz` (2f44849f…, AUD 4e444103…) |
| kzvnc.thinkweb.me | noVNC :6080 | app `kzvnc` (24b89b47…, AUD 73d24792…) |
| kzssh.thinkweb.me | ssh 192.168.78.254:22, clients use `cloudflared access ssh` | app `kzssh` (0406b536…, AUD 6141dca3…) |
| rea.thinkweb.me | nginx `rea` 127.0.0.1:80 → /var/www/rea (REA report) | app `rea` (feb425bb…, AUD ded66c07…) |
| dev.hotelkhaolak.com | nginx → next dev :3000 | app `dev`, policy `Warp` (device posture only) |
| driver.thinkweb.me | nginx `driver` | none, public by choice |

kz, kzvnc, kzssh and rea all use the reusable policy `Owner only
(thanawatpootin@gmail.com)` (989292de…, one email), and every protected rule in
config.yml carries `originRequest.access {required, teamName: thinkweb, audTag}`,
so cloudflared fails closed if an app is deleted.

Hazards found on 2026-10-18:
- `CF_API_TOKEN` in `~/.config/cloudflare-secrets.sh`, which that file itself
  marks compromised since 2026-08-13, is still **active**. It is user-owned and
  can create and edit Access policies, apps and service tokens, so a holder could
  add an email to the owner policy and get into all four hosts. It cannot read
  zones, audit logs or its own token record, so it cannot roll itself.
- Policies `kzp`, `kz`, `thinkweb`, `Thanawat Poot-in` and `Allow main email`
  include `any_valid_service_token`, so the exposed `CF_KZ_CLIENT_ID/SECRET`
  service token would pass them. Use an email-only policy for new apps.
- About 31 other reusable policies exist and most are orphaned (`app_count` 0).
- sshd accepted 21 password logins via the tunnel in the 30 days to 2026-10-18;
  WARP private-network routing to 192.168.78.0/24 is not gated by these apps.
- cloudflared 2026.10.1 reports `warp-routing.enabled` as an unused key.

**Why:** a hostname published through this tunnel is public unless an Access
*application* (not just a policy) covers it, and the shared policies admit any
service token, including the leaked one.

**How to apply:** for a new protected hostname, follow the rea pattern: nginx
vhost on 127.0.0.1:80 only → email-only reusable policy → Access app (note its
AUD) → ingress rule with `originRequest.access` → back up, `ingress validate`,
restart → `cloudflared tunnel route dns` last. To prove the origin JWT check
without a PIN, attach a 1h service token via a temporary `non_identity` policy,
fetch with `CF-Access-Client-Id/Secret` (or `TUNNEL_SERVICE_TOKEN_ID/SECRET`
for `cloudflared access ssh`), then delete both. Re-check remote state with the
API rather than trusting this table. Related: [[vnc-access-architecture]]
