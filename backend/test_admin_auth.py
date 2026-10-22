import unittest
import json
import psycopg2
import bcrypt
from app import app
from db_config import get_db_connection
from init_db import setup_database

class TestAdminAuthenticationAndSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure database tables and default admin are setup
        setup_database()
        cls.client = app.test_client()
        cls.client.testing = True
        
        # Ensure test normal user exists in account_tbl
        conn = get_db_connection()
        cursor = conn.cursor()
        
        test_user_email = "normaluser@example.com"
        test_user_pass = "UserPass123"
        hashed = bcrypt.hashpw(test_user_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("SELECT account_id FROM account_tbl WHERE email = %s", (test_user_email,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
                INSERT INTO account_tbl (family_name, email, password_hash)
                VALUES (%s, %s, %s)
            """, ("TestFamily", test_user_email, hashed))
            conn.commit()
            
        cursor.close()
        conn.close()

    def test_01_existing_user_registration_and_login(self):
        """Test that existing User login and registration work as before."""
        # Test User Login
        response = self.client.post('/userlogin', json={
            "email": "normaluser@example.com",
            "password": "UserPass123"
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("email"), "normaluser@example.com")

    def test_02_successful_admin_login(self):
        """Test successful Admin login with correct credentials."""
        response = self.client.post('/admin/login', json={
            "username_or_email": "admin@niramaya.com",
            "password": "Admin@1234"
        })
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        self.assertEqual(data["admin"]["username"], "admin")
        self.assertEqual(data["admin"]["email"], "admin@niramaya.com")
        self.assertEqual(data["admin"]["role"], "admin")
        # Ensure passwords/hashes are NEVER returned in response
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)

    def test_03_invalid_admin_login(self):
        """Test invalid Admin login attempts."""
        # Wrong password
        res1 = self.client.post('/admin/login', json={
            "username_or_email": "admin@niramaya.com",
            "password": "WrongPassword123"
        })
        self.assertEqual(res1.status_code, 401)
        self.assertFalse(res1.get_json()["success"])

        # Non-existent admin
        res2 = self.client.post('/admin/login', json={
            "username_or_email": "fakeadmin@niramaya.com",
            "password": "Admin@1234"
        })
        self.assertEqual(res2.status_code, 401)
        self.assertFalse(res2.get_json()["success"])

        # Missing parameters
        res3 = self.client.post('/admin/login', json={})
        self.assertEqual(res3.status_code, 400)
        self.assertFalse(res3.get_json()["success"])

    def test_04_unauthenticated_access_to_admin_apis(self):
        """Test unauthenticated access (missing, invalid, or malformed token)."""
        # No token header
        res1 = self.client.get('/admin/verify')
        self.assertEqual(res1.status_code, 401)
        self.assertFalse(res1.get_json()["success"])

        # Invalid token
        res2 = self.client.get('/admin/verify', headers={
            'Authorization': 'Bearer invalid_fake_token_123'
        })
        self.assertEqual(res2.status_code, 401)
        self.assertFalse(res2.get_json()["success"])

        # Malformed header
        res3 = self.client.get('/admin/profile', headers={
            'Authorization': 'InvalidHeaderSyntax'
        })
        self.assertEqual(res3.status_code, 401)

    def test_05_normal_user_cannot_access_admin_apis(self):
        """Test that normal user credentials / tokens cannot access Admin APIs."""
        # Normal user trying to login via Admin endpoint
        res1 = self.client.post('/admin/login', json={
            "username_or_email": "normaluser@example.com",
            "password": "UserPass123"
        })
        self.assertEqual(res1.status_code, 401)
        self.assertFalse(res1.get_json()["success"])

        # Normal user trying to access protected admin route without admin token
        res2 = self.client.get('/admin/profile')
        self.assertEqual(res2.status_code, 401)

    def test_06_admin_logout(self):
        """Test Admin logout revokes the token."""
        # Step 1: Login to get a valid token
        login_res = self.client.post('/admin/login', json={
            "username_or_email": "admin",
            "password": "Admin@1234"
        })
        token = login_res.get_json()["token"]

        # Step 2: Access protected route with token
        verify_res = self.client.get('/admin/verify', headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(verify_res.status_code, 200)

        # Step 3: Logout
        logout_res = self.client.post('/admin/logout', headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(logout_res.status_code, 200)
        self.assertTrue(logout_res.get_json()["success"])

        # Step 4: Verify that token is now revoked and cannot be reused
        after_logout_res = self.client.get('/admin/verify', headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(after_logout_res.status_code, 401)

if __name__ == '__main__':
    unittest.main()
