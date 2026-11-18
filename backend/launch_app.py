"""
Niramaya Health AI - Automated Launcher & Server Manager
- Offline & Online Compatible (SQLite, Local PostgreSQL, or Cloud Neon PostgreSQL)
- Ensures clean port 5000
- Starts Flask server
- Automatically waits until server responds before opening browser
"""
import os
import sys
import time
import socket
import threading
import webbrowser
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def _load_dotenv_files():
    for env_path in (os.path.join(PROJECT_ROOT, ".env"), os.path.join(BASE_DIR, ".env")):
        if not os.path.isfile(env_path):
            continue
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass


_load_dotenv_files()


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
        output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
        for line in output.strip().splitlines():
            if 'LISTENING' in line:
                pid = line.strip().split()[-1]
                subprocess.run(
                    f'taskkill /F /PID {pid}',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"[*] Closed previous process (PID: {pid})")
                time.sleep(1)
                break
    except Exception as e:
        print(f"[!] Note: Could not auto-kill port {port}: {e}")


def wait_and_open_browser(url="http://127.0.0.1:5000", max_wait=20):
    """Waits until the server is actually responding before opening the browser."""
    print("[*] Waiting for server to initialize AI models & database...")
    start_time = time.time()
    probe_url = url.rstrip('/') + '/api/status'
    while time.time() - start_time < max_wait:
        try:
            with urllib.request.urlopen(probe_url, timeout=1.0) as resp:
                if resp.status == 200:
                    print("\n" + "=" * 64)
                    print("   >>> SUCCESS: NIRAMAYA HEALTH AI IS LIVE AND READY! <<<")
                    print("=" * 64)
                    print(f"  [+] Home Page      : {url}/home.html")
                    print(f"  [+] Symptom Checker: {url}/question_input.html")
                    print(f"  [+] Admin Portal   : {url}/admin_login.html")
                    print("-" * 64)
                    print("  NOTES:")
                    print("  * Browser has been opened automatically.")
                    print("  * KEEP THIS WINDOW OPEN while using the project.")
                    print("  * Press Ctrl+C or close this window to stop the server.")
                    print("=" * 64 + "\n")
                    webbrowser.open(url)
                    return
        except Exception:
            time.sleep(0.6)

    print("[*] Opening browser now...")
    webbrowser.open(url)


def main():
    print("=" * 64)
    print("        NIRAMAYA HEALTH AI - SYSTEM LAUNCHER")
    print("=" * 64)
    print("[1/3] Checking database connection...")

    try:
        from db_config import get_db_connection
        conn = get_db_connection()
        is_sqlite = conn.__class__.__name__ == 'SQLiteConnWrapper'
        conn.close()
        if is_sqlite:
            print("[+] Database: CONNECTED & READY (SQLite: backend/niramaya.db)")
        elif os.environ.get("DATABASE_URL"):
            print("[+] Database: CONNECTED & READY (Cloud PostgreSQL via DATABASE_URL)")
        else:
            print("[+] Database: CONNECTED & READY (Local PostgreSQL: projectH)")
    except Exception as e:
        print(f"[!] Warning: Database check notice: {e}")

    print("[2/3] Checking Port 5000...")
    free_port(5000)

    print("[3/3] Launching Flask Server on http://127.0.0.1:5000 ...")

    # Start browser opener in background thread
    threading.Thread(target=wait_and_open_browser, daemon=True).start()

    # Import and run app
    from app import app
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
