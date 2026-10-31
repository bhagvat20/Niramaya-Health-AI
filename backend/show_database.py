import sys
import os

try:
    from db_config import get_db_connection
    conn = get_db_connection()
except Exception as e:
    print(f"[ERROR] Could not connect to database: {e}")
    sys.exit(1)

cur = conn.cursor()

is_sqlite = conn.__class__.__name__ == 'SQLiteConnWrapper'
db_engine = "SQLite (Local niramaya.db)" if is_sqlite else "PostgreSQL (localhost:5432 / projectH)"

print("=" * 76)
print("              NIRAMAYA HEALTH AI - CLINICAL DATABASE VIEWER")
print("=" * 76)
print(f" Database Engine : {db_engine}")
print(f" Database Name   : projectH")
print(f" Status          : ONLINE & READY")
print("=" * 76)

# Aggregate Summary Counts
try:
    cur.execute("SELECT COUNT(*) FROM account_tbl;")
    total_acc = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM member_tbl;")
    total_mem = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM chat_history_tbl;")
    total_chat = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM health_content_tbl;")
    total_content = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM admin_tbl;")
    total_admin = cur.fetchone()[0]

    print("\n [SYSTEM OVERVIEW COUNTS]")
    print(f"  + Registered Accounts : {total_acc}")
    print(f"  + Family Members      : {total_mem}")
    print(f"  + AI Consultations    : {total_chat}")
    print(f"  + Health Articles/Tips: {total_content}")
    print(f"  + Admin Profiles      : {total_admin}")
    print("-" * 76)
except Exception as e:
    print(f" [!] Notice counting tables: {e}")

tables = [
    ("account_tbl", ["account_id", "family_name", "email", "is_active", "created_at"]),
    ("member_tbl", ["member_id", "account_id", "name", "gender", "age", "height", "weight"]),
    ("chat_history_tbl", ["history_id", "account_id", "member_id", "model", "user_input", "timestamp"]),
    ("admin_tbl", ["admin_id", "username", "email", "role", "is_active"]),
    ("health_content_tbl", ["content_id", "title", "category", "content_type", "status"])
]

for tbl_name, cols in tables:
    print(f"\n [TABLE] {tbl_name.upper()}")
    print("-" * 76)
    try:
        col_str = ", ".join(cols)
        cur.execute(f"SELECT {col_str} FROM {tbl_name} ORDER BY 1 DESC LIMIT 10;")
        rows = cur.fetchall()
        if not rows:
            print("  (Table is currently empty)")
        else:
            col_widths = [max(len(c), 12) for c in cols]
            for r in rows:
                for i, v in enumerate(r):
                    s = str(v)[:28] if v is not None else "NULL"
                    col_widths[i] = min(max(col_widths[i], len(s)), 30)

            header = " | ".join(c.upper().ljust(col_widths[i]) for i, c in enumerate(cols))
            divider = "-+-".join("-" * col_widths[i] for i in range(len(cols)))
            print(header)
            print(divider)
            for r in rows:
                row_str = " | ".join((str(val)[:28] if val is not None else "NULL").ljust(col_widths[i]) for i, val in enumerate(r))
                print(row_str)
    except Exception as err:
        print(f"  Error reading table: {err}")

conn.close()
print("\n" + "=" * 76)
print(" Presentation & Demo Access:")
print(" 1. Web Portal URL  : http://127.0.0.1:5000/home.html")
print(" 2. Symptom Checker : http://127.0.0.1:5000/question_input.html")
print(" 3. Admin Portal    : http://127.0.0.1:5000/admin_login.html (User: admin@niramaya.com)")
print("=" * 76)
