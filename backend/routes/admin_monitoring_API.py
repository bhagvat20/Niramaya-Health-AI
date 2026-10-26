from flask import Blueprint, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime
from db_config import get_db_connection
from routes.admin_auth_API import admin_required

admin_monitoring_bp = Blueprint('admin_monitoring', __name__)
CORS(admin_monitoring_bp)

@admin_monitoring_bp.route('/admin/monitoring/stats', methods=['GET'])
@admin_required
def get_system_stats():
    """
    Retrieve real aggregated statistics from database tables.
    Never hardcodes metrics.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total registered users
        cursor.execute("SELECT COUNT(*), COUNT(CASE WHEN is_active = TRUE THEN 1 END), COUNT(CASE WHEN is_active = FALSE THEN 1 END) FROM account_tbl;")
        u_row = cursor.fetchone()
        total_users = u_row[0]
        active_users = u_row[1]
        deactivated_users = u_row[2]

        # Total family members
        cursor.execute("SELECT COUNT(*) FROM member_tbl;")
        total_members = cursor.fetchone()[0]

        # Total AI chats / disease prediction interactions
        cursor.execute("SELECT COUNT(*) FROM chat_history_tbl;")
        total_ai_chats = cursor.fetchone()[0]

        # Total Health Content items
        cursor.execute("SELECT COUNT(*), COUNT(CASE WHEN status = 'published' THEN 1 END) FROM health_content_tbl;")
        c_row = cursor.fetchone()
        total_health_content = c_row[0]
        published_health_content = c_row[1]

        # Active admin sessions
        cursor.execute("SELECT COUNT(*) FROM admin_tokens_tbl WHERE expires_at > CURRENT_TIMESTAMP;")
        active_admin_sessions = cursor.fetchone()[0]

        return jsonify({
            "success": True,
            "stats": {
                "total_users": total_users,
                "active_users": active_users,
                "deactivated_users": deactivated_users,
                "total_members": total_members,
                "total_ai_chats": total_ai_chats,
                "total_disease_predictions": total_ai_chats,
                "total_health_content": total_health_content,
                "published_health_content": published_health_content,
                "active_admin_sessions": active_admin_sessions
            }
        }), 200

    except Exception as e:
        print(f"Error in get_system_stats: {e}")
        return jsonify({"success": False, "message": "Failed to calculate system statistics"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_monitoring_bp.route('/admin/monitoring/activity', methods=['GET'])
@admin_required
def get_recent_activity():
    """
    Retrieve real recent activity logs (registrations, AI queries, content updates).
    Never exposes passwords, hashes, or credentials.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Recent registrations (last 5)
        cursor.execute("""
            SELECT account_id, family_name, email, is_active, created_at
            FROM account_tbl
            ORDER BY created_at DESC
            LIMIT 5;
        """)
        reg_rows = cursor.fetchall()
        recent_registrations = [
            {
                "account_id": r[0],
                "family_name": r[1],
                "email": r[2],
                "is_active": r[3],
                "created_at": r[4].isoformat() if hasattr(r[4], 'isoformat') else str(r[4]) if r[4] else None
            }
            for r in reg_rows
        ]

        # Recent AI queries (last 5)
        cursor.execute("""
            SELECT c.history_id, a.email, m.name, c.model, c.timestamp, c.user_input
            FROM chat_history_tbl c
            JOIN account_tbl a ON c.account_id = a.account_id
            JOIN member_tbl m ON c.member_id = m.member_id
            ORDER BY c.timestamp DESC
            LIMIT 5;
        """)
        chat_rows = cursor.fetchall()
        recent_chats = []
        for r in chat_rows:
            raw_text = r[5] or ""
            snippet = raw_text[:80] + ("..." if len(raw_text) > 80 else "")
            ts = r[4].isoformat() if hasattr(r[4], 'isoformat') else str(r[4]) if r[4] else None
            recent_chats.append({
                "history_id": r[0],
                "user_email": r[1],
                "member_name": r[2],
                "model": r[3],
                "timestamp": ts,
                "query_snippet": snippet
            })

        # Recent content updates (last 5)
        cursor.execute("""
            SELECT content_id, content_type, title, category, status, updated_at
            FROM health_content_tbl
            ORDER BY updated_at DESC
            LIMIT 5;
        """)
        content_rows = cursor.fetchall()
        recent_content_updates = [
            {
                "content_id": r[0],
                "content_type": r[1],
                "title": r[2],
                "category": r[3],
                "status": r[4],
                "updated_at": r[5].isoformat() if hasattr(r[5], 'isoformat') else str(r[5]) if r[5] else None
            }
            for r in content_rows
        ]

        return jsonify({
            "success": True,
            "activity": {
                "recent_registrations": recent_registrations,
                "recent_chats": recent_chats,
                "recent_content_updates": recent_content_updates
            }
        }), 200

    except Exception as e:
        print(f"Error in get_recent_activity: {e}")
        return jsonify({"success": False, "message": "Failed to fetch activity logs"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_monitoring_bp.route('/admin/monitoring/system-status', methods=['GET'])
@admin_required
def get_system_status():
    """
    Retrieve real database connection status and table health counts.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        tables = ['account_tbl', 'member_tbl', 'chat_history_tbl', 'health_content_tbl', 'admin_tbl', 'admin_tokens_tbl']
        table_counts = {}

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            table_counts[table] = cursor.fetchone()[0]

        has_gemini_key = bool(os.getenv('GEMINI_API_KEY'))

        return jsonify({
            "success": True,
            "system_status": {
                "database_connected": True,
                "database_name": "projectH",
                "server_time": datetime.utcnow().isoformat() + "Z",
                "table_counts": table_counts,
                "ai_engine_configured": True,
                "gemini_api_key_present": has_gemini_key
            }
        }), 200

    except Exception as e:
        print(f"Error in get_system_status: {e}")
        return jsonify({
            "success": False,
            "system_status": {
                "database_connected": False,
                "error": str(e)
            }
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_monitoring_bp.route('/admin/monitoring/overview', methods=['GET'])
@admin_required
def get_monitoring_overview():
    """
    Combined endpoint returning stats, activity stream, and system status in a single request.
    """
    try:
        # Call helper functions internally
        stats_resp, status_code1 = get_system_stats()
        activity_resp, status_code2 = get_recent_activity()
        system_resp, status_code3 = get_system_status()

        if status_code1 == 200 and status_code2 == 200 and status_code3 == 200:
            return jsonify({
                "success": True,
                "stats": stats_resp.get_json()["stats"],
                "activity": activity_resp.get_json()["activity"],
                "system_status": system_resp.get_json()["system_status"]
            }), 200
        else:
            return jsonify({"success": False, "message": "Failed to load monitoring overview"}), 500
    except Exception as e:
        print(f"Error in get_monitoring_overview: {e}")
        return jsonify({"success": False, "message": "Server error generating monitoring overview"}), 500
