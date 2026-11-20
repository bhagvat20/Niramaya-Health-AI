"""
Niramaya Health AI - Autonomous Background Cloud Sync Worker
Maintains continuous real-time synchronization between Render Cloud and Local/Offline instances.
When someone registers or updates data on Render, it pulls down into local niramaya.db.
When someone registers or updates data locally, it pushes up to Render.
"""
import os
import sys
import time
import json
import threading
import urllib.request
from datetime import datetime

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

CLOUD_API_URL = os.environ.get("CLOUD_SYNC_URL", "https://niramaya-health-ai.onrender.com/api/sync/exchange")

def is_running_on_render():
    """Detects if currently executing inside Render cloud container."""
    return bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))


def run_one_sync_cycle():
    """Executes a single bidirectional exchange cycle with the cloud."""
    # Don't sync with self if already on Render
    if is_running_on_render():
        return False

    try:
        from db_config import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch current local accounts
        cursor.execute("""
            SELECT account_id, family_name, email, password_hash, is_active, created_at 
            FROM account_tbl;
        """)
        local_accounts = []
        for r in cursor.fetchall():
            local_accounts.append({
                "account_id": r[0],
                "family_name": r[1],
                "email": str(r[2]).strip().lower() if r[2] else "",
                "password_hash": r[3],
                "is_active": bool(r[4]),
                "created_at": str(r[5]) if r[5] else ""
            })

        # 2. Fetch local members
        cursor.execute("""
            SELECT m.member_id, m.account_id, m.name, m.gender, m.age, m.height, m.weight, m.created_at, a.email
            FROM member_tbl m
            LEFT JOIN account_tbl a ON m.account_id = a.account_id;
        """)
        local_members = []
        for r in cursor.fetchall():
            local_members.append({
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

        # 3. Fetch local chats
        cursor.execute("""
            SELECT c.history_id, c.account_id, c.member_id, c.user_input, c.bot_response, c.model, c.timestamp, a.email
            FROM chat_history_tbl c
            LEFT JOIN account_tbl a ON c.account_id = a.account_id;
        """)
        local_chats = []
        for r in cursor.fetchall():
            local_chats.append({
                "history_id": r[0],
                "account_id": r[1],
                "member_id": r[2],
                "user_input": r[3],
                "bot_response": r[4],
                "model": r[5],
                "timestamp": str(r[6]) if r[6] else "",
                "account_email": str(r[7]).strip().lower() if r[7] else ""
            })

        # 4. Send payload to Render Cloud
        payload = json.dumps({
            "accounts": local_accounts,
            "members": local_members,
            "chats": local_chats
        }).encode('utf-8')

        req = urllib.request.Request(
            CLOUD_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Niramaya-Local-Sync-Engine/1.0"
            }
        )

        with urllib.request.urlopen(req, timeout=25) as resp:
            if resp.status == 200:
                cloud_data = json.loads(resp.read().decode('utf-8'))
                if cloud_data.get("success"):
                    # 5. Merge any accounts from Render that local does not have
                    cloud_accounts = cloud_data.get("accounts", [])
                    for acc in cloud_accounts:
                        email = str(acc.get("email") or "").strip().lower()
                        if not email:
                            continue

                        cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s;", (email,))
                        existing = cursor.fetchone()
                        fname = acc.get("family_name") or "Family"
                        pwd_hash = acc.get("password_hash") or "$2b$12$K1r6tE1599G..."
                        is_active = bool(acc.get("is_active", True))
                        created_at = acc.get("created_at") or datetime.now().isoformat()

                        if existing:
                            cursor.execute("""
                                UPDATE account_tbl SET family_name = %s, is_active = %s
                                WHERE account_id = %s;
                            """, (fname, is_active, existing[0]))
                        else:
                            cursor.execute("""
                                INSERT INTO account_tbl (family_name, email, password_hash, is_active, created_at)
                                VALUES (%s, %s, %s, %s, %s);
                            """, (fname, email, pwd_hash, is_active, created_at))

                    conn.commit()

                    # Merge cloud members into local
                    cloud_members = cloud_data.get("members", [])
                    for mem in cloud_members:
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
                                UPDATE member_tbl SET gender = %s, age = %s, height = %s, weight = %s
                                WHERE member_id = %s;
                            """, (gender, age, height, weight, existing_m[0]))
                        else:
                            cursor.execute("""
                                INSERT INTO member_tbl (account_id, name, gender, age, height, weight, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s);
                            """, (acc_id, mem_name, gender, age, height, weight, created_at))

                    conn.commit()

                    # Merge cloud chats into local
                    cloud_chats = cloud_data.get("chats", [])
                    for c in cloud_chats:
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
                            """, (acc_id, mem_id, u_input, b_resp, model, ts))

                    conn.commit()
                    return True

    except Exception as e:
        # Silently log network/offline errors so local functionality is never interrupted
        # print(f"[Sync Notice] Cloud ping: {e}")
        pass
    finally:
        if 'conn' in locals() and conn:
            try:
                conn.close()
            except Exception:
                pass
    return False


def trigger_instant_sync():
    """Runs a quick synchronous sync when requested by admin views."""
    threading.Thread(target=run_one_sync_cycle, daemon=True).start()


def _background_sync_loop():
    """Continuous background sync loop every 10 seconds."""
    time.sleep(3)  # Wait for server to finish binding port
    while True:
        run_one_sync_cycle()
        time.sleep(10)


def start_sync_worker():
    """Starts the background sync daemon thread if running locally."""
    if is_running_on_render():
        return
    t = threading.Thread(target=_background_sync_loop, daemon=True)
    t.start()
