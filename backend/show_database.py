import psycopg2
import sys
import os

try:
    from db_config import get_db_connection
    conn = get_db_connection()
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit(1)

cur = conn.cursor()

print("=" * 70)
print("             NIRAMAYA HEALTH AI - DATABASE VIEWER")
print("=" * 70)
print(f"Database Name: projectH")
print(f"User:          postgres")
print(f"Host:          localhost:5432")
print("=" * 70)

tables = [
    ("account_tbl", ["account_id", "family_name", "email", "is_active", "created_at"]),
    ("member_tbl", ["member_id", "account_id", "name", "gender", "age", "height", "weight"]),
    ("chat_history_tbl", ["history_id", "account_id", "member_id", "model", "user_input", "timestamp"]),
    ("admin_tbl", ["admin_id", "username", "email", "role", "is_active"]),
    ("health_content_tbl", ["content_id", "title", "category", "content_type", "status"])
]

for tbl_name, cols in tables:
    print(f"\n[TABLE] {tbl_name.upper()}")
    print("-" * 70)
    try:
        col_str = ", ".join(cols)
        cur.execute(f"SELECT {col_str} FROM {tbl_name} ORDER BY 1 LIMIT 10;")
        rows = cur.fetchall()
        if not rows:
            print("  (Table is currently empty)")
        else:
            header = " | ".join(cols)
            print(header)
            print("-" * len(header))
            for r in rows:
                formatted_row = [str(val)[:30] if val is not None else "NULL" for val in r]
                print(" | ".join(formatted_row))
    except Exception as err:
        print(f"  Error reading table: {err}")

conn.close()
print("\n" + "=" * 70)
print("Tip for Faculty Presentation:")
print("1. GUI Viewer: Open pgAdmin 4 -> Connect to PostgreSQL -> Databases -> projectH -> Schemas -> public -> Tables.")
print("2. Admin Dashboard: Login to Admin Portal at http://localhost:5000/admin_login.html (User: admin@niramaya.com)")
print("=" * 70)
