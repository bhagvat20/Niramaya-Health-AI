from flask import Blueprint, request, jsonify
from flask_cors import CORS
import psycopg2
import bcrypt

from db_config import get_db_connection

# Create a Blueprint for register routes
register_bp = Blueprint('register', __name__)
CORS(register_bp)

def connect_db():
    return get_db_connection()


@register_bp.route('/register', methods=['POST'])
def register_user():
    conn = None
    cursor = None
    try:
        data = request.json or {}
        fname = (data.get('fname') or data.get('familyname') or data.get('family_name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password')

        if not email or not fname or not password:
            return jsonify({"success": False, "message": "Email, family name and password are required"}), 400

        hashed_psw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = connect_db()
        cursor = conn.cursor()

        # Check existing email case-insensitively
        cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "This email is already registered. Please login or use a different email."}), 400

        cursor.execute(
            "INSERT INTO account_tbl (email, password_hash, family_name) VALUES (%s, %s, %s) RETURNING account_id",
            (email, hashed_psw.decode('utf-8'), fname)
        )
        account_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            "success": True,
            "account_id": str(account_id),
            "familyname": fname,
            "email": email,
            "message": "Registration successful"
        }), 200

    except psycopg2.IntegrityError:
        return jsonify({"success": False, "message": "Email already exists"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()