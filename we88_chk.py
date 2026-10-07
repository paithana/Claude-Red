#!/usr/bin/env python3
"""
we88_chk.py — Bulk OCR/QR decode local JPGs, extract PromptPay qr_string,
               submit to /mb/auto-slip-deposit/check on asdgapicenterssdo.com
Usage:
    uv run we88_chk.py slips/          # scan all JPG/PNG in dir
    uv run we88_chk.py slip1.jpg       # single file
    uv run we88_chk.py slips/ --curl   # print curl one-liners only
    uv run we88_chk.py slips/ --dry    # decode only, no submit
"""
import sys, json, re, time, ssl, os, argparse
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
API_HOST  = os.environ.get("API_HOST",
    "54ef7626cb381f4bab8be91f0cdbce47mgapi.asdgapicenterssdo.com")
ENDPOINT  = f"https://{API_HOST}/mb/auto-slip-deposit/check"
JWT       = os.environ.get("WE88_JWT", os.environ.get("JWT", ""))
if not JWT:
    for _jwt_file in (Path(".jwt.we88c"), Path(".jwt")):
        if _jwt_file.exists():
            JWT = _jwt_file.read_text().strip()
            if JWT: break
AWSALB    = os.environ.get("AWSALB", "")
if not AWSALB:
    _alb_file = Path(".awsalb")
    if _alb_file.exists(): AWSALB = _alb_file.read_text().strip()
TEMPLATE  = os.environ.get("WE88_TEMPLATE", "vn")
RATE      = 3
OUT       = f"we88_chk_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

# PromptPay EMV QR pattern
QR_RE = re.compile(r'(00[24]\d{2}[0-9A-Z]{20,120}(?:TH|DTF)[0-9A-Z]{4,20})', re.IGNORECASE)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode    = ssl.CERT_NONE

results = []
_last   = [0.0]


def rate_wait():
    gap = 1.0 / RATE - (time.time() - _last[0])
    if gap > 0:
        time.sleep(gap)
    _last[0] = time.time()


# ── QR / OCR decode ───────────────────────────────────────────────────────────
def decode_qr(path: Path) -> list[str]:
    found = []

    # Method 1: pyzbar direct QR decode
    try:
        from pyzbar.pyzbar import decode as pyz_decode
        from PIL import Image
        img = Image.open(path)
        for obj in pyz_decode(img):
            data = obj.data.decode("utf-8", errors="replace")
            if data.startswith("00") and len(data) > 30:
                found.append(data.strip())
    except ImportError:
        pass
    except Exception as e:
        print(f"  [pyzbar] {path.name}: {e}")

    if found:
        return found

    # Method 2: OpenCV grayscale + threshold + pyzbar
    try:
        import cv2
        from pyzbar.pyzbar import decode as pyz_decode
        img = cv2.imread(str(path))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
        for src in (gray, thresh):
            for obj in pyz_decode(src):
                data = obj.data.decode("utf-8", errors="replace")
                if data.startswith("00"):
                    found.append(data.strip())
    except ImportError:
        pass
    except Exception:
        pass

    if found:
        return list(dict.fromkeys(found))

    # Method 3: pytesseract OCR fallback
    try:
        import pytesseract
        from PIL import Image
        text = pytesseract.image_to_string(Image.open(path), lang="eng+tha",
                                            config="--psm 6")
        compact = re.sub(r'\s+', '', text)
        for m in QR_RE.finditer(compact):
            found.append(m.group(1))
        for line in text.splitlines():
            line = line.strip().replace(" ", "")
            if len(line) > 30 and line.startswith("00") and re.match(r'^[0-9A-Z]+$', line, re.I):
                found.append(line)
    except ImportError:
        print("  [warn] pytesseract not installed — pip install pytesseract pillow")
    except Exception as e:
        print(f"  [ocr] {path.name}: {e}")

    return list(dict.fromkeys(found))


