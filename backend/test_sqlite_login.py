import sqlite3
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db_config import init_sqlite_db, SQLiteConnWrapper, _sqlite_split_part

def test_login_sqlite():
    db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_login_temp.db')
    if os.path.exists(db_file):
        os.remove(db_file)

    try:
        init_sqlite_db(db_file)
        raw_conn = sqlite3.connect(db_file)
        raw_conn.create_function('split_part', 3, _sqlite_split_part)
        raw_conn.create_function('SPLIT_PART', 3, _sqlite_split_part)
        cur = SQLiteConnWrapper(raw_conn).cursor()

        # Insert a test user
        cur.execute("INSERT INTO account_tbl (family_name, email, password_hash, is_active) VALUES (%s, %s, %s, %s)",
                    ('Aniket', 'aniket@gmail.com', 'test_hash', 1))
        raw_conn.commit()

        # Test the query from user_login_API.py
        ident_lower = 'aniket@gmail.com'
        acc_id_val = -1

        cur.execute("""
            SELECT account_id, password_hash, family_name, is_active, email
            FROM account_tbl 
            WHERE LOWER(email) = %s 
               OR LOWER(family_name) = %s 
               OR account_id = %s
            ORDER BY account_id ASC
            LIMIT 1
        """, (ident_lower, ident_lower, acc_id_val))
        res = cur.fetchone()
        print('SQLite query result:', res)
        assert res is not None, "Failed to find user in SQLite"
        assert res[2] == 'Aniket'

        # Test split_part function
        cur.execute("SELECT SPLIT_PART('aniket@gmail.com', '@', 1)")
        udf_res = cur.fetchone()
        print('SQLite SPLIT_PART UDF result:', udf_res)
        assert udf_res[0] == 'aniket', f"Expected 'aniket', got {udf_res[0]}"

        raw_conn.close()
        print('SUCCESS: SQLite login query and fallback UDF passed with zero errors!')
    finally:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass

if __name__ == '__main__':
    test_login_sqlite()
