import os
import psycopg2

def get_db_connection(dbname="projectH"):
    """
    Establishes a PostgreSQL database connection using configured environment variables
    or fallback passwords ('1234', 'postgres').
    """
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Handles postgres:// to postgresql:// for compatibility with newer psycopg2
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(database_url, connect_timeout=4)

    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    user = os.environ.get("DB_USER", "postgres")
    env_password = os.environ.get("DB_PASSWORD")

    passwords_to_try = []
    if env_password:
        passwords_to_try.append(env_password)
    passwords_to_try.extend(["1234", "postgres"])

    last_error = None
    for pwd in passwords_to_try:
        try:
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=pwd,
                host=host,
                port=port,
                connect_timeout=3
            )
            return conn
        except Exception as e:
            last_error = e

    if last_error:
        raise last_error
    raise Exception("Could not connect to PostgreSQL database.")
