import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load optional .env files so DATABASE_URL is picked up if configured locally
for _env_path in (os.path.join(PROJECT_ROOT, ".env"), os.path.join(BASE_DIR, ".env")):
    if os.path.isfile(_env_path):
        try:
            with open(_env_path, "r", encoding="utf-8") as _f:
                for _raw in _f:
                    _line = _raw.strip()
                    if not _line or _line.startswith("#") or "=" not in _line:
                        continue
                    _k, _v = _line.split("=", 1)
                    _k = _k.strip()
                    _v = _v.strip().strip('"').strip("'")
                    if _k and _k not in os.environ:
                        os.environ[_k] = _v
        except Exception:
            pass

try:
    from db_config import get_db_connection
    conn = get_db_connection()
except Exception as e:
    print(f"[ERROR] Could not connect to database: {e}")
    sys.exit(1)

cur = conn.cursor()

is_sqlite = conn.__class__.__name__ == 'SQLiteConnWrapper'
if is_sqlite:
    db_engine = "SQLite (Local backend/niramaya.db)"
    db_name = "niramaya.db"
elif os.environ.get("DATABASE_URL"):
    db_engine = "Cloud PostgreSQL (Neon / Render DATABASE_URL)"
    db_name = "Cloud PostgreSQL"
else:
    db_engine = "PostgreSQL (localhost:5432)"
    db_name = "projectH"

print("=" * 78)
print("              NIRAMAYA HEALTH AI - CLINICAL DATABASE VIEWER")
print("=" * 78)
print(f" Database Engine : {db_engine}")
print(f" Database Name   : {db_name}")
print(f" Status          : ONLINE & READY")
print("=" * 78)

# Aggregate Summary Counts
try:
    def _count(tbl):
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl};")
            return cur.fetchone()[0]
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return 0

    print("\n [SYSTEM OVERVIEW COUNTS]")
    print(f"  + Registered Accounts : {_count('account_tbl')}")
    print(f"  + Family Members      : {_count('member_tbl')}")
    print(f"  + AI Consultations    : {_count('chat_history_tbl')}")
    print(f"  + Health Articles/Tips: {_count('health_content_tbl')}")
    print(f"  + Admin Profiles      : {_count('admin_tbl')}")
    print(f"  + Password Reset OTPs : {_count('password_reset_otps')}")
    print("-" * 78)
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
    print("-" * 78)
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
                row_str = " | ".join(
                    (str(val)[:28] if val is not None else "NULL").ljust(col_widths[i])
                    for i, val in enumerate(r)
                )
                print(row_str)
    except Exception as err:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"  Error reading table: {err}")

conn.close()
print("\n" + "=" * 78)
print(" Access URLs:")
print(" 1. Web Portal URL  : http://127.0.0.1:5000/home.html")
print(" 2. Symptom Checker : http://127.0.0.1:5000/question_input.html")
print(" 3. Admin Portal    : http://127.0.0.1:5000/admin_login.html (admin@niramaya.com)")
print(" 4. Live Render URL : https://niramaya-health-ai.onrender.com/home.html")
print("=" * 78)
