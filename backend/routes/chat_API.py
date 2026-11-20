from flask import Blueprint, request, jsonify
from flask_cors import CORS
import psycopg2
from datetime import datetime

from db_config import get_db_connection

# Create a Blueprint for chat-related routes
chat_bp = Blueprint('chat', __name__)
CORS(chat_bp)

def connect_db():
    return get_db_connection()


@chat_bp.route('/savechat', methods=['POST'])
def save_chat():
    conn = None
    cursor = None
    try:
        # Get data from the request body
        data = request.json or {}
        account_id = data.get('account_id')
        email = (data.get('email') or '').strip().lower()
        member_id = data.get('member_id')
        user_input = data.get('user_input')
        bot_response = data.get('bot_response')
        model = data.get('model')

        if not all([user_input, bot_response, model]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        if not account_id and not email:
            return jsonify({"success": False, "message": "Valid logged-in account_id or email is required"}), 401

        # Establish database connection
        conn = connect_db()
        cursor = conn.cursor()

        acc_row = None
        # 1. Resolve strictly by user email first if available (universal across Local PostgreSQL & Render Cloud SQLite)
        if email:
            cursor.execute("SELECT account_id, family_name FROM account_tbl WHERE LOWER(email) = %s LIMIT 1", (email,))
            acc_row = cursor.fetchone()

        # 2. Fall back to account_id if email was not supplied or not yet found
        if not acc_row and account_id:
            try:
                acc_int = int(account_id)
                cursor.execute("SELECT account_id, family_name FROM account_tbl WHERE account_id = %s LIMIT 1", (acc_int,))
                acc_row = cursor.fetchone()
            except (ValueError, TypeError):
                pass

        # 3. If still not found and email was provided, run quick sync in case user registered on another node
        if not acc_row and email:
            try:
                from sync_worker import sync_now
                sync_now(timeout_sec=2.5)
                cursor.execute("SELECT account_id, family_name FROM account_tbl WHERE LOWER(email) = %s LIMIT 1", (email,))
                acc_row = cursor.fetchone()
            except Exception:
                pass

        if not acc_row:
            return jsonify({"success": False, "message": "Account not found. Please login to save history."}), 404

        resolved_account_id = acc_row[0]
        acc_family_name = acc_row[1] if (len(acc_row) > 1 and acc_row[1]) else "Primary Profile"

        # Resolve member_id: check if requested member belongs to this account
        resolved_member_id = None
        if member_id and str(member_id).lower() not in ['null', 'undefined', '', 'none', '0']:
            try:
                mem_candidate = int(member_id)
                cursor.execute("SELECT member_id FROM member_tbl WHERE member_id = %s AND account_id = %s", (mem_candidate, resolved_account_id))
                m_found = cursor.fetchone()
                if m_found:
                    resolved_member_id = m_found[0]
            except Exception:
                pass

        if not resolved_member_id:
            # Fall back to the first registered family member for this account
            cursor.execute("SELECT member_id FROM member_tbl WHERE account_id = %s ORDER BY member_id ASC LIMIT 1", (resolved_account_id,))
            m_row = cursor.fetchone()
            if m_row:
                resolved_member_id = m_row[0]
            else:
                # Create a default member profile if none exists
                cursor.execute("""
                    INSERT INTO member_tbl (account_id, name, gender, age, height, weight)
                    VALUES (%s, %s, 'Other', 25, '170', '65')
                    RETURNING member_id
                """, (resolved_account_id, acc_family_name))
                m_new = cursor.fetchone()
                resolved_member_id = m_new[0] if m_new else 1

        # Insert consultation history into database
        cursor.execute("""
            INSERT INTO chat_history_tbl (account_id, member_id, user_input, bot_response, model)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING history_id
        """, (resolved_account_id, resolved_member_id, user_input, bot_response, model))

        row = cursor.fetchone()
        history_id = row[0] if (row and len(row) > 0) else 1
        conn.commit()

        # Trigger instant bidirectional sync to Cloud / Local
        try:
            from sync_worker import trigger_instant_sync
            trigger_instant_sync()
        except Exception:
            pass

        return jsonify({
            "success": True,
            "message": "Chat history saved successfully",
            "history_id": history_id,
            "account_id": resolved_account_id
        }), 200

    except psycopg2.Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    except ValueError as e:
        return jsonify({"success": False, "message": "Invalid ID format"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@chat_bp.route('/getchat', methods=['POST'])
def get_chat():
    conn = None
    cursor = None
    try:
        data = request.json or {}
        account_id = data.get('account_id')
        email = (data.get('email') or '').strip().lower()
        member_id = data.get('member_id')

        if not account_id and not email:
            return jsonify({"success": False, "message": "Account ID or Email is required"}), 400

        # Trigger fast sync so chats performed on Cloud/Local are immediately visible
        try:
            from sync_worker import sync_now
            sync_now(timeout_sec=2.0)
        except Exception:
            pass

        conn = connect_db()
        cursor = conn.cursor()

        acc_id = None
        # 1. Resolve by email first
        if email:
            cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s LIMIT 1", (email,))
            r = cursor.fetchone()
            if r:
                acc_id = r[0]

        # 2. Resolve by numeric account_id if not found by email
        if not acc_id and account_id:
            try:
                cand_id = int(account_id)
                cursor.execute("SELECT account_id FROM account_tbl WHERE account_id = %s LIMIT 1", (cand_id,))
                r = cursor.fetchone()
                if r:
                    acc_id = r[0]
                else:
                    acc_id = cand_id
            except (ValueError, TypeError):
                pass

        if not acc_id and not email:
            return jsonify({
                "success": True,
                "message": "No chat history found for this account",
                "history": []
            }), 200

        # Query all consultations belonging to this account or user email
        if member_id and str(member_id).lower() not in ['all', 'null', 'undefined', '', 'none', '0']:
            try:
                mem_id = int(member_id)
                cursor.execute("""
                    SELECT c.history_id, c.user_input, c.bot_response, c.model, c.timestamp, m.name, c.member_id
                    FROM chat_history_tbl c
                    LEFT JOIN member_tbl m ON c.member_id = m.member_id
                    LEFT JOIN account_tbl a ON c.account_id = a.account_id
                    WHERE (c.account_id = %s OR (LOWER(a.email) = %s AND %s != '')) AND c.member_id = %s
                    ORDER BY c.timestamp DESC
                """, (acc_id, email, email, mem_id))
            except Exception:
                cursor.execute("""
                    SELECT c.history_id, c.user_input, c.bot_response, c.model, c.timestamp, m.name, c.member_id
                    FROM chat_history_tbl c
                    LEFT JOIN member_tbl m ON c.member_id = m.member_id
                    LEFT JOIN account_tbl a ON c.account_id = a.account_id
                    WHERE (c.account_id = %s OR (LOWER(a.email) = %s AND %s != ''))
                    ORDER BY c.timestamp DESC
                """, (acc_id, email, email))
        else:
            cursor.execute("""
                SELECT c.history_id, c.user_input, c.bot_response, c.model, c.timestamp, m.name, c.member_id
                FROM chat_history_tbl c
                LEFT JOIN member_tbl m ON c.member_id = m.member_id
                LEFT JOIN account_tbl a ON c.account_id = a.account_id
                WHERE (c.account_id = %s OR (LOWER(a.email) = %s AND %s != ''))
                ORDER BY c.timestamp DESC
            """, (acc_id, email, email))

        history = cursor.fetchall() or []

        history_list = []
        for h in history:
            ts = h[4]
            ts_str = ts.isoformat() if hasattr(ts, 'isoformat') else (str(ts) if ts else '')
            history_list.append({
                "history_id": h[0],
                "question": h[1],
                "response": h[2],
                "model": h[3],
                "timestamp": ts_str,
                "member_name": h[5] or "Family Member",
                "member_id": h[6]
            })

        return jsonify({
            "success": True,
            "message": "Chat history retrieved successfully",
            "history": history_list
        }), 200

    except psycopg2.Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    except ValueError as e:
        return jsonify({"success": False, "message": "Invalid ID format"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@chat_bp.route('/deletechat', methods=['POST'])
def delete_chat():
    conn = None
    cursor = None
    try:
        data = request.json or {}
        account_id = data.get('account_id')
        email = (data.get('email') or '').strip().lower()
        history_id = data.get('history_id')
        member_id = data.get('member_id')

        if (not account_id and not email) or not history_id:
            return jsonify({"success": False, "message": "Account ID/Email and History ID are required"}), 400

        try:
            hist_id = int(history_id)
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid history_id"}), 400

        conn = connect_db()
        cursor = conn.cursor()

        acc_id = None
        if email:
            cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s LIMIT 1", (email,))
            r = cursor.fetchone()
            if r:
                acc_id = r[0]

        if not acc_id and account_id:
            try:
                acc_id = int(account_id)
            except Exception:
                pass

        if not acc_id:
            return jsonify({"success": False, "message": "Account not found"}), 404

        if member_id and str(member_id).lower() not in ['all', 'null', 'undefined', '', 'none', '0']:
            try:
                mem_id = int(member_id)
                cursor.execute("""
                    DELETE FROM chat_history_tbl 
                    WHERE account_id = %s AND member_id = %s AND history_id = %s
                """, (acc_id, mem_id, hist_id))
            except Exception:
                cursor.execute("""
                    DELETE FROM chat_history_tbl 
                    WHERE account_id = %s AND history_id = %s
                """, (acc_id, hist_id))
        else:
            cursor.execute("""
                DELETE FROM chat_history_tbl 
                WHERE account_id = %s AND history_id = %s
            """, (acc_id, hist_id))

        conn.commit()

        # Trigger instant sync so deletion is mirrored
        try:
            from sync_worker import trigger_instant_sync
            trigger_instant_sync()
        except Exception:
            pass

        return jsonify({
            "success": True,
            "message": "Chat history deleted successfully"
        }), 200

    except psycopg2.Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
