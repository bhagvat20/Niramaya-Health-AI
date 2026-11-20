"""
Niramaya Health AI - Concurrent Cloud & Offline Database Sync API
Enables seamless bidirectional data exchange between Render Cloud and Local/Offline instances.
When a user is added on Render, they immediately sync to the offline admin, and vice-versa.
"""
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from datetime import datetime
from db_config import get_db_connection

sync_bp = Blueprint('sync_bp', __name__)
CORS(sync_bp)

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

    return accounts, members, chats


@sync_bp.route('/api/sync/exchange', methods=['GET', 'POST'])
def exchange_sync_data():
    """
    Bidirectional synchronization endpoint:
    - Merges incoming accounts/members/chats into this database.
    - Returns all current accounts/members/chats to the caller.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        data = request.get_json(silent=True) or {}
        in_accounts = data.get("accounts", [])
        in_members = data.get("members", [])
        in_chats = data.get("chats", [])

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
                SELECT history_id FROM chat_history_tbl 
                WHERE account_id = %s AND user_input = %s AND timestamp = %s;
            """, (acc_id, u_input, ts))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO chat_history_tbl (account_id, member_id, user_input, bot_response, model, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, (acc_id, mem_id, b_resp, model, ts))

        conn.commit()

        # Return latest comprehensive records from this database
        all_accounts, all_members, all_chats = _get_all_records(cursor)

        return jsonify({
            "success": True,
            "message": "Sync exchange successful",
            "counts": {
                "accounts": len(all_accounts),
                "members": len(all_members),
                "chats": len(all_chats)
            },
            "accounts": all_accounts,
            "members": all_members,
            "chats": all_chats
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
