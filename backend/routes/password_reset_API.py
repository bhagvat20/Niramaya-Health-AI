from flask import Blueprint, request, jsonify
from flask_cors import CORS
import psycopg2
import bcrypt
import random
import string
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from db_config import get_db_connection

# Create Blueprint for password reset routes
password_reset_bp = Blueprint('password_reset', __name__)
CORS(password_reset_bp)

# Database connection helper
def connect_db():
    return get_db_connection()


# Generate 6-digit OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# Send OTP email
def send_otp_email(email, otp):
    try:
        msg = MIMEText(f'Your OTP for password reset is: {otp}\nIt is valid only one time.')
        msg['Subject'] = 'Niramaya Password Reset OTP'
        msg['From'] = GMAIL_USER
        msg['To'] = email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.set_debuglevel(1)  # Enable debug output
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, email, msg.as_string())
        print(f"OTP email sent to {email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected Error sending email: {e}")
        return False

# Forgot Password API
@password_reset_bp.route('/forgotpassword', methods=['POST'])
def forgot_password():
    conn = None
    cursor = None
    try:
        data = request.json or {}
        email = data.get('email')

        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400

        conn = connect_db()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute("SELECT account_id, email FROM account_tbl WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"success": False, "message": "Email not found"}), 404

        # Generate OTP
        otp = generate_otp()

        # Send OTP via email
        if send_otp_email(email, otp):
            return jsonify({
                "success": True,
                "message": "OTP sent to your email",
                "otp": otp,
                "account_id": user[0]
            }), 200
        else:
            return jsonify({"success": False, "message": "Failed to send OTP"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Reset Password API
@password_reset_bp.route('/resetpassword', methods=['POST'])
def reset_password():
    conn = None
    cursor = None
    try:
        data = request.json or {}
        account_id = data.get('account_id')
        new_password = data.get('new_password')

        if not account_id or not new_password:
            return jsonify({"success": False, "message": "Account ID and new password are required"}), 400

        conn = connect_db()
        cursor = conn.cursor()
        
        # Verify account exists
        cursor.execute("SELECT account_id FROM account_tbl WHERE account_id = %s", (account_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({"success": False, "message": "Account not found"}), 404

        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update password
        cursor.execute(
            "UPDATE account_tbl SET password_hash = %s WHERE account_id = %s",
            (hashed_password.decode('utf-8'), account_id)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Password reset successfully",
            "account_id": account_id
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Change Password API (for logged-in users — verifies current password first)
@password_reset_bp.route('/changepassword', methods=['POST'])
def change_password():
    conn = None
    cursor = None
    try:
        data = request.json or {}
        account_id = data.get('account_id')
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not account_id or not current_password or not new_password:
            return jsonify({"success": False, "message": "All fields are required."}), 400

        if len(new_password) < 6:
            return jsonify({"success": False, "message": "New password must be at least 6 characters."}), 400

        conn = connect_db()
        cursor = conn.cursor()

        # Fetch current hashed password
        cursor.execute("SELECT password_hash FROM account_tbl WHERE account_id = %s", (account_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "Account not found."}), 404

        stored_hash = user[0]

        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash.encode('utf-8')):
            return jsonify({"success": False, "message": "Current password is incorrect."}), 401

        # Hash and save the new password
        new_hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "UPDATE account_tbl SET password_hash = %s WHERE account_id = %s",
            (new_hashed.decode('utf-8'), account_id)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Password changed successfully."}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()