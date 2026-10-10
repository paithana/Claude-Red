#!/usr/bin/env python3 -I
"""rtdb_rollback.py — Roll back test values written during F31 RTDB exploit testing.
Cleans up wallet/balance/DEPOSIT_APPROVE/cashback fake entries on both vak88z2 and we88c.
"""
import json, os, ssl, time, urllib.request, urllib.error

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def http(method, url, body=None, timeout=15):
    h = {"Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, method=method, data=data, headers=h)
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=timeout) as resp:
            return resp.status, resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')[:400]
    except Exception as ex:
        return 0, str(ex)[:200]

def fb_refresh(api_key, refresh_token_file):
    """Exchange stored refresh token for a fresh Firebase ID token."""
    if not os.path.exists(refresh_token_file):
        return None
    refresh_tok = open(refresh_token_file).read().strip()
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
    body = f"grant_type=refresh_token&refresh_token={refresh_tok}".encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
            d = json.loads(resp.read())
            # Update stored refresh token if rotated
            new_refresh = d.get("refresh_token")
            if new_refresh and new_refresh != refresh_tok:
                open(refresh_token_file, "w").write(new_refresh)
            return d.get("id_token")
    except Exception as ex:
        print(f"  FB refresh failed: {ex}")
        return None

def platform_fb_token(tid):
    """Get Firebase ID token for we88c via /mb/firebase-token + identitytoolkit."""
    JWT_FILE = "/home/kzp/claude-red/.jwt.we88c"
    if not os.path.exists(JWT_FILE):
        return None
    jwt = open(JWT_FILE).read().strip()
    # Step 1: get custom token from mgapi
    url = f"https://{tid}mgapi.asdgapicenterssdo.com/mb/firebase-token"
    code, body = http("GET", url, timeout=15)
    # Note: we need Authorization header but we pass jwt inline
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
            d = json.loads(resp.read())
            custom_token = d.get("token") or d.get("customToken") or d.get("data", {}).get("token")
    except Exception:
        return None
    if not custom_token:
        return None
    # Step 2: exchange custom token for ID token
    api_key = "AIzaSyAI5j8kaGDUcUDE5ZMk9Um4CneqEx-4q-s"
    url2 = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={api_key}"
    code2, body2 = http("POST", url2, body={"token": custom_token, "returnSecureToken": True})
    if code2 == 200:
        return json.loads(body2).get("idToken")
    return None

def rtdb_get(rtdb_url, path, fb_token):
    code, body = http("GET", f"{rtdb_url}{path}.json?auth={fb_token}")
    if code == 200:
        return json.loads(body)
    return None

def rtdb_delete(rtdb_url, path, fb_token):
    code, body = http("DELETE", f"{rtdb_url}{path}.json?auth={fb_token}")
    return code, body

def rtdb_put(rtdb_url, path, fb_token, value):
    code, body = http("PUT", f"{rtdb_url}{path}.json?auth={fb_token}", body=value)
    return code, body

