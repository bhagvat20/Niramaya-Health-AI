from flask import Blueprint, request, jsonify
from flask_cors import CORS
import re
import sqlite3
import psycopg2
import bcrypt

from db_config import get_db_connection

# Create a Blueprint for register routes
register_bp = Blueprint('register', __name__)
CORS(register_bp)


def connect_db():
    return get_db_connection()


def _sync_account_sequence(conn, cursor):
    """Repairs PostgreSQL serial sequence on account_tbl if seeded rows left it behind."""
    try:
        conn.rollback()
        cursor.execute(
            "SELECT setval(pg_get_serial_sequence('account_tbl', 'account_id'), "
            "COALESCE((SELECT MAX(account_id) FROM account_tbl), 1), "
            "(SELECT COUNT(*) > 0 FROM account_tbl));"
        )
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass


@register_bp.route('/register', methods=['POST'])
def register_user():
    conn = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        fname = (data.get('fname') or data.get('familyname') or data.get('family_name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = (data.get('password') or '').strip()

        if not email or not fname or not password:
            return jsonify({"success": False, "message": "Email, family name and password are required"}), 400

        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return jsonify({"success": False, "message": "Please enter a valid email address."}), 400

        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters long."}), 400

        hashed_psw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn = connect_db()
        cursor = conn.cursor()

        # Check existing email case-insensitively
        cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s", (email,))
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "This email is already registered. Please login or use a different email."
            }), 400

        # Insert account (with automatic PostgreSQL sequence recovery if primary key collided)
        try:
            cursor.execute(
                "INSERT INTO account_tbl (email, password_hash, family_name) VALUES (%s, %s, %s) RETURNING account_id",
                (email, hashed_psw, fname)
            )
            account_id = cursor.fetchone()[0]
            conn.commit()
        except psycopg2.IntegrityError as ie:
            err_msg = str(ie).lower()
            if 'account_tbl_pkey' in err_msg or 'account_id' in err_msg:
                _sync_account_sequence(conn, cursor)
                cursor.execute(
                    "INSERT INTO account_tbl (email, password_hash, family_name) VALUES (%s, %s, %s) RETURNING account_id",
                    (email, hashed_psw, fname)
                )
                account_id = cursor.fetchone()[0]
                conn.commit()
            else:
                conn.rollback()
                return jsonify({
                    "success": False,
                    "message": "This email is already registered. Please login or use a different email."
                }), 400
        except sqlite3.IntegrityError:
            conn.rollback()
            return jsonify({
                "success": False,
                "message": "This email is already registered. Please login or use a different email."
            }), 400

        return jsonify({
            "success": True,
            "account_id": str(account_id),
            "familyname": fname,
            "email": email,
            "message": "Registration successful"
        }), 200

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Registration error: {e}")
        return jsonify({"success": False, "message": f"Registration error: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
