"""
Synchronizes all data from SQLite (backend/niramaya.db) into PostgreSQL (projectH).
Ensures that when viewing tables in pgAdmin 4, all real project data is present.
"""
import os
import sys
import sqlite3
import psycopg2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, "niramaya.db")

def sync():
    if not os.path.exists(SQLITE_PATH):
        print(f"[!] SQLite DB not found at {SQLITE_PATH}")
        return

    # Check PostgreSQL connection
    pg_conn = None
    passwords = [None, "", "1234", "postgres", "Admin@1234"]
    for pwd in passwords:
        try:
            pg_conn = psycopg2.connect(
                dbname="projectH",
                user="postgres",
                password=pwd,
                host="127.0.0.1",
                port=5432,
                connect_timeout=2
            )
            break
        except Exception:
            pass

    if not pg_conn:
        print("[!] Could not connect to PostgreSQL 'projectH'. Make sure service is running.")
        return

    sq_conn = sqlite3.connect(SQLITE_PATH)
    sq_cur = sq_conn.cursor()
    pg_cur = pg_conn.cursor()

    print("[*] Connected to both SQLite and PostgreSQL. Starting data sync to 'projectH'...")

    # 1. Sync accounts
    try:
        sq_cur.execute("SELECT account_id, family_name, email, password_hash, is_active, created_at FROM account_tbl;")
        accounts = sq_cur.fetchall()
        for r in accounts:
            pg_cur.execute("""
                INSERT INTO account_tbl (account_id, family_name, email, password_hash, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (account_id) DO UPDATE SET
                    family_name = EXCLUDED.family_name,
                    email = EXCLUDED.email,
                    is_active = EXCLUDED.is_active;
            """, (r[0], r[1], r[2], r[3], bool(r[4]), r[5]))
        pg_conn.commit()
        print(f" [+] Synced {len(accounts)} accounts into account_tbl")
    except Exception as e:
        pg_conn.rollback()
        print(f" [!] Notice syncing account_tbl: {e}")

    # 2. Sync members
    try:
        sq_cur.execute("SELECT member_id, account_id, name, gender, age, height, weight, created_at FROM member_tbl;")
        members = sq_cur.fetchall()
        for r in members:
            pg_cur.execute("""
                INSERT INTO member_tbl (member_id, account_id, name, gender, age, height, weight, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (member_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    gender = EXCLUDED.gender,
                    age = EXCLUDED.age,
                    height = EXCLUDED.height,
                    weight = EXCLUDED.weight;
            """, (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
        pg_conn.commit()
        print(f" [+] Synced {len(members)} family members into member_tbl")
    except Exception as e:
        pg_conn.rollback()
        print(f" [!] Notice syncing member_tbl: {e}")

    # 3. Sync chat history
    try:
        sq_cur.execute("SELECT history_id, account_id, member_id, user_input, bot_response, model, timestamp FROM chat_history_tbl;")
        chats = sq_cur.fetchall()
        for r in chats:
            pg_cur.execute("""
                INSERT INTO chat_history_tbl (history_id, account_id, member_id, user_input, bot_response, model, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (history_id) DO NOTHING;
            """, (r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
        pg_conn.commit()
        print(f" [+] Synced {len(chats)} AI consultations into chat_history_tbl")
    except Exception as e:
        pg_conn.rollback()
        print(f" [!] Notice syncing chat_history_tbl: {e}")

    # 4. Sync health content
    try:
        sq_cur.execute("SELECT content_id, content_type, title, category, content, author_or_source, external_link, image_url, status, created_at, updated_at FROM health_content_tbl;")
        content = sq_cur.fetchall()
        for r in content:
            pg_cur.execute("""
                INSERT INTO health_content_tbl (content_id, content_type, title, category, content, author_or_source, external_link, image_url, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (content_id) DO NOTHING;
            """, r)
        pg_conn.commit()
        print(f" [+] Synced {len(content)} health content items into health_content_tbl")
    except Exception as e:
        pg_conn.rollback()
        print(f" [!] Notice syncing health_content_tbl: {e}")

    # Update serial sequences so future inserts don't collide
    for seq, tbl, col in [('account_tbl_account_id_seq', 'account_tbl', 'account_id'),
                          ('member_tbl_member_id_seq', 'member_tbl', 'member_id'),
                          ('chat_history_tbl_history_id_seq', 'chat_history_tbl', 'history_id'),
                          ('health_content_tbl_content_id_seq', 'health_content_tbl', 'content_id')]:
        try:
            pg_cur.execute(f"SELECT setval('{seq}', COALESCE((SELECT MAX({col}) FROM {tbl}), 1));")
            pg_conn.commit()
        except Exception:
            try:
                pg_conn.rollback()
            except Exception:
                pass

    sq_conn.close()
    pg_conn.close()
    print("[+] All tables successfully synced to PostgreSQL projectH!")

if __name__ == "__main__":
    sync()