def rollback_rtdb(label, rtdb_url, uid, fb_token, real_balance=None):
    print(f"\n{'='*60}")
    print(f"ROLLBACK: {label}")
    print(f"  RTDB: {rtdb_url}")
    print(f"  UID:  {uid}")
    print(f"  Real platform balance: {real_balance} THB")
    print(f"{'='*60}")

    changes = []

    # 1. Read current user node (top-level)
    user_data = rtdb_get(rtdb_url, f"/users/{uid}", fb_token)
    if user_data is None:
        print(f"  [SKIP] Cannot read /users/{uid} — token may be invalid")
        return

    print(f"  Current top-level keys: {list(user_data.keys()) if isinstance(user_data, dict) else 'not a dict'}")

    # 2. Delete wallet/balance/credit if they look like test values
    for field in ["wallet", "balance", "credit"]:
        val = user_data.get(field) if isinstance(user_data, dict) else None
        if val is None:
            continue
        # Detect test values: dict with 999999, or scalar >= 99999
        is_test = False
        if isinstance(val, (int, float)) and val >= 99999:
            is_test = True
        elif isinstance(val, dict):
            # Check if any nested value is >= 99999
            nums = [v for v in val.values() if isinstance(v, (int, float)) and v >= 99999]
            if nums:
                is_test = True
        if is_test:
            print(f"  [DELETE] /users/{uid}/{field} (value={str(val)[:60]}) — test value detected")
            code, body = rtdb_delete(rtdb_url, f"/users/{uid}/{field}", fb_token)
            print(f"    → DELETE {code}: {body[:80]}")
            changes.append(f"deleted /{field}")

    # 3. Delete test DEPOSIT_APPROVE entries (keep real ones if any)
    dep_approve = user_data.get("DEPOSIT_APPROVE") if isinstance(user_data, dict) else None
    if isinstance(dep_approve, dict):
        for dep_id, dep_val in dep_approve.items():
            # Real deposit IDs look like UUIDs with hyphens; test ones too but amounts are huge
            amount = None
            if isinstance(dep_val, dict):
                amount = dep_val.get("amount") or dep_val.get("deposit_amount")
                try:
                    amount = float(amount) if amount is not None else None
                except (TypeError, ValueError):
                    amount = None
            elif isinstance(dep_val, (int, float)):
                amount = dep_val
            # Delete if amount >= 99999 (test) or if value is literally 99999
            if amount is not None and amount >= 99999:
                print(f"  [DELETE] DEPOSIT_APPROVE/{dep_id} (amount={amount}) — test value")
                code, body = rtdb_delete(rtdb_url, f"/users/{uid}/DEPOSIT_APPROVE/{dep_id}", fb_token)
                print(f"    → DELETE {code}: {body[:60]}")
                changes.append(f"deleted DEPOSIT_APPROVE/{dep_id[:8]}")
            elif isinstance(dep_val, (int, float)) and dep_val >= 99999:
                print(f"  [DELETE] DEPOSIT_APPROVE/{dep_id} (val={dep_val}) — test value")
                code, body = rtdb_delete(rtdb_url, f"/users/{uid}/DEPOSIT_APPROVE/{dep_id}", fb_token)
                print(f"    → DELETE {code}: {body[:60]}")
                changes.append(f"deleted DEPOSIT_APPROVE/{dep_id[:8]}")
        # Also check if DEPOSIT_APPROVE itself is a scalar test value
    elif isinstance(dep_approve, (int, float)) and dep_approve >= 99999:
        print(f"  [DELETE] DEPOSIT_APPROVE (val={dep_approve}) — scalar test value")
        code, body = rtdb_delete(rtdb_url, f"/users/{uid}/DEPOSIT_APPROVE", fb_token)
        print(f"    → DELETE {code}: {body[:60]}")
        changes.append("deleted DEPOSIT_APPROVE (scalar)")

    # 4. Delete fake DEPOSIT_CONFIRM entries
    dep_confirm = user_data.get("DEPOSIT_CONFIRM") if isinstance(user_data, dict) else None
    if isinstance(dep_confirm, dict):
        for dep_id, dep_val in dep_confirm.items():
            amount = dep_val.get("amount") if isinstance(dep_val, dict) else dep_val
            try:
                amount = float(amount) if amount is not None else None
            except (TypeError, ValueError):
                amount = None
            if amount is not None and amount >= 99999:
                print(f"  [DELETE] DEPOSIT_CONFIRM/{dep_id} (amount={amount}) — test value")
                code, body = rtdb_delete(rtdb_url, f"/users/{uid}/DEPOSIT_CONFIRM/{dep_id}", fb_token)
                print(f"    → DELETE {code}: {body[:60]}")
                changes.append(f"deleted DEPOSIT_CONFIRM/{dep_id[:8]}")

    # 5. Delete fake cashback entries
    cashback = user_data.get("cashback") if isinstance(user_data, dict) else None
    if isinstance(cashback, (int, float)) and cashback >= 99999:
        print(f"  [DELETE] cashback (val={cashback}) — test value")
        code, body = rtdb_delete(rtdb_url, f"/users/{uid}/cashback", fb_token)
        print(f"    → DELETE {code}: {body[:60]}")
        changes.append("deleted cashback")
    elif isinstance(cashback, dict):
        for k, v in cashback.items():
            if isinstance(v, (int, float)) and v >= 99999:
                print(f"  [DELETE] cashback/{k} (val={v}) — test value")
                code, body = rtdb_delete(rtdb_url, f"/users/{uid}/cashback/{k}", fb_token)
                print(f"    → DELETE {code}: {body[:60]}")
                changes.append(f"deleted cashback/{k}")

    # 6. Delete JACKPOT_WIN test entries
    jackpot = user_data.get("JACKPOT_WIN") if isinstance(user_data, dict) else None
    if jackpot is not None:
        print(f"  [DELETE] JACKPOT_WIN — test value")
        code, body = rtdb_delete(rtdb_url, f"/users/{uid}/JACKPOT_WIN", fb_token)
        print(f"    → DELETE {code}: {body[:60]}")
        changes.append("deleted JACKPOT_WIN")

    # Also check jackpot_wins
    jackpot2 = user_data.get("jackpot_wins") if isinstance(user_data, dict) else None
    if jackpot2 is not None:
        print(f"  [DELETE] jackpot_wins — test value")
        code, body = rtdb_delete(rtdb_url, f"/users/{uid}/jackpot_wins", fb_token)
        print(f"    → DELETE {code}: {body[:60]}")
        changes.append("deleted jackpot_wins")

    # 7. Verify final state
    print(f"\n  [VERIFY] Reading final state after rollback...")
    final = rtdb_get(rtdb_url, f"/users/{uid}", fb_token)
    if isinstance(final, dict):
        remaining_keys = list(final.keys())
        print(f"  Remaining keys: {remaining_keys}")
        # Check for any remaining large values
        for field in ["wallet", "balance", "credit", "cashback"]:
            v = final.get(field)
            if isinstance(v, (int, float)) and v >= 99999:
                print(f"  [WARN] {field} still has large value: {v}")
            elif isinstance(v, dict):
                large = [k for k, vv in v.items() if isinstance(vv, (int, float)) and vv >= 99999]
                if large:
                    print(f"  [WARN] {field} still has large nested values: {large}")
    else:
        print(f"  Final state: {str(final)[:200]}")

    if changes:
        print(f"\n  [DONE] Changes made: {', '.join(changes)}")
    else:
        print(f"\n  [CLEAN] No test values found — RTDB already clean (or couldn't read)")


