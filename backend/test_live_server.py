import requests
import time
import subprocess
import os
import sys

def run_live_tests():
    print("Launching Flask backend server...")
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    base_url = "http://127.0.0.1:5000"
    
    # Wait for server readiness
    for _ in range(10):
        try:
            res = requests.get(f"{base_url}/admin/verify")
            break
        except Exception:
            time.sleep(1)
    
    try:

        # 1. Admin Login
        print("\n--- 1. Testing Admin Login ---")
        res = requests.post(f"{base_url}/admin/login", json={
            "username_or_email": "admin@niramaya.com",
            "password": "Admin@1234"
        })
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
        assert res.status_code == 200
        token = res.json()["token"]
        
        # 2. Verify Session
        print("\n--- 2. Testing Protected /admin/verify ---")
        res = requests.get(f"{base_url}/admin/verify", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
        assert res.status_code == 200
        
        # 3. Access Admin Profile
        print("\n--- 3. Testing Protected /admin/profile ---")
        res = requests.get(f"{base_url}/admin/profile", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
        assert res.status_code == 200
        
        # 4. Invalid Token Access
        print("\n--- 4. Testing Invalid Token Access ---")
        res = requests.get(f"{base_url}/admin/profile", headers={
            "Authorization": "Bearer invalid_token_xyz"
        })
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
        assert res.status_code == 401
        
        # 5. Normal User Login
        print("\n--- 5. Testing Existing User Login ---")
        res = requests.post(f"{base_url}/userlogin", json={
            "email": "normaluser@example.com",
            "password": "UserPass123"
        })
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
        assert res.status_code == 200
        
        # 6. Admin Logout
        print("\n--- 6. Testing Admin Logout ---")
        res = requests.post(f"{base_url}/admin/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
        assert res.status_code == 200
        
        # 7. Post-logout Token Reuse Check
        print("\n--- 7. Testing Revoked Token Reuse ---")
        res = requests.get(f"{base_url}/admin/verify", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.json()}")
        assert res.status_code == 401
        
        print("\n>>> ALL LIVE HTTP SERVER TESTS PASSED SUCCESSFULLY! <<<")
        
    finally:
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_live_tests()
