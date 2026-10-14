#!/usr/bin/env python3 -I
"""probe_template_th.py — Test template:th header fix on mgapi POST endpoints.

Run: python3 -I probe_template_th.py

Uses the vak88z2 JWT from the pasted network capture.
"""
import json, uuid, sys
import requests

TID_VAK = "af6efb584a3d317b5a11ab6209b88e1b"
TID_WE  = "54ef7626cb381f4bab8be91f0cdbce47"

# vak88z2 JWT from user's network capture (fresh)
JWT_VAK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmZjZjMDhmYi1jMTA5LTRjMzMtOWI5Zi0zNDJlMmFjYTM4MjIiLCJjZiI6IjQzMTY3MGFlM2U0YjRjNDYwMDYwODVjMDAwMjc0YTgzIiwiaXNfbm90X2NvbXBsZXRlIjpmYWxzZSwiZXhwIjoxNzkxNjI0NjU3LCJpYXQiOjE3OTE2MTAyNTd9.3t_ri8oGfDkMncQcQrJ09I64KJY-lPmQwN5BvtSHYAg"

import pathlib
JWT_WE = pathlib.Path(".jwt.we88c").read_text().strip() if pathlib.Path(".jwt.we88c").exists() else ""

def hdrs(tid_type="vak", template="th"):
    jwt = JWT_VAK if tid_type == "vak" else JWT_WE
    return {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
        "template": template,
        "CorrelationID": str(uuid.uuid4()),
        "Origin": f"https://m.{'vak88z2' if tid_type == 'vak' else 'we88c'}.com",
    }

def test(label, method, url, **kwargs):
    r = getattr(requests, method)(url, timeout=12, **kwargs)
    try:
        body = r.json()
        out = json.dumps(body, ensure_ascii=False)[:400]
    except Exception:
        out = r.text[:200]
    print(f"[{r.status_code}] {label}")
    print(f"  {out}")
    print()
    return r.status_code, body if r.ok else {}

# ─── vak88z2 tests ───────────────────────────────────────────────────────────
VAK_MGAPI = f"https://{TID_VAK}mgapi.asdgapicenterssdo.com"

print("=" * 60)
print("VAK88Z2 — template:th")
print("=" * 60)

# GET bank-information
test("GET /mb/bank-information", "get",
     f"{VAK_MGAPI}/mb/bank-information",
     params={"domain": "m.vak88z2.com"},
     headers=hdrs("vak", "th"))

# GET sign-url (was ISE before)
test("POST /mb/sign-url-upload-slip", "post",
     f"{VAK_MGAPI}/mb/sign-url-upload-slip",
     headers=hdrs("vak", "th"),
     json={"filename": "slip.jpeg", "content_type": "image/jpeg", "size": 50000})

# POST deposit-transaction
test("POST /mb/deposit-transaction (minimal)", "post",
     f"{VAK_MGAPI}/mb/deposit-transaction",
     headers=hdrs("vak", "th"),
     json={"amount": 200, "bank_id": "dummy"})

# ─── we88c tests ─────────────────────────────────────────────────────────────
if JWT_WE:
    WE_MGAPI = f"https://{TID_WE}mgapi.asdgapicenterssdo.com"
    print("=" * 60)
    print("WE88C — template:th")
    print("=" * 60)

    test("GET /mb/bank-information (we88c)", "get",
         f"{WE_MGAPI}/mb/bank-information",
         params={"domain": "m.we88c.com"},
         headers=hdrs("we", "th"))

    test("POST /mb/sign-url-upload-slip (we88c)", "post",
         f"{WE_MGAPI}/mb/sign-url-upload-slip",
         headers=hdrs("we", "th"),
         json={"filename": "slip.jpeg", "content_type": "image/jpeg", "size": 50000})

    test("POST /mb/deposit-transaction (we88c)", "post",
         f"{WE_MGAPI}/mb/deposit-transaction",
         headers=hdrs("we", "th"),
         json={"amount": 200, "bank_id": "dummy"})
else:
    print("[!] No .jwt.we88c found — we88c tests skipped")
