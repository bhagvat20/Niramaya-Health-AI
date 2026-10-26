import os
import re
import sqlite3
import psycopg2

class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self._last_id = None

    def execute(self, sql, params=None):
        has_returning = bool(re.search(r'RETURNING\s+\w+', sql, re.IGNORECASE))
        clean_sql = re.sub(r'RETURNING\s+\w+', '', sql, flags=re.IGNORECASE)
        clean_sql = clean_sql.replace('::text', '')
        clean_sql = re.sub(r'\bILIKE\b', 'LIKE', clean_sql, flags=re.IGNORECASE)
        clean_sql = clean_sql.replace('%s', '?')
        if params is None:
            self.cursor.execute(clean_sql)
        else:
            self.cursor.execute(clean_sql, params)
        if has_returning:
            self._last_id = self.cursor.lastrowid
        else:
            self._last_id = None
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

def init_sqlite_db(db_path):
    """Initializes tables and seeds default data in SQLite if not present."""
    conn = sqlite3.connect(db_path)
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
        from seed_data import SEED_ACCOUNTS, SEED_MEMBERS, SEED_CHATS, SEED_HEALTH_CONTENT
    except ImportError:
        SEED_ACCOUNTS, SEED_MEMBERS, SEED_CHATS, SEED_HEALTH_CONTENT = [], [], [], []

    # Seed accounts
    cur.execute("SELECT COUNT(*) FROM account_tbl")
    if cur.fetchone()[0] == 0 and SEED_ACCOUNTS:
        for a in SEED_ACCOUNTS:
            cur.execute("""
                INSERT OR IGNORE INTO account_tbl (account_id, family_name, email, password_hash, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (a[0], a[1], a[2], a[3], a[4], 1 if a[5] else 0))

    # Seed members
    cur.execute("SELECT COUNT(*) FROM member_tbl")
    if cur.fetchone()[0] == 0 and SEED_MEMBERS:
        for m in SEED_MEMBERS:
            cur.execute("""
                INSERT OR IGNORE INTO member_tbl (member_id, account_id, name, gender, age, height, weight, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7]))

    # Seed chats
    cur.execute("SELECT COUNT(*) FROM chat_history_tbl")
    if cur.fetchone()[0] == 0 and SEED_CHATS:
        for c in SEED_CHATS:
            cur.execute("""
                INSERT OR IGNORE INTO chat_history_tbl (history_id, account_id, member_id, user_input, bot_response, model, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (c[0], c[1], c[2], c[3], c[4], c[5], c[6]))

    # Seed health content
    cur.execute("SELECT COUNT(*) FROM health_content_tbl")
    if cur.fetchone()[0] < 25 and SEED_HEALTH_CONTENT:
        for h in SEED_HEALTH_CONTENT:
            cur.execute("""
                INSERT OR REPLACE INTO health_content_tbl (content_id, content_type, title, category, content, author_or_source, external_link, image_url, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8], h[9], h[10]))

    conn.commit()
    conn.close()

def get_db_connection(dbname="projectH"):
    """
    Establishes database connection:
    1. DATABASE_URL (Render PostgreSQL or cloud DB)
    2. Localhost PostgreSQL (user laptop)
    3. SQLite Fallback (Render without database or machines without PostgreSQL)
    """
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        try:
            return psycopg2.connect(database_url, connect_timeout=4)
        except Exception as e:
            print(f"[!] Warning: DATABASE_URL connection failed: {e}")

    # Try local PostgreSQL (on localhost)
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    user = os.environ.get("DB_USER", "postgres")
    env_password = os.environ.get("DB_PASSWORD")

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
                connect_timeout=2
            )
            return conn
        except Exception:
            pass

    # Seamless SQLite fallback if PostgreSQL is not running
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sqlite_path = os.path.join(base_dir, "niramaya.db")
    init_sqlite_db(sqlite_path)
    sqlite_conn = sqlite3.connect(sqlite_path, check_same_thread=False)
    return SQLiteConnWrapper(sqlite_conn)
