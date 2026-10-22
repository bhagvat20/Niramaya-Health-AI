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
        data = request.json
        fname = data.get('fname')
        email = data.get('email')
        password = data.get('password')

        if not email or not fname or not password:
            return jsonify({"success": False, "message": "Email, family name and password are required"}), 400

        hashed_psw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO account_tbl (email, password_hash, family_name) VALUES (%s, %s, %s) RETURNING account_id",
            (email, hashed_psw.decode('utf-8'), fname)
        )
        account_id = cursor.fetchone()[0]
        conn.commit()
        return jsonify({"success": True, "account_id": account_id, "message": "Registration successful"}), 200

    except psycopg2.IntegrityError:
        return jsonify({"success": False, "message": "Email already exists"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()