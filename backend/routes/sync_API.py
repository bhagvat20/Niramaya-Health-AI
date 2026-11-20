"""
Niramaya Health AI - Concurrent Cloud & Offline Database Sync API
Enables seamless bidirectional data exchange between Render Cloud and Local/Offline instances.
When a user is added on Render, they immediately sync to the offline admin, and vice-versa.
"""
import os
import sys
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask import Blueprint, request, jsonify
from flask_cors import CORS
from datetime import datetime
from db_config import get_db_connection

sync_bp = Blueprint('sync_bp', __name__)
CORS(sync_bp)

DEFAULT_SYNC_KEY = "niramaya_sync_sec_2026_e7d8f9"

def _is_sync_authorized(req) -> bool:
    """Validates sync authorization via X-Sync-Token, Authorization Bearer, or request body."""
    expected_key = os.environ.get("SYNC_AUTH_KEY", DEFAULT_SYNC_KEY).strip()
    # 1. Header: X-Sync-Token
    token = req.headers.get("X-Sync-Token", "").strip()
    # 2. Header: Authorization Bearer
    if not token and req.headers.get("Authorization", "").startswith("Bearer "):
        token = req.headers.get("Authorization", "").split(" ", 1)[1].strip()
    # 3. Payload: sync_token
    if not token and req.is_json:
        data = req.get_json(silent=True) or {}
        token = str(data.get("sync_token") or "").strip()
    return bool(token and token == expected_key)

def _get_all_records(cursor):
    """Fetches all accounts, members, and chats for sync payload."""
    cursor.execute("""
        SELECT account_id, family_name, email, password_hash, is_active, created_at 
        FROM account_tbl ORDER BY account_id ASC;
    """)
    accounts = []
    for r in cursor.fetchall():
        accounts.append({
            "account_id": r[0],
            "family_name": r[1],
            "email": str(r[2]).strip().lower() if r[2] else "",
            "password_hash": r[3],
            "is_active": bool(r[4]),
            "created_at": str(r[5]) if r[5] else ""
        })

    cursor.execute("""
        SELECT m.member_id, m.account_id, m.name, m.gender, m.age, m.height, m.weight, m.created_at, a.email
        FROM member_tbl m
        LEFT JOIN account_tbl a ON m.account_id = a.account_id
        ORDER BY m.member_id ASC;
    """)
    members = []
    for r in cursor.fetchall():
        members.append({
            "member_id": r[0],
            "account_id": r[1],
            "name": r[2],
            "gender": r[3],
            "age": r[4],
            "height": r[5] or "N/A",
            "weight": r[6] or "N/A",
            "created_at": str(r[7]) if r[7] else "",
            "account_email": str(r[8]).strip().lower() if r[8] else ""
        })

    cursor.execute("""
        SELECT c.history_id, c.account_id, c.member_id, c.user_input, c.bot_response, c.model, c.timestamp, a.email
        FROM chat_history_tbl c
        LEFT JOIN account_tbl a ON c.account_id = a.account_id
        ORDER BY c.history_id ASC;
    """)
    chats = []
    for r in cursor.fetchall():
        chats.append({
            "history_id": r[0],
            "account_id": r[1],
            "member_id": r[2],
            "user_input": r[3],
            "bot_response": r[4],
            "model": r[5],
            "timestamp": str(r[6]) if r[6] else "",
            "account_email": str(r[7]).strip().lower() if r[7] else ""
        })

    otps = []
    try:
        cursor.execute("""
            SELECT o.otp_id, o.account_id, o.email, o.otp_code, o.expires_at, o.used, o.created_at, a.email
            FROM password_reset_otps o
            LEFT JOIN account_tbl a ON o.account_id = a.account_id
            ORDER BY o.otp_id ASC;
        """)
        for r in cursor.fetchall():
            otps.append({
                "otp_id": r[0],
                "account_id": r[1],
                "email": str(r[2]).strip().lower() if r[2] else "",
                "otp_code": str(r[3]),
                "expires_at": str(r[4]) if r[4] else "",
                "used": bool(r[5]),
                "created_at": str(r[6]) if r[6] else "",
                "account_email": str(r[7]).strip().lower() if r[7] else (str(r[2]).strip().lower() if r[2] else "")
            })
    except Exception:
        pass

    return accounts, members, chats, otps


