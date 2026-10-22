import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import bcrypt
from db_config import get_db_connection

def setup_database():
    try:
        # Step 1: Connect to default postgres DB to create projectH database if it doesn't exist
        print("Connecting to PostgreSQL server...")
        conn = get_db_connection(dbname="postgres")
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

        # Step 4: Seed initial approved Health Content if health_content_tbl is empty
        cursor_proj.execute("SELECT COUNT(*) FROM health_content_tbl;")
        content_count = cursor_proj.fetchone()[0]
        if content_count == 0:
            print("Seeding initial approved health content...")
            initial_tips = [
                (
                    "wellness_tip",
                    "Spring Seasonal Wellness",
                    "Spring",
                    "Eat fresh greens, berries, and lean proteins to boost energy. Avoid heavy, oily foods that can cause sluggishness. Stay active with outdoor hikes or cycling.",
                    "Niramaya Health Editorial Team",
                    "published"
                ),
                (
                    "wellness_tip",
                    "Summer Hydration & Energy",
                    "Summer",
                    "Eat hydrating fruits like watermelon and light salads. Avoid excessive caffeine and sugary drinks that dehydrate. Stay active by swimming or jogging early to beat the heat.",
                    "Niramaya Health Editorial Team",
                    "published"
                ),
                (
                    "wellness_tip",
                    "Autumn Warmth & Active Care",
                    "Autumn",
                    "Eat root vegetables, apples, and warm soups for comfort. Avoid processed snacks and excess sugar. Stay active with indoor yoga or pilates as the days cool down.",
                    "Niramaya Health Editorial Team",
                    "published"
                ),
                (
                    "wellness_tip",
                    "Winter Vitality & Defense",
                    "Winter",
                    "Eat hearty stews, citrus fruits, and whole grains for warmth. Avoid high-fat comfort foods and excessive alcohol. Stay active with indoor workouts or winter sports.",
                    "Niramaya Health Editorial Team",
                    "published"
                ),
                (
                    "article",
                    "Artificial Intelligence in Early Health Screening",
                    "AI Health",
                    "Recent studies highlight the transformative potential of machine learning and natural language processing in assisting early symptom analysis and preventative wellness monitoring.",
                    "Europe PMC / Niramaya Research",
                    "published"
                )
            ]

            for item in initial_tips:
                cursor_proj.execute("""
                    INSERT INTO health_content_tbl (content_type, title, category, content, author_or_source, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, item)
            conn_proj.commit()
            print("Initial health content seeded successfully!")
        else:
            print("Health content items already exist.")

        cursor_proj.close()
        conn_proj.close()
        print("Database initialization complete!")


    except Exception as e:
        print(f"Error during database initialization: {e}")

if __name__ == "__main__":
    setup_database()

