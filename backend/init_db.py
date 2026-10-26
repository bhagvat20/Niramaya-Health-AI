import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import bcrypt
from db_config import get_db_connection

def setup_database():
    try:
        conn = get_db_connection(dbname="postgres")
        # If SQLite fallback was returned, schema is already initialized
        if conn.__class__.__name__ == 'SQLiteConnWrapper':
            print("SQLite database active and ready.")
            conn.close()
            return

        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'projectH'")
        exists = cursor.fetchone()
        if not exists:
            print("Creating database 'projectH'...")
            cursor.execute('CREATE DATABASE "projectH"')
            print("Database 'projectH' created successfully.")
        else:
            print("Database 'projectH' already exists.")

        cursor.close()
        conn.close()

        # Step 2: Connect to projectH database and run schema.sql
        print("Connecting to 'projectH' database...")
        conn_proj = get_db_connection(dbname="projectH")
        cursor_proj = conn_proj.cursor()

        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        cursor_proj.execute(schema_sql)
        cursor_proj.execute("ALTER TABLE account_tbl ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL;")
        conn_proj.commit()
        print("Tables and schema migration verified successfully in 'projectH'!")


        # Step 3: Seed initial admin user if admin_tbl is empty
        cursor_proj.execute("SELECT COUNT(*) FROM admin_tbl;")
        admin_count = cursor_proj.fetchone()[0]
        if admin_count == 0:
            print("Seeding default admin user...")
            default_admin_email = "admin@niramaya.com"
            default_admin_username = "admin"
            default_admin_pass = "Admin@1234"
            hashed = bcrypt.hashpw(default_admin_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor_proj.execute("""
                INSERT INTO admin_tbl (username, email, password_hash, role, is_active)
                VALUES (%s, %s, %s, 'admin', TRUE)
            """, (default_admin_username, default_admin_email, hashed))
            conn_proj.commit()
            print("Default admin user created successfully! (username: admin, email: admin@niramaya.com)")
        else:
            print("Admin user(s) already exist.")

        # Step 4: Seed initial approved Health Content if health_content_tbl is empty or partial
        try:
            from seed_data import SEED_ACCOUNTS, SEED_MEMBERS, SEED_CHATS, SEED_HEALTH_CONTENT
        except ImportError:
            SEED_ACCOUNTS, SEED_MEMBERS, SEED_CHATS, SEED_HEALTH_CONTENT = [], [], [], []

        # Seed user accounts if account_tbl is empty
        cursor_proj.execute("SELECT COUNT(*) FROM account_tbl;")
        account_count = cursor_proj.fetchone()[0]
        if account_count == 0 and SEED_ACCOUNTS:
            print("Seeding initial user accounts...")
            for a in SEED_ACCOUNTS:
                cursor_proj.execute("""
                    INSERT INTO account_tbl (account_id, family_name, email, password_hash, created_at, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING;
                """, (a[0], a[1], a[2], a[3], a[4], a[5]))
            conn_proj.commit()
            print(f"Seeded {len(SEED_ACCOUNTS)} user accounts successfully.")

        # Seed members if member_tbl is empty
        cursor_proj.execute("SELECT COUNT(*) FROM member_tbl;")
        member_count = cursor_proj.fetchone()[0]
        if member_count == 0 and SEED_MEMBERS:
            print("Seeding initial family members...")
            for m in SEED_MEMBERS:
                cursor_proj.execute("""
                    INSERT INTO member_tbl (member_id, account_id, name, gender, age, height, weight, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (member_id) DO NOTHING;
                """, (m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7]))
            conn_proj.commit()
            print(f"Seeded {len(SEED_MEMBERS)} family members successfully.")

        # Seed chat history if chat_history_tbl is empty
        cursor_proj.execute("SELECT COUNT(*) FROM chat_history_tbl;")
        chat_count = cursor_proj.fetchone()[0]
        if chat_count == 0 and SEED_CHATS:
            print("Seeding initial disease predictions...")
            for c in SEED_CHATS:
                cursor_proj.execute("""
                    INSERT INTO chat_history_tbl (history_id, account_id, member_id, user_input, bot_response, model, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (history_id) DO NOTHING;
                """, (c[0], c[1], c[2], c[3], c[4], c[5], c[6]))
            conn_proj.commit()
            print(f"Seeded {len(SEED_CHATS)} chats successfully.")

        # Seed full health content if health_content_tbl has fewer than 25 items
        cursor_proj.execute("SELECT COUNT(*) FROM health_content_tbl;")
        content_count = cursor_proj.fetchone()[0]
        if content_count < 25 and SEED_HEALTH_CONTENT:
            print("Seeding full health content items...")
            for h in SEED_HEALTH_CONTENT:
                cursor_proj.execute("""
                    INSERT INTO health_content_tbl (content_id, content_type, title, category, content, author_or_source, external_link, image_url, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (content_id) DO UPDATE SET
                        content_type = EXCLUDED.content_type,
                        title = EXCLUDED.title,
                        category = EXCLUDED.category,
                        content = EXCLUDED.content,
                        status = EXCLUDED.status;
                """, (h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8], h[9], h[10]))
            conn_proj.commit()
            print(f"Seeded {len(SEED_HEALTH_CONTENT)} health content items successfully.")

        # Update PostgreSQL sequence values to prevent auto-increment conflicts
        try:
            cursor_proj.execute("SELECT setval(pg_get_serial_sequence('account_tbl', 'account_id'), COALESCE(MAX(account_id), 1)) FROM account_tbl;")
            cursor_proj.execute("SELECT setval(pg_get_serial_sequence('member_tbl', 'member_id'), COALESCE(MAX(member_id), 1)) FROM member_tbl;")
            cursor_proj.execute("SELECT setval(pg_get_serial_sequence('chat_history_tbl', 'history_id'), COALESCE(MAX(history_id), 1)) FROM chat_history_tbl;")
            cursor_proj.execute("SELECT setval(pg_get_serial_sequence('health_content_tbl', 'content_id'), COALESCE(MAX(content_id), 1)) FROM health_content_tbl;")
            conn_proj.commit()
        except Exception:
            pass

        cursor_proj.close()
        conn_proj.close()
        print("Database initialization complete!")

    except Exception as e:
        print(f"Error during database initialization: {e}")

if __name__ == "__main__":
    setup_database()

