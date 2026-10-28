from flask import Blueprint, request, jsonify
from flask_cors import CORS
import psycopg2
import re
from db_config import get_db_connection
from routes.admin_auth_API import admin_required

# Blueprint for Admin User Management routes
admin_users_bp = Blueprint('admin_users', __name__)
CORS(admin_users_bp)

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

@admin_users_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """
    Retrieve list of registered users with search and filter capabilities.
    Never exposes passwords or password hashes.
    """
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all').strip().lower()
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT 
                a.account_id, 
                a.family_name, 
                a.email, 
                a.is_active, 
                a.created_at,
                COUNT(DISTINCT m.member_id) as member_count,
                COUNT(DISTINCT c.history_id) as chat_count
            FROM account_tbl a
            LEFT JOIN member_tbl m ON a.account_id = m.account_id
            LEFT JOIN chat_history_tbl c ON a.account_id = c.account_id
            WHERE 1=1
        """
        params = []
        
        if search_query:
            sql += " AND (a.email ILIKE %s OR a.family_name ILIKE %s OR CAST(a.account_id AS TEXT) = %s)"
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param, search_query])
            
        if status_filter == 'active':
            sql += " AND a.is_active = %s"
            params.append(True)
        elif status_filter == 'deactivated':
            sql += " AND a.is_active = %s"
            params.append(False)
            
        sql += " GROUP BY a.account_id, a.family_name, a.email, a.is_active, a.created_at ORDER BY a.created_at DESC"
        
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() or []
        
        users_list = []
        for r in rows:
            users_list.append({
                "account_id": r[0],
                "family_name": r[1],
                "email": r[2],
                "is_active": bool(r[3]),
                "created_at": r[4].isoformat() if hasattr(r[4], 'isoformat') else str(r[4]) if r[4] else None,
                "member_count": r[5] or 0,
                "chat_count": r[6] or 0
            })
            
        return jsonify({
            "success": True,
            "count": len(users_list),
            "users": users_list
        }), 200
        
    except Exception as e:
        print(f"Error in get_all_users: {e}")
        return jsonify({"success": False, "message": "Failed to fetch user accounts"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_users_bp.route('/admin/users/<int:account_id>', methods=['GET'])
@admin_required
def get_user_details(account_id):
    """
    Retrieve single user details and associated family members.
    Never exposes passwords or password hashes.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user account info
        cursor.execute("""
            SELECT account_id, family_name, email, is_active, created_at
            FROM account_tbl
            WHERE account_id = %s
        """, (account_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            return jsonify({"success": False, "message": "User account not found"}), 404
            
        user_data = {
            "account_id": user_row[0],
            "family_name": user_row[1],
            "email": user_row[2],
            "is_active": bool(user_row[3]),
            "created_at": user_row[4].isoformat() if hasattr(user_row[4], 'isoformat') else str(user_row[4]) if user_row[4] else None
        }
        
        # Get associated members
        cursor.execute("""
            SELECT member_id, name, gender, age, height, weight, created_at
            FROM member_tbl
            WHERE account_id = %s
            ORDER BY member_id ASC
        """, (account_id,))
        members_rows = cursor.fetchall() or []
        
        members_list = [
            {
                "member_id": m[0],
                "name": m[1],
                "gender": m[2],
                "age": m[3],
                "height": m[4],
                "weight": m[5],
                "created_at": m[6].isoformat() if hasattr(m[6], 'isoformat') else str(m[6]) if m[6] else None
            }
            for m in members_rows
        ]
        
        # Get chat count & recent consultation history
        cursor.execute("SELECT COUNT(*) FROM chat_history_tbl WHERE account_id = %s", (account_id,))
        chat_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT c.history_id, c.user_input, c.bot_response, c.model, c.timestamp, m.name
            FROM chat_history_tbl c
            LEFT JOIN member_tbl m ON c.member_id = m.member_id
            WHERE c.account_id = %s
            ORDER BY c.timestamp DESC
            LIMIT 15;
        """, (account_id,))
        chat_rows = cursor.fetchall() or []
        recent_consultations = [
            {
                "history_id": cr[0],
                "user_input": cr[1],
                "bot_response": cr[2][:120] + ("..." if len(cr[2] or "") > 120 else "") if cr[2] else "",
                "model": cr[3],
                "timestamp": cr[4].isoformat() if hasattr(cr[4], 'isoformat') else str(cr[4]) if cr[4] else None,
                "member_name": cr[5] or "Primary Profile"
            }
            for cr in chat_rows
        ]
        
        user_data["members"] = members_list
        user_data["chat_count"] = chat_count
        user_data["recent_consultations"] = recent_consultations
        
        return jsonify({
            "success": True,
            "user": user_data
        }), 200
        
    except Exception as e:
        print(f"Error in get_user_details: {e}")
        return jsonify({"success": False, "message": "Failed to fetch user details"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_users_bp.route('/admin/users/<int:account_id>', methods=['PUT'])
@admin_users_bp.route('/admin/users/<int:account_id>/update', methods=['POST'])
@admin_required
def update_user(account_id):
    """
    Edit/update user profile information (family_name, email).
    Validates input and checks for email uniqueness.
    """
    conn = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        family_name = (data.get('family_name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        
        if not family_name or not email:
            return jsonify({
                "success": False,
                "message": "Family name and Email are required fields"
            }), 400
            
        if not re.match(EMAIL_REGEX, email):
            return jsonify({
                "success": False,
                "message": "Invalid email address format"
            }), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT account_id FROM account_tbl WHERE account_id = %s", (account_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "User account not found"}), 404
            
        # Check email uniqueness against other users
        cursor.execute("SELECT account_id FROM account_tbl WHERE LOWER(email) = %s AND account_id != %s", (email, account_id))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Email is already in use by another account"}), 400
            
        cursor.execute("""
            UPDATE account_tbl
            SET family_name = %s, email = %s
            WHERE account_id = %s
        """, (family_name, email, account_id))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "User profile updated successfully",
            "user": {
                "account_id": account_id,
                "family_name": family_name,
                "email": email
            }
        }), 200
        
    except Exception as e:
        print(f"Error in update_user: {e}")
        return jsonify({"success": False, "message": "Failed to update user profile"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_users_bp.route('/admin/users/<int:account_id>/status', methods=['PUT', 'POST'])
@admin_required
def toggle_user_status(account_id):
    """
    Activate or deactivate a user account.
    """
    conn = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_active FROM account_tbl WHERE account_id = %s", (account_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({"success": False, "message": "User account not found"}), 404
            
        current_status = row[0]
        
        # If explicitly passed in body use it, otherwise toggle current status
        if 'is_active' in data:
            new_status = bool(data['is_active'])
        else:
            new_status = not current_status
            
        cursor.execute("""
            UPDATE account_tbl
            SET is_active = %s
            WHERE account_id = %s
        """, (new_status, account_id))
        conn.commit()
        
        status_text = "activated" if new_status else "deactivated"
        return jsonify({
            "success": True,
            "message": f"User account successfully {status_text}",
            "account_id": account_id,
            "is_active": new_status
        }), 200
        
    except Exception as e:
        print(f"Error in toggle_user_status: {e}")
        return jsonify({"success": False, "message": "Failed to change user status"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_users_bp.route('/admin/users/<int:account_id>', methods=['DELETE'])
@admin_required
def delete_user(account_id):
    """
    Delete a user account with proper safeguards.
    Requires explicit confirmation payload or query param ('confirm=true').
    Handles foreign key relationships cleanly.
    """
    data = request.get_json(silent=True) or {}
    confirm_flag = data.get('confirm') or request.args.get('confirm') == 'true'
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check user exists
        cursor.execute("SELECT account_id, family_name, email FROM account_tbl WHERE account_id = %s", (account_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            return jsonify({"success": False, "message": "User account not found"}), 404
            
        # Get count of related records to inform admin
        cursor.execute("SELECT COUNT(*) FROM member_tbl WHERE account_id = %s", (account_id,))
        member_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chat_history_tbl WHERE account_id = %s", (account_id,))
        chat_count = cursor.fetchone()[0]
        
        # Safeguard Check: Require explicit confirmation
        if not confirm_flag:
            return jsonify({
                "success": False,
                "requires_confirmation": True,
                "message": "User deletion requires explicit confirmation",
                "user": {
                    "account_id": user_row[0],
                    "family_name": user_row[1],
                    "email": user_row[2]
                },
                "impact_summary": {
                    "members_to_delete": member_count,
                    "chats_to_delete": chat_count
                }
            }), 400
            
        # Perform deletion in database transaction
        cursor.execute("DELETE FROM account_tbl WHERE account_id = %s", (account_id,))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"User '{user_row[2]}' and associated data ({member_count} members, {chat_count} chat entries) deleted successfully",
            "deleted_account_id": account_id
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in delete_user: {e}")
        return jsonify({"success": False, "message": "Failed to delete user account safely"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
