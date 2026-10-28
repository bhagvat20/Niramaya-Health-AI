from flask import Blueprint, request, jsonify
from flask_cors import CORS
import psycopg2

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
        member_id = data.get('member_id')
        user_input = data.get('user_input')
        bot_response = data.get('bot_response')
        model = data.get('model')

        if not all([account_id, user_input, bot_response, model]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        # Convert IDs
        try:
            account_id = int(account_id)
        except (ValueError, TypeError):
            account_id = 1

        # Establish database connection
        conn = connect_db()
        cursor = conn.cursor()

        # Ensure account_id exists in account_tbl to prevent foreign key errors
        cursor.execute("SELECT account_id, family_name FROM account_tbl WHERE account_id = %s", (account_id,))
        acc_row = cursor.fetchone()
        if not acc_row:
            # Fall back to any active account or account 1
            cursor.execute("SELECT account_id, family_name FROM account_tbl ORDER BY account_id ASC LIMIT 1")
            acc_row = cursor.fetchone()
            if acc_row:
                account_id = acc_row[0]
            else:
                cursor.execute("""
                    INSERT INTO account_tbl (family_name, email, password_hash, is_active)
                    VALUES ('Default Family', 'guest@niramaya.com', 'none', 1)
                    RETURNING account_id
                """)
                account_id = cursor.fetchone()[0]
                acc_row = (account_id, 'Default Family')

        acc_family_name = acc_row[1] if (acc_row and len(acc_row) > 1 and acc_row[1]) else "Primary Profile"

        # If member_id is missing, null, or empty string, resolve to an existing member or create a default primary profile
        if not member_id or str(member_id).lower() in ['null', 'undefined', '', 'none', '0']:
            cursor.execute("SELECT member_id FROM member_tbl WHERE account_id = %s ORDER BY member_id ASC LIMIT 1", (account_id,))
            m_row = cursor.fetchone()
            if m_row:
                member_id = m_row[0]
            else:
                cursor.execute("""
                    INSERT INTO member_tbl (account_id, name, gender, age, height, weight)
                    VALUES (%s, %s, 'Other', 25, '170', '65')
                    RETURNING member_id
                """, (account_id, acc_family_name))
                m_new = cursor.fetchone()
                member_id = m_new[0] if m_new else 1
        else:
            try:
                member_id = int(member_id)
                # Verify member belongs to this account or exists
                cursor.execute("SELECT member_id FROM member_tbl WHERE member_id = %s", (member_id,))
                if not cursor.fetchone():
                    cursor.execute("SELECT member_id FROM member_tbl WHERE account_id = %s ORDER BY member_id ASC LIMIT 1", (account_id,))
                    fallback_m = cursor.fetchone()
                    member_id = fallback_m[0] if fallback_m else None
            except Exception:
                member_id = None

            if not member_id:
                cursor.execute("""
                    INSERT INTO member_tbl (account_id, name, gender, age, height, weight)
                    VALUES (%s, %s, 'Other', 25, '170', '65')
                    RETURNING member_id
                """, (account_id, acc_family_name))
                m_new = cursor.fetchone()
                member_id = m_new[0] if m_new else 1

        # Insert chat history into the database
        cursor.execute("""
            INSERT INTO chat_history_tbl (account_id, member_id, user_input, bot_response, model)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING history_id
        """, (account_id, member_id, user_input, bot_response, model))
        
        row = cursor.fetchone()
        history_id = row[0] if (row and len(row) > 0) else 1
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Chat history saved successfully",
            "history_id": history_id
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
        member_id = data.get('member_id')
        if not account_id:
            return jsonify({"success": False, "message": "Account ID is required"}), 400

        conn = connect_db()
        cursor = conn.cursor()

        acc_id = int(account_id)

        if member_id and str(member_id).lower() not in ['all', 'null', 'undefined', '']:
            mem_id = int(member_id)
            cursor.execute("""
                SELECT c.history_id, c.user_input, c.bot_response, c.model, c.timestamp, m.name, c.member_id
                FROM chat_history_tbl c
                LEFT JOIN member_tbl m ON c.member_id = m.member_id
                WHERE c.account_id = %s AND c.member_id = %s
                ORDER BY c.timestamp DESC
            """, (acc_id, mem_id))
        else:
            cursor.execute("""
                SELECT c.history_id, c.user_input, c.bot_response, c.model, c.timestamp, m.name, c.member_id
                FROM chat_history_tbl c
                LEFT JOIN member_tbl m ON c.member_id = m.member_id
                WHERE c.account_id = %s
                ORDER BY c.timestamp DESC
            """, (acc_id,))

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
        history_id = data.get('history_id')
        member_id = data.get('member_id')

        if not account_id or not history_id:
            return jsonify({"success": False, "message": "Account ID and History ID are required"}), 400

        acc_id = int(account_id)
        hist_id = int(history_id)

        conn = connect_db()
        cursor = conn.cursor()

        if member_id and str(member_id).lower() not in ['all', 'null', 'undefined', '']:
            mem_id = int(member_id)
            cursor.execute("""
                DELETE FROM chat_history_tbl 
                WHERE account_id = %s AND member_id = %s AND history_id = %s
            """, (acc_id, mem_id, hist_id))
        else:
            cursor.execute("""
                DELETE FROM chat_history_tbl 
                WHERE account_id = %s AND history_id = %s
            """, (acc_id, hist_id))

        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "No matching history found"}), 404

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