@sync_bp.route('/api/sync/exchange', methods=['GET', 'POST'])
def exchange_sync_data():
    """
    Bidirectional synchronization endpoint:
    - Authenticates via X-Sync-Token / SYNC_AUTH_KEY to protect confidential medical and user data.
    - Merges incoming accounts/members/chats/otps into this database.
    - Returns all current accounts/members/chats/otps to the caller.
    """
    if not _is_sync_authorized(request):
        return jsonify({
            "success": False,
            "error": "Unauthorized: valid X-Sync-Token is required to access sync data."
        }), 401
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        data = request.get_json(silent=True) or {}
        in_accounts = data.get("accounts", [])
        in_members = data.get("members", [])
        in_chats = data.get("chats", [])
        in_otps = data.get("otps", [])

        # 1. Merge incoming accounts (keyed by unique email)
        for acc in in_accounts:
            email = str(acc.get("email") or "").strip().lower()
            if not email or "@" not in email:
                continue

            fname = acc.get("family_name") or "Family"
            pwd_hash = acc.get("password_hash") or "$2b$12$K1r6tE1599G..."
            is_active = bool(acc.get("is_active", True))
            created_at = acc.get("created_at") or datetime.now().isoformat()

            cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s;", (email,))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE account_tbl 
                    SET family_name = %s, is_active = %s
                    WHERE account_id = %s;
                """, (fname, is_active, existing[0]))
            else:
                cursor.execute("""
                    INSERT INTO account_tbl (family_name, email, password_hash, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s);
                """, (fname, email, pwd_hash, is_active, created_at))

        conn.commit()

        # 2. Merge incoming members (linked by parent account email)
        for mem in in_members:
            acc_email = str(mem.get("account_email") or "").strip().lower()
            mem_name = str(mem.get("name") or "").strip()
            if not acc_email or not mem_name:
                continue

            cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s;", (acc_email,))
            parent = cursor.fetchone()
            if not parent:
                continue
            acc_id = parent[0]

            gender = mem.get("gender") or "Other"
            age = mem.get("age") or 25
            height = mem.get("height") or "N/A"
            weight = mem.get("weight") or "N/A"
            created_at = mem.get("created_at") or datetime.now().isoformat()

            cursor.execute("SELECT member_id FROM member_tbl WHERE account_id = %s AND name = %s;", (acc_id, mem_name))
            existing_m = cursor.fetchone()

            if existing_m:
                cursor.execute("""
                    UPDATE member_tbl 
                    SET gender = %s, age = %s, height = %s, weight = %s
                    WHERE member_id = %s;
                """, (gender, age, height, weight, existing_m[0]))
            else:
                cursor.execute("""
                    INSERT INTO member_tbl (account_id, name, gender, age, height, weight, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (acc_id, mem_name, gender, age, height, weight, created_at))

        conn.commit()

        # 3. Merge incoming chats
        for c in in_chats:
            acc_email = str(c.get("account_email") or "").strip().lower()
            u_input = str(c.get("user_input") or "").strip()
            if not acc_email or not u_input:
                continue

            cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s;", (acc_email,))
            parent = cursor.fetchone()
            if not parent:
                continue
            acc_id = parent[0]

            cursor.execute("SELECT member_id FROM member_tbl WHERE account_id = %s ORDER BY member_id ASC LIMIT 1;", (acc_id,))
            m_row = cursor.fetchone()
            mem_id = m_row[0] if m_row else 1

            b_resp = c.get("bot_response") or ""
            model = c.get("model") or "LRv1"
            ts = c.get("timestamp") or datetime.now().isoformat()

            cursor.execute("""
                SELECT history_id, timestamp FROM chat_history_tbl 
                WHERE account_id = %s AND user_input = %s;
            """, (acc_id, u_input))
            existing_rows = cursor.fetchall() or []
            is_dup = False
            ts_prefix = str(ts).replace('T', ' ')[:16]
            for er in existing_rows:
                er_ts = str(er[1] or '').replace('T', ' ')[:16]
                if er_ts and er_ts == ts_prefix:
                    is_dup = True
                    break
            if not is_dup:
                cursor.execute("""
                    INSERT INTO chat_history_tbl (account_id, member_id, user_input, bot_response, model, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (acc_id, mem_id, u_input, b_resp, model, ts))

        conn.commit()

        # 4. Merge incoming password reset OTPs
        if in_otps:
            try:
                for o in in_otps:
                    acc_email = str(o.get("account_email") or o.get("email") or "").strip().lower()
                    otp_code = str(o.get("otp_code") or "").strip()
                    if not acc_email or not otp_code:
                        continue

                    cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s;", (acc_email,))
                    parent = cursor.fetchone()
                    if not parent:
                        continue
                    acc_id = parent[0]

                    used = bool(o.get("used", False))
                    expires_at = o.get("expires_at") or datetime.now().isoformat()
                    created_at = o.get("created_at") or datetime.now().isoformat()

                    cursor.execute("""
                        SELECT otp_id FROM password_reset_otps 
                        WHERE account_id = %s AND otp_code = %s;
                    """, (acc_id, otp_code))
                    existing_o = cursor.fetchone()

                    is_sqlite = conn.__class__.__name__ == 'SQLiteConnWrapper'
                    if existing_o:
                        cursor.execute("""
                            UPDATE password_reset_otps SET used = %s WHERE otp_id = %s;
                        """, (1 if (is_sqlite and used) else used, existing_o[0]))
                    else:
                        if is_sqlite:
                            cursor.execute("""
                                INSERT INTO password_reset_otps (account_id, email, otp_code, expires_at, used, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s);
                            """, (acc_id, acc_email, otp_code, expires_at, 1 if used else 0, created_at))
                        else:
                            cursor.execute("""
                                INSERT INTO password_reset_otps (account_id, email, otp_code, expires_at, used, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s);
                            """, (acc_id, acc_email, otp_code, expires_at, used, created_at))
                conn.commit()
            except Exception as _oe:
                try:
                    conn.rollback()
                except Exception:
                    pass

        # Return latest comprehensive records from this database
        all_accounts, all_members, all_chats, all_otps = _get_all_records(cursor)

        return jsonify({
            "success": True,
            "message": "Sync exchange successful",
            "counts": {
                "accounts": len(all_accounts),
                "members": len(all_members),
                "chats": len(all_chats),
                "otps": len(all_otps)
            },
            "accounts": all_accounts,
            "members": all_members,
            "chats": all_chats,
            "otps": all_otps
        }), 200

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
