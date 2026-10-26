from flask import Blueprint, request, jsonify
from flask_cors import CORS
import psycopg2
import bcrypt

from db_config import get_db_connection

# Create a Blueprint for user login routes
login_bp = Blueprint('login', __name__)
CORS(login_bp)

def connect_db():
    return get_db_connection()


@login_bp.route('/userlogin', methods=['POST'])
def user_login():
    conn = None
    cursor = None
    try:
        data = request.json or {}
        email = (data.get('email') or '').strip().lower()
        password = (data.get('password') or '').strip()

        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required"}), 400

        conn = connect_db()
        cursor = conn.cursor()
        
        # First, get account details (case-insensitive email)
        cursor.execute("""
            SELECT account_id, password_hash, family_name, is_active 
            FROM account_tbl 
            WHERE LOWER(email) = %s
        """, (email,))
        account_row = cursor.fetchone()
        
        if not account_row:
            return jsonify({"success": False, "message": "User not found"}), 400

        account_id, stored_password, familyname, is_active = account_row
        
        if not is_active:
            return jsonify({"success": False, "message": "Account is deactivated. Please contact administrator."}), 403

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return jsonify({"success": False, "message": "Incorrect password"}), 400

        # Fetch members associated with this account
        cursor.execute("""
            SELECT member_id, name 
            FROM member_tbl 
            WHERE account_id = %s
        """, (account_id,))
        members = cursor.fetchall() or []

        # Prepare member data for response (empty if user has not added any member)
        members_list = [
            {"member_id": str(member[0]), "name": member[1], "account_id": str(account_id)}
            for member in members
        ]

        # Return success response with member information
        return jsonify({
            "success": True,
            "message": "Login successful",
            "account_id": str(account_id),
            "email": email,
            "familyname": familyname,
            "members": members_list
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()