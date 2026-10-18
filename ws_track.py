#!/usr/bin/env python3
"""ws_track.py — Track cross-tenant player eea830ab on vak88z2.

Runs two concurrent tasks:
  1. Wallet poller  — GET /mb/wallet every 10s, prints delta
  2. mgapi WebSocket — wss://{TID}mgapi.../mb/ws?token={JWT} (authenticated)
  3. pbapi WebSocket — wss://{TID}pbapi.../pb/ws (unauthenticated game-win broadcast)

Usage: uv run ws_track.py [--jwt <path>] [--interval <secs>]
"""
import argparse, asyncio, json, pathlib, time
import requests
import websockets

TID   = "af6efb584a3d317b5a11ab6209b88e1b"
MGAPI = f"https://{TID}mgapi.asdgapicenterssdo.com"
MGWS  = f"wss://{TID}mgapi.asdgapicenterssdo.com/mb/ws"
PBWS  = f"wss://{TID}pbapi.asdgapicenterssdo.com/pb/ws"

ap = argparse.ArgumentParser()
ap.add_argument("--jwt", type=pathlib.Path,
                default=pathlib.Path("/home/kzp/claude-red/.jwt.eea830ab"))
ap.add_argument("--interval", type=int, default=10)
args = ap.parse_args()

JWT = args.jwt.read_text().strip()
HDRS = {"Authorization": f"Bearer {JWT}", "template": "th",
        "Accept": "application/json"}

_last_bal  = None
_last_pts  = None
_start     = time.time()


def ts():
    elapsed = int(time.time() - _start)
    return f"+{elapsed:4d}s"


def fmt_wallet(d):
    global _last_bal, _last_pts
    bal = d.get("balance", "?")
    pts = d.get("pointData", {}).get("point", d.get("point", "?"))
    tdt = d.get("data", [{}])[0].get("turn_deposit_target", 0) if d.get("data") else 0

    parts = [f"bal={bal} THB  pts={pts}  turn={tdt}"]
    if _last_bal is not None and bal != _last_bal:
        try:
            delta = float(bal) - float(_last_bal)
            parts.append(f"  ← ΔBAL {delta:+.2f}")
        except Exception:
            pass
    if _last_pts is not None and pts != _last_pts:
        try:
            delta = float(pts) - float(_last_pts)
            parts.append(f"  ΔPTS {delta:+.2f}")
        except Exception:
            pass
    _last_bal = bal
    _last_pts = pts
    return "".join(parts)


async def wallet_poller(interval):
    print(f"[wallet] polling every {interval}s")
    while True:
        try:
            r = requests.get(f"{MGAPI}/mb/wallet", headers=HDRS, timeout=8)
            if r.ok:
                d = r.json()
                print(f"[{ts()}] WALLET  {fmt_wallet(d)}")
            else:
                print(f"[{ts()}] WALLET  ERR {r.status_code}: {r.text[:80]}")
        except Exception as e:
            print(f"[{ts()}] WALLET  EXC {e}")
        await asyncio.sleep(interval)


async def mgapi_ws():
    url = f"{MGWS}?token={JWT}"
    print(f"[mgws]  connecting {MGWS}?token=...")
    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
            print(f"[{ts()}] MGWS    CONNECTED")
            # send test messages
            for probe in [
                '{"action":"get","resource":"wallet"}',
                '{"method":"find","service":"wallet"}',
                '{"jsonrpc":"2.0","method":"wallet","id":1}',
            ]:
                await ws.send(probe)
            async for msg in ws:
                print(f"[{ts()}] MGWS  ← {str(msg)[:200]}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"[{ts()}] MGWS    REJECTED HTTP {e.status_code}")
    except Exception as e:
        print(f"[{ts()}] MGWS    EXC {type(e).__name__}: {e}")


async def pbapi_ws():
    print(f"[pbws]  connecting {PBWS}")
    try:
        async with websockets.connect(PBWS, ping_interval=20, ping_timeout=10) as ws:
            print(f"[{ts()}] PBWS    CONNECTED (unauthenticated game-win broadcast)")
            async for msg in ws:
                try:
                    d = json.loads(msg)
                    evt = d.get("type", d.get("event", "?"))
                    print(f"[{ts()}] PBWS  ← type={evt}  {str(msg)[:160]}")
                except Exception:
                    print(f"[{ts()}] PBWS  ← {str(msg)[:160]}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"[{ts()}] PBWS    REJECTED HTTP {e.status_code}")
    except Exception as e:
        print(f"[{ts()}] PBWS    EXC {type(e).__name__}: {e}")


async def main():
    print(f"=== ws_track  player=eea830ab  TID={TID[:8]}... ===")
    print(f"    JWT exp check: {JWT[-20:]}")
    print()
    await asyncio.gather(
        wallet_poller(args.interval),
        mgapi_ws(),
        pbapi_ws(),
    )


asyncio.run(main())
