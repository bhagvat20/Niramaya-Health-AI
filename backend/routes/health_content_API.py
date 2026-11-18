from flask import Blueprint, request, jsonify
from flask_cors import CORS
import psycopg2
from db_config import get_db_connection
from routes.admin_auth_API import admin_required

health_content_bp = Blueprint('health_content', __name__)
CORS(health_content_bp)

MEDICAL_DISCLAIMER = "Niramaya health information is provided for educational and informational purposes only and does not constitute professional medical advice, diagnosis, or treatment."

def format_dt(dt):
    if not dt:
        return None
    return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)

# ==========================================
# PUBLIC READ-ONLY ENDPOINTS (NORMAL USERS)
# ==========================================

@health_content_bp.route('/api/health-content/tips', methods=['GET'])
def get_public_wellness_tips():
    """
    Public endpoint: Fetch published wellness tips.
    Supports optional 'category' filter.
    """
    category = request.args.get('category', '').strip()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT content_id, title, category, content, author_or_source, created_at, updated_at
            FROM health_content_tbl
            WHERE content_type = 'wellness_tip' AND status = 'published'
        """
        params = []
        if category:
            sql += " AND category ILIKE %s"
            params.append(category)
            
        sql += " ORDER BY content_id ASC"
        
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() or []
        
        tips = [
            {
                "content_id": r[0],
                "title": r[1],
                "category": r[2],
                "content": r[3],
                "author_or_source": r[4],
                "created_at": format_dt(r[5]),
                "updated_at": format_dt(r[6])
            }
            for r in rows
        ]
        
        return jsonify({
            "success": True,
            "count": len(tips),
            "disclaimer": MEDICAL_DISCLAIMER,
            "tips": tips
        }), 200
        
    except Exception as e:
        print(f"Error in get_public_wellness_tips: {e}")
        return jsonify({"success": False, "message": "Failed to fetch wellness tips"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@health_content_bp.route('/api/health-content/articles', methods=['GET'])
def get_public_articles():
    """
    Public endpoint: Fetch published health articles and research items.
    Supports optional 'category' filter.
    """
    category = request.args.get('category', '').strip()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT content_id, title, category, content, author_or_source, external_link, image_url, created_at, updated_at
            FROM health_content_tbl
            WHERE content_type = 'article' AND status = 'published'
        """
        params = []
        if category:
            sql += " AND category ILIKE %s"
            params.append(category)
            
        sql += " ORDER BY created_at DESC"
        
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        
        articles = [
            {
                "content_id": r[0],
                "title": r[1],
                "category": r[2],
                "content": r[3],
                "author_or_source": r[4],
                "external_link": r[5],
                "image_url": r[6],
                "created_at": format_dt(r[7]),
                "updated_at": format_dt(r[8])
            }
            for r in rows
        ]
        
        return jsonify({
            "success": True,
            "count": len(articles),
            "disclaimer": MEDICAL_DISCLAIMER,
            "articles": articles
        }), 200
        
    except Exception as e:
        print(f"Error in get_public_articles: {e}")
        return jsonify({"success": False, "message": "Failed to fetch health articles"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@health_content_bp.route('/api/health-content/<int:content_id>', methods=['GET'])
def get_single_content(content_id):
    """
    Public endpoint: Retrieve single published content item.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT content_id, content_type, title, category, content, author_or_source, external_link, image_url, status, created_at, updated_at
            FROM health_content_tbl
            WHERE content_id = %s AND status = 'published'
        """, (content_id,))
        r = cursor.fetchone()
        
        if not r:
            return jsonify({"success": False, "message": "Content item not found or not published"}), 404
            
        content_item = {
            "content_id": r[0],
            "content_type": r[1],
            "title": r[2],
            "category": r[3],
            "content": r[4],
            "author_or_source": r[5],
            "external_link": r[6],
            "image_url": r[7],
            "status": r[8],
            "created_at": format_dt(r[9]),
            "updated_at": format_dt(r[10])
        }
        
        return jsonify({
            "success": True,
            "disclaimer": MEDICAL_DISCLAIMER,
            "content": content_item
        }), 200
        
    except Exception as e:
        print(f"Error in get_single_content: {e}")
        return jsonify({"success": False, "message": "Failed to fetch content"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==========================================
# ADMIN MANAGEMENT ENDPOINTS (PROTECTED)
# ==========================================

@health_content_bp.route('/admin/health-content', methods=['GET'])
@admin_required
def admin_get_all_content():
    """
    Admin endpoint: Retrieve all health content (tips & articles) regardless of status.
    Supports filtering by type ('wellness_tip'/'article'/'all'), status ('published'/'archived'/'draft'/'all'), and search query.
    """
    content_type = request.args.get('type', 'all').strip().lower()
    status_filter = request.args.get('status', 'all').strip().lower()
    search_query = request.args.get('search', '').strip()
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT content_id, content_type, title, category, content, author_or_source, external_link, image_url, status, created_at, updated_at
            FROM health_content_tbl
            WHERE 1=1
        """
        params = []
        
        if content_type in ['wellness_tip', 'article']:
            sql += " AND content_type = %s"
            params.append(content_type)
            
        if status_filter in ['published', 'archived', 'draft']:
            sql += " AND status = %s"
            params.append(status_filter)
            
        if search_query:
            sql += " AND (title ILIKE %s OR content ILIKE %s OR category ILIKE %s)"
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param, search_param])
            
        sql += " ORDER BY updated_at DESC, content_id DESC"
        
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        
        items = [
            {
                "content_id": r[0],
                "content_type": r[1],
                "title": r[2],
                "category": r[3],
                "content": r[4],
                "author_or_source": r[5],
                "external_link": r[6],
                "image_url": r[7],
                "status": r[8],
                "created_at": format_dt(r[9]),
                "updated_at": format_dt(r[10])
            }
            for r in rows
        ]
        
        return jsonify({
            "success": True,
            "count": len(items),
            "disclaimer": MEDICAL_DISCLAIMER,
            "items": items
        }), 200
        
    except Exception as e:
        print(f"Error in admin_get_all_content: {e}")
        return jsonify({"success": False, "message": "Failed to fetch health content"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@health_content_bp.route('/admin/health-content', methods=['POST'])
@admin_required
def admin_create_content():
    """
    Admin endpoint: Create new health content item (Wellness Tip or Health Article).
    Validates input before saving.
    """
    data = request.get_json(silent=True) or {}
    
    content_type = (data.get('content_type') or '').strip().lower()
    title = (data.get('title') or '').strip()
    category = (data.get('category') or '').strip()
    content = (data.get('content') or '').strip()
    author_or_source = (data.get('author_or_source') or 'Niramaya Health Editorial').strip()
    external_link = (data.get('external_link') or '').strip()
    image_url = (data.get('image_url') or '').strip()
    status = (data.get('status') or 'published').strip().lower()
    
    if content_type not in ['wellness_tip', 'article']:
        return jsonify({"success": False, "message": "Content type must be 'wellness_tip' or 'article'"}), 400
        
    if not title or not content:
        return jsonify({"success": False, "message": "Title and Content body are required fields"}), 400
        
    if status not in ['published', 'archived', 'draft']:
        status = 'published'
        
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO health_content_tbl (content_type, title, category, content, author_or_source, external_link, image_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING content_id, created_at, updated_at
        """, (content_type, title, category, content, author_or_source, external_link, image_url, status))
        
        new_id, created_at, updated_at = cursor.fetchone()
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Health content created successfully",
            "disclaimer": MEDICAL_DISCLAIMER,
            "item": {
                "content_id": new_id,
                "content_type": content_type,
                "title": title,
                "category": category,
                "content": content,
                "author_or_source": author_or_source,
                "external_link": external_link,
                "image_url": image_url,
                "status": status,
                "created_at": format_dt(created_at),
                "updated_at": format_dt(updated_at)
            }
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in admin_create_content: {e}")
        return jsonify({"success": False, "message": "Failed to save health content"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@health_content_bp.route('/admin/health-content/<int:content_id>', methods=['PUT'])
@health_content_bp.route('/admin/health-content/<int:content_id>/update', methods=['POST'])
@admin_required
def admin_update_content(content_id):
    """
    Admin endpoint: Update existing health content item.
    """
    data = request.get_json(silent=True) or {}
    
    title = (data.get('title') or '').strip()
    category = (data.get('category') or '').strip()
    content = (data.get('content') or '').strip()
    author_or_source = (data.get('author_or_source') or '').strip()
    external_link = (data.get('external_link') or '').strip()
    image_url = (data.get('image_url') or '').strip()
    status = (data.get('status') or '').strip().lower()
    content_type = (data.get('content_type') or '').strip().lower()
    
    if not title or not content:
        return jsonify({"success": False, "message": "Title and Content body cannot be empty"}), 400
        
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify content exists
        cursor.execute("SELECT content_id FROM health_content_tbl WHERE content_id = %s", (content_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Health content item not found"}), 404
            
        cursor.execute("""
            UPDATE health_content_tbl
            SET title = %s,
                category = %s,
                content = %s,
                author_or_source = %s,
                external_link = %s,
                image_url = %s,
                status = COALESCE(NULLIF(%s, ''), status),
                content_type = COALESCE(NULLIF(%s, ''), content_type),
                updated_at = CURRENT_TIMESTAMP
            WHERE content_id = %s
        """, (title, category, content, author_or_source, external_link, image_url, status, content_type, content_id))
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Health content item updated successfully",
            "disclaimer": MEDICAL_DISCLAIMER,
            "content_id": content_id
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in admin_update_content: {e}")
        return jsonify({"success": False, "message": "Failed to update health content"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@health_content_bp.route('/admin/health-content/<int:content_id>/status', methods=['PUT', 'POST'])
@admin_required
def admin_toggle_status(content_id):
    """
    Admin endpoint: Change status of content item (e.g. 'published', 'archived', 'draft').
    """
    data = request.get_json(silent=True) or {}
    new_status = (data.get('status') or '').strip().lower()
    
    if new_status not in ['published', 'archived', 'draft']:
        return jsonify({"success": False, "message": "Status must be 'published', 'archived', or 'draft'"}), 400
        
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE health_content_tbl
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE content_id = %s
        """, (new_status, content_id))
        
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Content item not found"}), 404
            
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": f"Content status updated to '{new_status}'",
            "content_id": content_id,
            "status": new_status
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in admin_toggle_status: {e}")
        return jsonify({"success": False, "message": "Failed to change content status"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@health_content_bp.route('/admin/health-content/<int:content_id>', methods=['DELETE'])
@admin_required
def admin_delete_content(content_id):
    """
    Admin endpoint: Delete or archive outdated health content item.
    Supports query parameter 'archive=true' for archiving instead of permanent deletion.
    """
    data = request.get_json(silent=True) or {}
    should_archive = request.args.get('archive') == 'true' or data.get('archive') is True
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT content_id, title FROM health_content_tbl WHERE content_id = %s", (content_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"success": False, "message": "Content item not found"}), 404
            
        if should_archive:
            cursor.execute("UPDATE health_content_tbl SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE content_id = %s", (content_id,))
            message = f"Content item '{row[1]}' archived successfully"
        else:
            cursor.execute("DELETE FROM health_content_tbl WHERE content_id = %s", (content_id,))
            message = f"Content item '{row[1]}' deleted permanently"
            
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": message,
            "content_id": content_id
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in admin_delete_content: {e}")
        return jsonify({"success": False, "message": "Failed to remove content item"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==========================================
# LIVE RESEARCH PAPERS PROXY (EuropePMC + Verified Fallback)
# ==========================================

_RESEARCH_CACHE = {"timestamp": 0, "papers": []}

CURATED_FALLBACK_PAPERS = [
    {
        "title": "BioGPT: Generative Pre-trained Transformer for Biomedical Text Generation and Mining",
        "authors": "Luo R, Sun L, Xia Y, Qin T, Zhang S, Poon H, Liu TY",
        "journal": "Briefings in Bioinformatics",
        "year": "2022",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36156661/",
        "image": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=600&q=80",
        "tag": "Biomedical AI • 2022"
    },
    {
        "title": "Large Language Models Encode Clinical Knowledge",
        "authors": "Singhal K, Azizi S, Tu T, Mahdavi SS, Wei J, Chung HW, et al.",
        "journal": "Nature",
        "year": "2023",
        "url": "https://pubmed.ncbi.nlm.nih.gov/37438534/",
        "image": "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=600&q=80",
        "tag": "Nature • 2023"
    },
    {
        "title": "Evaluation of Symptom Checkers for Self Diagnosis and Triage: Audit Study",
        "authors": "Semigran HL, Linder JA, Gidengil C, Mehrotra A",
        "journal": "BMJ",
        "year": "2015",
        "url": "https://pubmed.ncbi.nlm.nih.gov/26157077/",
        "image": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=600&q=80",
        "tag": "BMJ • 2015"
    },
    {
        "title": "High-Performance Medicine: The Convergence of Human and Artificial Intelligence",
        "authors": "Topol EJ",
        "journal": "Nature Medicine",
        "year": "2019",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30617339/",
        "image": "https://images.unsplash.com/photo-1550831107-1553da8c8464?auto=format&fit=crop&w=600&q=80",
        "tag": "Nature Medicine • 2019"
    },
    {
        "title": "A Guide to Deep Learning in Healthcare",
        "authors": "Esteva A, Robicquet A, Ramsundar B, Kuleshov V, DePristo M, et al.",
        "journal": "Nature Medicine",
        "year": "2019",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30617335/",
        "image": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=600&q=80",
        "tag": "Healthcare ML • 2019"
    },
    {
        "title": "Artificial Intelligence in Clinical Decision Support: Challenges and Opportunities",
        "authors": "Sutton RT, Pincock D, Baumgart DC, Sadowski DC, Fedorak RN, Kroeker KI",
        "journal": "NPJ Digital Medicine",
        "year": "2020",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32047862/",
        "image": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=600&q=80",
        "tag": "NPJ Digital Medicine • 2020"
    }
]


@health_content_bp.route('/api/research-papers', methods=['GET'])
def get_live_research_papers():
    """
    Returns 6 latest peer-reviewed Health AI / Clinical research papers from EuropePMC
    (cached 15 minutes) with verified clickable PubMed/EuropePMC fallbacks.
    """
    import time
    import re
    import html
    import json
    import urllib.request

    now = time.time()
    if _RESEARCH_CACHE["papers"] and (now - _RESEARCH_CACHE["timestamp"] < 900):
        return jsonify({"success": True, "source": "cache", "papers": _RESEARCH_CACHE["papers"]}), 200

    image_pool = [
        "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1532938911079-1b06ac7ceec7?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1579684385127-1ef15d508118?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1550831107-1553da8c8464?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=600&q=80",
    ]

    try:
        epmc_url = (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            "?query=(%22artificial+intelligence%22+AND+(healthcare+OR+clinical+OR+diagnosis))"
            "&resultType=lite&format=json&pageSize=12&sort=P_PDATE_D+desc"
        )
        req = urllib.request.Request(epmc_url, headers={"User-Agent": "NiramayaHealthAI/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        raw_results = payload.get("resultList", {}).get("result", [])

        papers = []
        for item in raw_results:
            title = html.unescape(re.sub(r"<[^>]+>", "", item.get("title") or "")).strip().rstrip(".")
            if not title:
                continue
            pmcid = item.get("pmcid")
            source = item.get("source") or "MED"
            pid = item.get("id") or ""
            if pmcid:
                article_url = f"https://europepmc.org/article/PMC/{pmcid}"
            elif pid:
                article_url = f"https://europepmc.org/article/{source}/{pid}"
            else:
                continue

            papers.append({
                "title": title,
                "authors": item.get("authorString") or "Clinical Research Group",
                "journal": item.get("journalTitle") or "Europe PMC",
                "year": str(item.get("pubYear") or "Latest"),
                "url": article_url,
                "image": image_pool[len(papers) % len(image_pool)],
                "tag": f"{item.get('journalTitle') or 'Research'} • {item.get('pubYear') or 'Latest'}"
            })
            if len(papers) >= 6:
                break

        if papers:
            _RESEARCH_CACHE["timestamp"] = now
            _RESEARCH_CACHE["papers"] = papers
            return jsonify({"success": True, "source": "europepmc", "papers": papers}), 200
    except Exception as e:
        print(f"Live EuropePMC fetch note: {e}")

    return jsonify({"success": True, "source": "curated", "papers": CURATED_FALLBACK_PAPERS}), 200

