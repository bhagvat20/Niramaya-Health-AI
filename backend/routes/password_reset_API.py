from flask import Blueprint, request, jsonify
from flask_cors import CORS
import os
import json
import random
import string
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
import bcrypt

from db_config import get_db_connection

# Create Blueprint for password reset routes
password_reset_bp = Blueprint('password_reset', __name__)
CORS(password_reset_bp)


def connect_db():
    return get_db_connection()


def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def _ensure_otp_table(conn, cursor):
    """Ensure password_reset_otps table exists on both PostgreSQL and SQLite."""
    is_sqlite = conn.__class__.__name__ == 'SQLiteConnWrapper'
    if is_sqlite:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_otps (
                otp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                otp_code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_otps (
                otp_id SERIAL PRIMARY KEY,
                account_id INT NOT NULL REFERENCES account_tbl(account_id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                otp_code VARCHAR(10) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()


def _build_otp_email_bodies(otp):
    plain = (
        f"Hello,\n\n"
        f"Your Niramaya Health AI password reset verification OTP is: {otp}\n\n"
        f"This code is valid for 10 minutes and can be used only once.\n"
        f"If you did not request a password reset, please ignore this email.\n\n"
        f"— Niramaya Health AI Team"
    )
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; background: #0f172a; color: #f8fafc; border-radius: 12px;">
        <h2 style="color: #60a5fa; margin-top: 0;">Niramaya Health AI — Password Reset</h2>
        <p style="color: #cbd5e1; font-size: 15px;">Use the one-time verification code below to reset your password:</p>
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 18px; text-align: center; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #34d399;">{otp}</span>
        </div>
        <p style="color: #94a3b8; font-size: 13px;">This OTP expires in <strong>10 minutes</strong> and can only be used once.</p>
        <p style="color: #64748b; font-size: 12px; margin-top: 24px;">If you did not request this reset, you can safely ignore this email.</p>
    </div>
    """
    return plain, html


def send_otp_email(email, otp):
    """
    Attempts to send real OTP email via:
    1. Resend HTTPS API (RESEND_API_KEY) - works on Render free tier
    2. Brevo HTTPS API (BREVO_API_KEY) - works on Render free tier
    3. SMTP (SMTP_HOST/SMTP_USER/SMTP_PASS or GMAIL_USER/GMAIL_PASS) - tries 587 STARTTLS then 465 SSL
    Returns (sent: bool, detail: str).
    """
    plain_body, html_body = _build_otp_email_bodies(otp)
    subject = "Niramaya Health AI — Password Reset OTP"

    # 1. Resend API (HTTPS, never blocked by Render)
    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    if resend_key:
        sender = os.environ.get("EMAIL_FROM", "Niramaya Health AI <onboarding@resend.dev>").strip()
        try:
            payload = json.dumps({
                "from": sender,
                "to": [email],
                "subject": subject,
                "html": html_body,
                "text": plain_body
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=payload,
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "NiramayaHealthAI/1.0"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    print(f"[OTP] Email sent via Resend API to {email}")
                    return True, "resend"
        except Exception as e:
            print(f"[OTP] Resend API failed: {e}")

    # 2. Brevo API (HTTPS, free tier, never blocked by Render)
    brevo_key = os.environ.get("BREVO_API_KEY", "").strip()
    if brevo_key:
        sender_email = (
            os.environ.get("BREVO_SENDER_EMAIL")
            or os.environ.get("GMAIL_USER")
            or "niramaya.health.ai@gmail.com"
        ).strip()
        try:
            payload = json.dumps({
                "sender": {"name": "Niramaya Health AI", "email": sender_email},
                "to": [{"email": email}],
                "subject": subject,
                "htmlContent": html_body,
                "textContent": plain_body
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=payload,
                headers={
                    "api-key": brevo_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    print(f"[OTP] Email sent via Brevo API to {email}")
                    return True, "brevo"
        except Exception as e:
            print(f"[OTP] Brevo API failed: {e}")

    # 3. SMTP (Gmail App Password or custom SMTP)
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_user = (os.environ.get("SMTP_USER") or os.environ.get("GMAIL_USER") or "").strip()
    smtp_pass_raw = (os.environ.get("SMTP_PASS") or os.environ.get("GMAIL_PASS") or "").strip()
    # Google displays 16-char App Passwords with spaces ("xxxx xxxx xxxx xxxx"); strip spaces for Gmail SMTP
    smtp_pass = smtp_pass_raw.replace(" ", "") if "gmail" in smtp_host.lower() else smtp_pass_raw

    if smtp_user and smtp_pass:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Niramaya Health AI <{smtp_user}>"
        msg["To"] = email
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Try STARTTLS (port 587) first, then SSL (port 465)
        custom_port = os.environ.get("SMTP_PORT", "").strip()
        ports_to_try = [int(custom_port)] if custom_port.isdigit() else [587, 465]
        last_err = ""
        for port in ports_to_try:
            try:
                if port == 465:
                    with smtplib.SMTP_SSL(smtp_host, 465, timeout=12) as server:
                        server.login(smtp_user, smtp_pass)
                        server.sendmail(smtp_user, email, msg.as_string())
                else:
                    with smtplib.SMTP(smtp_host, port, timeout=12) as server:
                        server.ehlo()
                        server.starttls()
                        server.ehlo()
                        server.login(smtp_user, smtp_pass)
                        server.sendmail(smtp_user, email, msg.as_string())
                print(f"[OTP] Email sent via SMTP ({smtp_host}:{port}) to {email}")
                return True, f"smtp:{port}"
            except Exception as e:
                last_err = str(e)
                print(f"[OTP] SMTP ({smtp_host}:{port}) error: {e}")
        return False, f"smtp_failed: {last_err}"

    print(f"[OTP ON-SCREEN MODE] No email provider configured. OTP for {email}: {otp}")
    return False, "not_configured"


@password_reset_bp.route('/forgotpassword/status', methods=['GET'])
def email_provider_status():
    """Diagnostic endpoint showing whether an email OTP provider is configured (no secrets exposed)."""
    if os.environ.get("RESEND_API_KEY", "").strip():
        return jsonify({"configured": True, "provider": "resend"}), 200
    if os.environ.get("BREVO_API_KEY", "").strip():
        return jsonify({"configured": True, "provider": "brevo"}), 200
    if (os.environ.get("SMTP_USER") or os.environ.get("GMAIL_USER") or "").strip() and (
        os.environ.get("SMTP_PASS") or os.environ.get("GMAIL_PASS") or ""
    ).strip():
        return jsonify({"configured": True, "provider": "smtp"}), 200
    return jsonify({"configured": False, "provider": "none"}), 200


# Forgot Password API
@password_reset_bp.route('/forgotpassword', methods=['POST'])
def forgot_password():
    conn = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()

        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400

        conn = connect_db()
        cursor = conn.cursor()
        _ensure_otp_table(conn, cursor)

        # Case-insensitive email lookup
        cursor.execute(
            "SELECT account_id, email FROM account_tbl WHERE LOWER(email) = %s LIMIT 1",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({
                "success": False,
                "message": "No account found with this email address. Please check your email or register first."
            }), 404

        account_id, registered_email = user[0], user[1]
        otp = generate_otp()
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)
        is_sqlite = conn.__class__.__name__ == 'SQLiteConnWrapper'

        # Invalidate previous unused OTPs for this account
        if is_sqlite:
            cursor.execute("UPDATE password_reset_otps SET used = 1 WHERE account_id = %s AND used = 0", (account_id,))
            cursor.execute(
                "INSERT INTO password_reset_otps (account_id, email, otp_code, expires_at, used) VALUES (%s, %s, %s, %s, 0)",
                (account_id, registered_email, otp, expires_at.isoformat())
            )
        else:
            cursor.execute("UPDATE password_reset_otps SET used = TRUE WHERE account_id = %s AND used = FALSE", (account_id,))
            cursor.execute(
                "INSERT INTO password_reset_otps (account_id, email, otp_code, expires_at, used) VALUES (%s, %s, %s, %s, FALSE)",
                (account_id, registered_email, otp, expires_at)
            )
        conn.commit()

        email_sent, provider_info = send_otp_email(registered_email, otp)

        if email_sent:
            return jsonify({
                "success": True,
                "email_sent": True,
                "delivery_method": "email",
                "message": f"A 6-digit OTP has been sent to {registered_email}. Please check your inbox (and spam folder).",
                "account_id": account_id
            }), 200
        else:
            return jsonify({
                "success": True,
                "email_sent": False,
                "delivery_method": "on_screen",
                "reason": provider_info,
                "message": "Email delivery is not configured on the server yet. Use the 6-digit verification OTP shown on screen to reset your password.",
                "otp": otp,
                "account_id": account_id
            }), 200

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Forgot password error: {e}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
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
        data = request.get_json(silent=True) or {}
        account_id = data.get('account_id')
        otp = (data.get('otp') or '').strip()
        new_password = (data.get('new_password') or '').strip()

        if not account_id or not new_password:
            return jsonify({"success": False, "message": "Account ID and new password are required"}), 400

        if len(new_password) < 6:
            return jsonify({"success": False, "message": "New password must be at least 6 characters long."}), 400

        try:
            account_id = int(account_id)
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid account ID"}), 400

        conn = connect_db()
        cursor = conn.cursor()
        _ensure_otp_table(conn, cursor)
        is_sqlite = conn.__class__.__name__ == 'SQLiteConnWrapper'

        # Verify account exists
        cursor.execute("SELECT account_id FROM account_tbl WHERE account_id = %s", (account_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"success": False, "message": "Account not found"}), 404

        # Verify OTP server-side when provided
        if otp:
            if is_sqlite:
                cursor.execute(
                    "SELECT otp_id, otp_code, expires_at FROM password_reset_otps "
                    "WHERE account_id = %s AND used = 0 ORDER BY otp_id DESC LIMIT 1",
                    (account_id,)
                )
            else:
                cursor.execute(
                    "SELECT otp_id, otp_code, expires_at FROM password_reset_otps "
                    "WHERE account_id = %s AND used = FALSE ORDER BY otp_id DESC LIMIT 1",
                    (account_id,)
                )
            otp_row = cursor.fetchone()
            if not otp_row:
                return jsonify({"success": False, "message": "No active OTP found. Please request a new OTP."}), 400

            otp_id, stored_otp, expires_at = otp_row
            if str(stored_otp).strip() != otp:
                return jsonify({"success": False, "message": "Incorrect OTP. Please verify and try again."}), 400

            # Check expiration
            now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
            is_expired = False
            if isinstance(expires_at, str):
                try:
                    exp_dt = datetime.fromisoformat(expires_at.replace('Z', '').split('+')[0].strip())
                    is_expired = exp_dt < now_utc
                except Exception:
                    is_expired = False
            elif isinstance(expires_at, datetime):
                exp_naive = expires_at.replace(tzinfo=None) if expires_at.tzinfo else expires_at
                is_expired = exp_naive < now_utc

            if is_expired:
                return jsonify({"success": False, "message": "OTP has expired. Please request a new OTP."}), 400

            # Mark OTP as used
            if is_sqlite:
                cursor.execute("UPDATE password_reset_otps SET used = 1 WHERE otp_id = %s", (otp_id,))
            else:
                cursor.execute("UPDATE password_reset_otps SET used = TRUE WHERE otp_id = %s", (otp_id,))

        # Hash and update new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "UPDATE account_tbl SET password_hash = %s WHERE account_id = %s",
            (hashed_password, account_id)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Password reset successfully! You can now login with your new password.",
            "account_id": account_id
        }), 200

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"Reset password error: {e}")
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
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
        data = request.get_json(silent=True) or {}
        account_id = data.get('account_id')
        current_password = (data.get('current_password') or '').strip()
        new_password = (data.get('new_password') or '').strip()

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
        pwd_ok = False
        try:
            pwd_ok = bcrypt.checkpw(current_password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception:
            pwd_ok = (current_password == stored_hash)

        if not pwd_ok:
            return jsonify({"success": False, "message": "Current password is incorrect."}), 401

        # Hash and save the new password
        new_hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            "UPDATE account_tbl SET password_hash = %s WHERE account_id = %s",
            (new_hashed, account_id)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Password changed successfully."}), 200

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
