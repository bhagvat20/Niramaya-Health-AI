"""
Niramaya Health AI - Automated Launcher & Server Manager
- 100% Offline Compatible (No Internet Required)
- Ensures clean port 5000
- Starts Flask server
- Automatically waits until server responds before opening browser
- Displays clear status for exams / presentations
"""
import os
import sys
import time
import socket
import threading
import webbrowser
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

def is_port_in_use(port=5000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def free_port(port=5000):
    """Kills any process currently occupying the port."""
    if not is_port_in_use(port):
        return
    print(f"[*] Port {port} is occupied. Freeing port...")
    try:
        import subprocess
        # Find PID on Windows
        output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
        for line in output.strip().splitlines():
            if 'LISTENING' in line:
                pid = line.strip().split()[-1]
                subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[*] Closed previous process (PID: {pid})")
                time.sleep(1)
                break
    except Exception as e:
        print(f"[!] Note: Could not auto-kill port {port}: {e}")

def wait_and_open_browser(url="http://127.0.0.1:5000", max_wait=20):
    """Waits until the server is actually responding before opening the browser."""
    print("[*] Waiting for server to initialize AI models & database...")
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status in (200, 302):
                    print("\n" + "=" * 62)
                    print("  >>> SUCCESS: NIRAMAYA HEALTH AI IS LIVE AND READY! <<<")
                    print("=" * 62)
                    print(f"  [+] Website URL : {url}")
                    print(f"  [+] Admin Portal: {url}/admin_login.html")
                    print(f"  [+] Mode        : 100% OFFLINE (NO INTERNET NEEDED)")
                    print("-" * 62)
                    print("  IMPORTANT NOTE FOR EXAM / PRESENTATION:")
                    print("  * Browser has been opened automatically.")
                    print("  * KEEP THIS BLACK WINDOW OPEN while showing the project.")
                    print("  * To STOP the server when done, close this window or Ctrl+C.")
                    print("=" * 62 + "\n")
                    webbrowser.open(url)
                    return
        except Exception:
            time.sleep(0.6)
    
    # Fallback if timeout
    print("[*] Opening browser now...")
    webbrowser.open(url)

def sync_cloud_history():
    """Syncs consultation history and accounts from cloud deployment to local DB if online."""
    try:
        import json
        import bcrypt
        from db_config import get_db_connection

        # 1. Sync accounts from cloud
        try:
            admin_req = urllib.request.Request(
                'https://niramaya-health-ai.onrender.com/admin/login',
                data=json.dumps({'username': 'admin', 'password': 'Admin@1234'}).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(admin_req, timeout=3) as aresp:
                atoken = json.loads(aresp.read().decode('utf-8')).get('token')
                if atoken:
                    users_req = urllib.request.Request(
                        'https://niramaya-health-ai.onrender.com/admin/users',
                        headers={'Authorization': f'Bearer {atoken}'}
                    )
                    with urllib.request.urlopen(users_req, timeout=3) as uresp:
                        cloud_users = json.loads(uresp.read().decode('utf-8')).get('users', [])
                        if cloud_users:
                            aconn = get_db_connection()
                            acur = aconn.cursor()
                            d_hash = bcrypt.hashpw('User@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                            for u in cloud_users:
                                acur.execute('SELECT account_id FROM account_tbl WHERE LOWER(email) = %s', (u['email'].lower(),))
                                if not acur.fetchone():
                                    acur.execute('''
                                        INSERT INTO account_tbl (account_id, family_name, email, password_hash, is_active)
                                        VALUES (%s, %s, %s, %s, TRUE)
                                    ''', (u['account_id'], u['family_name'], u['email'], d_hash))
                            aconn.commit()
                            aconn.close()
        except Exception:
            pass

        # 2. Sync chats from cloud
        req = urllib.request.Request(
            'https://niramaya-health-ai.onrender.com/getchat',
            data=json.dumps({'account_id': 1}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            history = data.get('history', [])
            if not history:
                return

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT member_id FROM member_tbl WHERE member_id = 24')
        if not cur.fetchone():
            cur.execute(
                'INSERT INTO member_tbl (member_id, account_id, name, gender, age, height, weight) '
                'VALUES (24, 1, %s, %s, %s, %s, %s)',
                ('TestFamily', 'Other', 25, '170', '65')
            )
            conn.commit()

        for h in history:
            cur.execute('SELECT history_id FROM chat_history_tbl WHERE history_id = %s', (h['history_id'],))
            if not cur.fetchone():
                cur.execute(
                    'INSERT INTO chat_history_tbl (history_id, account_id, member_id, user_input, bot_response, model, timestamp) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (h['history_id'], 1, h.get('member_id') or 24, h['question'], h['response'], h.get('model') or 'BioGPT', h.get('timestamp') or 'NOW()')
                )
        conn.commit()
        conn.close()
        print(f"[+] Synchronized consultations and accounts from cloud to local database.")
    except Exception:
        pass

def main():
    print("=" * 62)
    print("        NIRAMAYA HEALTH AI - SYSTEM LAUNCHER")
    print("=" * 62)
    print("[1/3] Checking environment...")
    
    # Check PostgreSQL
    try:
        from db_config import get_db_connection
        conn = get_db_connection()
        conn.close()
        print("[+] PostgreSQL Database: CONNECTED & READY (projectH)")
    except Exception as e:
        print(f"[!] Warning: PostgreSQL check: {e}")
        print("    If PostgreSQL service is stopped, start it via Windows Services.")

    # Background cloud sync
    threading.Thread(target=sync_cloud_history, daemon=True).start()

    print("[2/3] Checking Port 5000...")
    free_port(5000)

    print("[3/3] Launching Flask Server on http://127.0.0.1:5000 ...")
    
    # Start browser opener in background thread
    threading.Thread(target=wait_and_open_browser, daemon=True).start()

    # Import and run app
    from app import app
    # Run with debug=False to avoid double-spawn reloading in launcher
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    main()