# ============================================================
# vak88z2 rollback
# ============================================================
VAK88Z2_RTDB = "https://vak88z-default-rtdb.asia-southeast1.firebasedatabase.app"
VAK88Z2_API_KEY = "AIzaSyAELPsIAYigvKgJBAsbl_3WM9_tNOr5UiE"
VAK88Z2_UID = "ff6c08fb-c109-4c33-9b9f-342e2aca3822"
VAK88Z2_REFRESH_FILE = "/home/kzp/claude-red/fb_refresh_token_new.txt"

print("=== RTDB ROLLBACK — Cleaning up F31 test data ===")
print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S +07')}")

print("\n[1/2] Getting vak88z2 Firebase token...")
vak88z2_fb_token = fb_refresh(VAK88Z2_API_KEY, VAK88Z2_REFRESH_FILE)
if vak88z2_fb_token:
    print(f"  Token OK")
    rollback_rtdb(
        label="vak88z2",
        rtdb_url=VAK88Z2_RTDB,
        uid=VAK88Z2_UID,
        fb_token=vak88z2_fb_token,
        real_balance=0.57
    )
else:
    print(f"  [SKIP] Could not get vak88z2 FB token — refresh token may be expired")

# ============================================================
# we88c rollback
# ============================================================
WE88C_RTDB = "https://we88zz-default-rtdb.asia-southeast1.firebasedatabase.app"
WE88C_TID = "54ef7626cb381f4bab8be91f0cdbce47"
WE88C_UID = "266d74e3-d6ca-47eb-b9ac-b8c45574bad4"

print("\n[2/2] Getting we88c Firebase token via /mb/firebase-token...")
we88c_fb_token = platform_fb_token(WE88C_TID)
if we88c_fb_token:
    print(f"  Token OK")
    rollback_rtdb(
        label="we88c",
        rtdb_url=WE88C_RTDB,
        uid=WE88C_UID,
        fb_token=we88c_fb_token,
        real_balance=0.86
    )
else:
    print(f"  [SKIP] Could not get we88c FB token — JWT may be expired or /mb/firebase-token unavailable")

print("\n=== ROLLBACK COMPLETE ===")
