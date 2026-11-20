import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import bcrypt
from db_config import get_db_connection

def setup_database():
    try:
        database_url = os.environ.get("DATABASE_URL")

        if database_url:
            # Cloud PostgreSQL (Render / Neon): database already exists; connect directly
            print("Connecting to cloud PostgreSQL via DATABASE_URL...")
            conn_proj = get_db_connection()
            if conn_proj.__class__.__name__ == 'SQLiteConnWrapper':
                print("SQLite fallback database active and ready.")
                conn_proj.close()
                return
        else:
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

            # Ensure schema also exists in default 'postgres' database for pgAdmin 4 viewers
            try:
                schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
                with open(schema_path, 'r', encoding='utf-8') as f:
                    cursor.execute(f.read())
                for tbl, col in [
                    ('account_tbl', 'account_id'),
                    ('member_tbl', 'member_id'),
                    ('chat_history_tbl', 'history_id'),
                    ('admin_tbl', 'admin_id'),
                    ('admin_tokens_tbl', 'token_id'),
                    ('health_content_tbl', 'content_id'),
                    ('password_reset_otps', 'otp_id'),
                ]:
                    try:
                        cursor.execute(
                            f"SELECT setval(pg_get_serial_sequence('{tbl}', '{col}'), COALESCE((SELECT MAX({col}) FROM {tbl}), 1), (SELECT COUNT(*) > 0 FROM {tbl}));"
                        )
                    except Exception:
                        pass
            except Exception:
                pass

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

        # Step 4: Seed initial approved Health Content only (never re-seed dummy user accounts so deleted users never come back)
        try:
            from seed_data import SEED_HEALTH_CONTENT
        except ImportError:
            SEED_HEALTH_CONTENT = []

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
        for tbl, col in [
            ('account_tbl', 'account_id'),
            ('member_tbl', 'member_id'),
            ('chat_history_tbl', 'history_id'),
            ('admin_tbl', 'admin_id'),
            ('admin_tokens_tbl', 'token_id'),
            ('health_content_tbl', 'content_id'),
            ('password_reset_otps', 'otp_id'),
        ]:
            try:
                cursor_proj.execute(
                    f"SELECT setval(pg_get_serial_sequence('{tbl}', '{col}'), COALESCE((SELECT MAX({col}) FROM {tbl}), 1), (SELECT COUNT(*) > 0 FROM {tbl}));"
                )
                conn_proj.commit()
            except Exception:
                try:
                    conn_proj.rollback()
                except Exception:
                    pass

        cursor_proj.close()
        conn_proj.close()
        print("Database initialization complete!")

    except Exception as e:
        print(f"Error during database initialization: {e}")

if __name__ == "__main__":
    setup_database()

