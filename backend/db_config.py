import os
import re
import sqlite3
import psycopg2

def _sqlite_split_part(string, delimiter, part):
    if string is None:
        return ""
    parts = str(string).split(str(delimiter))
    try:
        idx = int(part) - 1
        return parts[idx] if 0 <= idx < len(parts) else ""
    except Exception:
        return ""

class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self._last_id = None

    def execute(self, sql, params=None):
        clean_sql = re.sub(r'::\w+', '', sql)
        clean_sql = re.sub(r'\bILIKE\b', 'LIKE', clean_sql, flags=re.IGNORECASE)
        clean_sql = clean_sql.replace('%s', '?')
        self._last_id = None
        if params is None:
            self.cursor.execute(clean_sql)
        else:
            # Convert datetime objects to ISO strings to avoid Python 3.12 sqlite3 deprecation warnings
            from datetime import datetime
            safe_params = tuple(
                p.isoformat(sep=' ') if isinstance(p, datetime) else p
                for p in params
            ) if isinstance(params, (tuple, list)) else params
            self.cursor.execute(clean_sql, safe_params)
        return self

    def fetchone(self):
        if self._last_id is not None:
            val = (self._last_id,)
            self._last_id = None
            return val
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def close(self):
        try:
            self.cursor.close()
        except Exception:
            pass

    @property
    def rowcount(self):
        try:
            return self.cursor.rowcount
        except Exception:
            return 0

class SQLiteConnWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        try:
            self.conn.commit()
        except Exception:
            pass

    def rollback(self):
        try:
            self.conn.rollback()
        except Exception:
            pass

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

    def set_isolation_level(self, level):
        pass

_sqlite_initialized = False
_working_pg_pwd = None

def init_sqlite_db(db_path):
    """Initializes tables and seeds default data in SQLite once if not present."""
    global _sqlite_initialized
    if _sqlite_initialized and os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    conn.create_function("split_part", 3, _sqlite_split_part)
    conn.create_function("SPLIT_PART", 3, _sqlite_split_part)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS account_tbl (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS member_tbl (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            height TEXT,
            weight TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS chat_history_tbl (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            user_input TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            model TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS admin_tbl (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS admin_tokens_tbl (
            token_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        );
        CREATE TABLE IF NOT EXISTS health_content_tbl (
            content_id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT,
            content TEXT NOT NULL,
            author_or_source TEXT,
            external_link TEXT,
            image_url TEXT,
            status TEXT DEFAULT 'published',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS password_reset_otps (
            otp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Seed default admin if empty
    cur.execute("SELECT COUNT(*) FROM admin_tbl")
    if cur.fetchone()[0] == 0:
        import bcrypt
        hashed = bcrypt.hashpw("Admin@1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("""
            INSERT INTO admin_tbl (username, email, password_hash, role, is_active)
            VALUES ('admin', 'admin@niramaya.com', ?, 'admin', 1)
        """, (hashed,))

    try:
        from seed_data import SEED_HEALTH_CONTENT
    except ImportError:
        SEED_HEALTH_CONTENT = []

    # Seed health content only (never re-seed dummy user accounts so deleted users stay deleted!)
    cur.execute("SELECT COUNT(*) FROM health_content_tbl")
    if cur.fetchone()[0] < 25 and SEED_HEALTH_CONTENT:
        for h in SEED_HEALTH_CONTENT:
            cur.execute("""
                INSERT OR REPLACE INTO health_content_tbl (content_id, content_type, title, category, content, author_or_source, external_link, image_url, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8], h[9], h[10]))

    conn.commit()
    conn.close()
    _sqlite_initialized = True

def get_db_connection(dbname="projectH"):
    """
    Establishes database connection with instant caching:
    1. DATABASE_URL (Render PostgreSQL or cloud DB)
    2. Localhost PostgreSQL with cached working password
    3. SQLite Fallback (one-time setup, zero-delay connections)
    """
    global _working_pg_pwd

    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        try:
            return psycopg2.connect(database_url, connect_timeout=15)
        except Exception as e:
            print(f"[!] Warning: DATABASE_URL connection failed: {e}")

    # Try local PostgreSQL (on localhost)
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    user = os.environ.get("DB_USER", "postgres")
    env_password = os.environ.get("DB_PASSWORD")

    # Fast path: try cached working password first if available
    if _working_pg_pwd is not None:
        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=_working_pg_pwd,
                host=host,
                port=port,
                connect_timeout=1
            )
            return conn
        except Exception:
            _working_pg_pwd = None

    passwords_to_try = []
    if env_password:
        passwords_to_try.append(env_password)
    passwords_to_try.extend(["1234", "postgres"])

    for pwd in passwords_to_try:
        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=pwd,
                host=host,
                port=port,
                connect_timeout=1
            )
            _working_pg_pwd = pwd
            return conn
        except Exception:
            pass

    # Seamless SQLite fallback if PostgreSQL is not running
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sqlite_path = os.path.join(base_dir, "niramaya.db")
    init_sqlite_db(sqlite_path)
    sqlite_conn = sqlite3.connect(sqlite_path, check_same_thread=False)
    sqlite_conn.create_function("split_part", 3, _sqlite_split_part)
    sqlite_conn.create_function("SPLIT_PART", 3, _sqlite_split_part)
    return SQLiteConnWrapper(sqlite_conn)
