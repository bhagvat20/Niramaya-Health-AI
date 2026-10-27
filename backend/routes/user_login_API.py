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
            # Check Cloud deployment (Render) if account was registered on cloud
            try:
                import urllib.request
                import json
                req = urllib.request.Request(
                    'https://niramaya-health-ai.onrender.com/userlogin',
                    data=json.dumps({'email': email, 'password': password}).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    cdata = json.loads(resp.read().decode('utf-8'))
                    if cdata.get('success'):
                        c_acc_id = int(cdata['account_id'])
                        c_fname = cdata.get('familyname', 'Family')
                        pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        cursor.execute("""
                            INSERT INTO account_tbl (account_id, family_name, email, password_hash, is_active)
                            VALUES (%s, %s, %s, %s, TRUE)
                            ON CONFLICT (account_id) DO UPDATE SET email = EXCLUDED.email, password_hash = EXCLUDED.password_hash
                        """, (c_acc_id, c_fname, email, pwd_hash))
                        
                        for m in cdata.get('members', []):
                            cursor.execute("""
                                INSERT INTO member_tbl (member_id, account_id, name, gender, age, height, weight)
                                VALUES (%s, %s, %s, 'Other', 25, '170', '65')
                                ON CONFLICT (member_id) DO NOTHING
                            """, (int(m['member_id']), c_acc_id, m['name']))
                        conn.commit()
                        return jsonify(cdata), 200
            except urllib.error.HTTPError as he:
                try:
                    err_json = json.loads(he.read().decode('utf-8'))
                    if err_json.get('message') == 'Incorrect password':
                        return jsonify({"success": False, "message": "Incorrect password"}), 400
                except Exception:
                    pass
            except Exception:
                pass

            return jsonify({"success": False, "message": "User not found"}), 400

        account_id, stored_password, familyname, is_active = account_row
        
        if not is_active:
            return jsonify({"success": False, "message": "Account is deactivated. Please contact administrator."}), 403

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            # If local password check failed (e.g. account was synced from cloud with dummy hash), verify with cloud
            cloud_verified = False
            try:
                import urllib.request
                import json
                req = urllib.request.Request(
                    'https://niramaya-health-ai.onrender.com/userlogin',
                    data=json.dumps({'email': email, 'password': password}).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=4) as resp:
                    cdata = json.loads(resp.read().decode('utf-8'))
                    if cdata.get('success'):
                        cloud_verified = True
                        new_pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        cursor.execute("UPDATE account_tbl SET password_hash = %s WHERE account_id = %s", (new_pwd_hash, account_id))
                        conn.commit()
                        return jsonify(cdata), 200
            except Exception:
                pass

            if not cloud_verified:
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