# ── API submit ────────────────────────────────────────────────────────────────
def submit(qr_string: str) -> dict:
    import uuid
    rate_wait()
    cid  = str(uuid.uuid4())
    body = json.dumps({"qr_string": qr_string}).encode()
    hdrs = {
        "Accept":        "application/json",
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {JWT}",
        "template":      TEMPLATE,
        "CorrelationID": cid,
        "User-Agent":    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
                         "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.6.1 "
                         "Mobile/15E148 Safari/604.1",
        "Referer":       "https://m.we88c.com/th/deposit?component_selected=deposit2",
        **({"Cookie": f"AWSALB={AWSALB}; AWSALBCORS={AWSALB}"} if AWSALB else {}),
    }
    r = urllib.request.Request(ENDPOINT, data=body, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=10, context=CTX) as resp:
            raw = resp.read(8192)
            return {"status": resp.status,
                    "body":   raw.decode("utf-8", errors="replace"),
                    "cid":    cid}
    except urllib.error.HTTPError as e:
        raw = e.read(4096)
        return {"status": e.code,
                "body":   raw.decode("utf-8", errors="replace"),
                "cid":    cid}
    except Exception as ex:
        return {"status": 0, "body": str(ex), "cid": cid}


def fmt_curl(qr_string: str) -> str:
    body = json.dumps({"qr_string": qr_string})
    tok  = JWT[:40] + "..." if len(JWT) > 40 else JWT or "<WE88_JWT>"
    return (
        f"curl -sk -X POST '{ENDPOINT}' \\\n"
        f"  -H 'Authorization: Bearer {tok}' \\\n"
        f"  -H 'Content-Type: application/json' \\\n"
        f"  -H 'template: {TEMPLATE}' \\\n"
        f"  -d '{body}'"
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path",   help="JPG/PNG file or directory")
    ap.add_argument("--dry",  action="store_true", help="Decode only, no API submit")
    ap.add_argument("--curl", action="store_true", help="Print curl one-liners")
    ap.add_argument("--out",  metavar="FILE",       help="Save results to FILE")
    ap.add_argument("--host", metavar="HOST",       help="Override API host")
    args = ap.parse_args()

    global API_HOST, ENDPOINT
    if args.host:
        API_HOST = args.host
        ENDPOINT = f"https://{API_HOST}/mb/auto-slip-deposit/check"

    if not JWT and not args.dry and not args.curl:
        print("[warn] WE88_JWT not set — responses will be 401. Use --dry or export WE88_JWT=...")

    p     = Path(args.path)
    files = sorted(p.glob("**/*.jp*g")) + sorted(p.glob("**/*.png")) \
            if p.is_dir() else [p]
    files = [f for f in files if f.suffix.lower() in (".jpg", ".jpeg", ".png")]

    if not files:
        print(f"No JPG/PNG files in {args.path}")
        sys.exit(1)

    print(f"{'─'*60}")
    print(f"we88_chk — {len(files)} file(s) | {ENDPOINT}")
    print(f"{'─'*60}")

    total_qr = 0
    for f in files:
        print(f"\n[{f.name}]")
        qr_list = decode_qr(f)
        if not qr_list:
            print("  ✗ no QR string found")
            results.append({"file": str(f), "qr_strings": [],
                             "ts": datetime.now(timezone.utc).isoformat()})
            continue

        for qs in qr_list:
            total_qr += 1
            print(f"  QR: {qs[:72]}{'…' if len(qs) > 72 else ''}")

            if args.curl:
                print(fmt_curl(qs))
                continue

            if args.dry:
                results.append({"file": str(f), "qr_string": qs,
                                 "ts": datetime.now(timezone.utc).isoformat()})
                continue

            res    = submit(qs)
            marker = "✓" if res["status"] in (200, 201, 202) else "✗"
            snip   = res["body"][:120].replace("\n", " ")
            print(f"  {marker} [{res['status']}] {snip}")
            results.append({
                "file":      str(f),
                "qr_string": qs,
                "status":    res["status"],
                "response":  res["body"][:500],
                "cid":       res["cid"],
                "ts":        datetime.now(timezone.utc).isoformat(),
            })

    out_path = Path(args.out or OUT)
    out_path.write_text(json.dumps({
        "ts":       datetime.now(timezone.utc).isoformat(),
        "endpoint": ENDPOINT,
        "files":    len(files),
        "qr_found": total_qr,
        "results":  results,
    }, indent=2, ensure_ascii=False))

    hits = [r for r in results if r.get("status") in (200, 201, 202)]
    print(f"\n{'─'*60}")
    print(f"Done — {len(files)} files, {total_qr} QR strings, {len(hits)} successful")
    print(f"Saved: {out_path}")
    if hits:
        print(f"\n★ Hits:")
        for h in hits:
            print(f"  [{h['status']}] {h['file']} → {h['response'][:80]}")


if __name__ == "__main__":
    main()
