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
        data = request.json
        account_id = data.get('account_id')
        member_id = data.get('member_id')
        user_input = data.get('user_input')
        bot_response = data.get('bot_response')
        model = data.get('model')

        if not all([account_id, member_id, user_input, bot_response, model]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        # Convert IDs to integers
        account_id = int(account_id)
        member_id = int(member_id)

        # Establish database connection
        conn = connect_db()
        cursor = conn.cursor()

        # Insert chat history into the database
        cursor.execute("""
            INSERT INTO chat_history_tbl (account_id, member_id, user_input, bot_response, model)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING history_id
        """, (account_id, member_id, user_input, bot_response,model))
        
        history_id = cursor.fetchone()[0]
        conn.commit()

        # Close cursor and connection
        cursor.close()
        conn.close()

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
        data = request.json
        account_id = data.get('account_id')
        member_id = data.get('member_id')
        if not account_id or not member_id:
            return jsonify({"success": False, "message": "Account ID and Member ID are required"}), 400

        account_id_str = str(account_id)
        member_id_str = str(member_id)
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT history_id, user_input, bot_response, model, timestamp FROM chat_history_tbl WHERE account_id::text = %s AND member_id::text = %s ORDER BY timestamp DESC", (account_id_str, member_id_str))
        history = cursor.fetchall()

        history_list = [
            {"history_id": h[0], "question": h[1], "response": h[2], "model": h[3], "timestamp": h[4].isoformat()}
            for h in history
        ]

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Chat history retrieved successfully",
            "history": history_list
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


@chat_bp.route('/deletechat', methods=['POST'])
def delete_chat():
    conn = None
    cursor = None
    try:
        data = request.json
        account_id = data.get('account_id')
        member_id = data.get('member_id')
        history_id = data.get('history_id')
        if not account_id or not member_id or not history_id:
            return jsonify({"success": False, "message": "Account ID, Member ID, and History ID are required"}), 400

        account_id_str = str(account_id)
        member_id_str = str(member_id)
        history_id = int(history_id)
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM chat_history_tbl 
            WHERE account_id::text = %s AND member_id::text = %s AND history_id = %s
        """, (account_id_str, member_id_str, history_id))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "No matching history found"}), 404

        cursor.close()
        conn.close()

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