from flask import Blueprint, jsonify, request
from flask_cors import CORS
from db_config import get_db_connection

database_viewer_bp = Blueprint('database_viewer_bp', __name__)
CORS(database_viewer_bp)

@database_viewer_bp.route('/api/database/overview', methods=['GET'])
def get_database_overview():
    """
    Returns full database tables content for visual inspection.
    Safe for presentation, reports, and administrative review.
    Works seamlessly with both SQLite (offline/local) and PostgreSQL (cloud/Render).
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        is_sqlite = conn.__class__.__name__ == 'SQLiteConnWrapper'
        db_engine = "SQLite (Local niramaya.db)" if is_sqlite else "PostgreSQL (projectH)"

        # 1. Accounts
        cur.execute("SELECT account_id, family_name, email, is_active, created_at FROM account_tbl ORDER BY account_id DESC;")
        accounts = []
        for r in cur.fetchall():
            accounts.append({
                "account_id": r[0],
                "family_name": r[1],
                "email": r[2],
                "is_active": bool(r[3]),
                "created_at": str(r[4]) if r[4] else ""
            })

        # 2. Members
        cur.execute("SELECT member_id, account_id, name, gender, age, height, weight, created_at FROM member_tbl ORDER BY member_id DESC;")
        members = []
        for r in cur.fetchall():
            members.append({
                "member_id": r[0],
                "account_id": r[1],
                "name": r[2],
                "gender": r[3],
                "age": r[4],
                "height": r[5] or "N/A",
                "weight": r[6] or "N/A",
                "created_at": str(r[7]) if r[7] else ""
            })

        # 3. Chat Consultations
        cur.execute("SELECT history_id, account_id, member_id, model, user_input, bot_response, timestamp FROM chat_history_tbl ORDER BY history_id DESC;")
        consultations = []
        for r in cur.fetchall():
            consultations.append({
                "history_id": r[0],
                "account_id": r[1],
                "member_id": r[2],
                "model": r[3],
                "user_input": r[4],
                "bot_response": (r[5][:120] + "...") if r[5] and len(r[5]) > 120 else (r[5] or ""),
                "timestamp": str(r[6]) if r[6] else ""
            })

        # 4. Health Content
        cur.execute("SELECT content_id, content_type, title, category, status, created_at FROM health_content_tbl ORDER BY content_id DESC LIMIT 50;")
        health_content = []
        for r in cur.fetchall():
            health_content.append({
                "content_id": r[0],
                "content_type": r[1],
                "title": r[2],
                "category": r[3] or "General",
                "status": r[4] or "published",
                "created_at": str(r[5]) if r[5] else ""
            })

        # 5. Admin
        cur.execute("SELECT admin_id, username, email, role, is_active, created_at FROM admin_tbl ORDER BY admin_id ASC;")
        admins = []
        for r in cur.fetchall():
            admins.append({
                "admin_id": r[0],
                "username": r[1],
                "email": r[2],
                "role": r[3],
                "is_active": bool(r[4]),
                "created_at": str(r[5]) if r[5] else ""
            })

        return jsonify({
            "success": True,
            "engine": db_engine,
            "counts": {
                "accounts": len(accounts),
                "members": len(members),
                "consultations": len(consultations),
                "health_content": len(health_content),
                "admins": len(admins)
            },
            "tables": {
                "accounts": accounts,
                "members": members,
                "consultations": consultations,
                "health_content": health_content,
                "admins": admins
            }
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
