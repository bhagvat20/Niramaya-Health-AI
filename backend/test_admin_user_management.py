import unittest
import json
import psycopg2
import bcrypt
from app import app
from db_config import get_db_connection
from init_db import setup_database

class TestAdminUserManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_database()
        cls.client = app.test_client()
        cls.client.testing = True

        # Ensure admin user token
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get admin id
        cursor.execute("SELECT admin_id FROM admin_tbl WHERE username = 'admin'")
        admin_row = cursor.fetchone()
        cls.admin_id = admin_row[0]

        # Login admin to get valid token
        login_res = cls.client.post('/admin/login', json={
            "username_or_email": "admin@niramaya.com",
            "password": "Admin@1234"
        })
        cls.admin_token = login_res.get_json()["token"]

        # Clean up existing test users from previous runs
        cursor.execute("DELETE FROM account_tbl WHERE email IN ('manageuser1@example.com', 'updatedsmith@example.com', 'deluser@example.com')")
        conn.commit()

        # Create dummy user 1 for management testing
        hashed = bcrypt.hashpw(b"Secret123", bcrypt.gensalt()).decode('utf-8')
        cursor.execute("""
            INSERT INTO account_tbl (family_name, email, password_hash, is_active)
            VALUES (%s, %s, %s, TRUE) RETURNING account_id
        """, ("SmithFamily", "manageuser1@example.com", hashed))
        cls.test_account_id_1 = cursor.fetchone()[0]
        conn.commit()


        # Add member to user 1
        cursor.execute("SELECT member_id FROM member_tbl WHERE account_id = %s", (cls.test_account_id_1,))
        mem = cursor.fetchone()
        if not mem:
            cursor.execute("""
                INSERT INTO member_tbl (account_id, name, gender, age, height, weight)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (cls.test_account_id_1, "John Smith", "Male", 35, "175", "70"))
            conn.commit()

        # Create dummy user 2 for deletion testing
        cursor.execute("SELECT account_id FROM account_tbl WHERE email = 'deluser@example.com'")
        row2 = cursor.fetchone()
        if not row2:
            hashed = bcrypt.hashpw(b"Secret123", bcrypt.gensalt()).decode('utf-8')
            cursor.execute("""
                INSERT INTO account_tbl (family_name, email, password_hash, is_active)
                VALUES (%s, %s, %s, TRUE) RETURNING account_id
            """, ("DeleteFamily", "deluser@example.com", hashed))
            cls.test_account_id_2 = cursor.fetchone()[0]
            conn.commit()
        else:
            cls.test_account_id_2 = row2[0]

        cursor.close()
        conn.close()

    def test_01_get_all_users(self):
        """Test retrieving all registered users."""
        res = self.client.get('/admin/users', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(len(data.get("users", [])), 2)
        
        # Verify passwords/hashes are not present in response
        for u in data["users"]:
            self.assertNotIn("password", u)
            self.assertNotIn("password_hash", u)

    def test_02_search_and_filter_users(self):
        """Test searching users by text query and status filter."""
        # Search by email
        res1 = self.client.get('/admin/users?search=manageuser1', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res1.status_code, 200)
        users1 = res1.get_json()["users"]
        self.assertEqual(len(users1), 1)
        self.assertEqual(users1[0]["email"], "manageuser1@example.com")

        # Filter by status
        res2 = self.client.get('/admin/users?status=active', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(all(u["is_active"] for u in res2.get_json()["users"]))

    def test_03_get_user_details(self):
        """Test viewing individual user details and associated family members."""
        res = self.client.get(f'/admin/users/{self.test_account_id_1}', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        user = data.get("user")
        self.assertEqual(user["email"], "manageuser1@example.com")
        self.assertEqual(user["family_name"], "SmithFamily")
        self.assertGreaterEqual(len(user.get("members", [])), 1)
        self.assertEqual(user["members"][0]["name"], "John Smith")
        # Ensure password hash is not exposed
        self.assertNotIn("password_hash", user)

    def test_04_update_user_profile(self):
        """Test editing user family name and email."""
        new_name = "UpdatedSmithFamily"
        new_email = "updatedsmith@example.com"

        res = self.client.put(f'/admin/users/{self.test_account_id_1}', 
            json={"family_name": new_name, "email": new_email},
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])

        # Re-fetch and verify update
        get_res = self.client.get(f'/admin/users/{self.test_account_id_1}', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        u = get_res.get_json()["user"]
        self.assertEqual(u["family_name"], new_name)
        self.assertEqual(u["email"], new_email)

    def test_05_activate_deactivate_user(self):
        """Test deactivating user account and verifying login restriction."""
        # Deactivate
        res1 = self.client.put(f'/admin/users/{self.test_account_id_1}/status',
            json={"is_active": False},
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res1.status_code, 200)
        self.assertFalse(res1.get_json()["is_active"])

        # Verify deactivated user cannot login
        login_res = self.client.post('/userlogin', json={
            "email": "updatedsmith@example.com",
            "password": "Secret123"
        })
        self.assertEqual(login_res.status_code, 403)
        self.assertIn("deactivated", login_res.get_json()["message"].lower())

        # Reactivate
        res2 = self.client.put(f'/admin/users/{self.test_account_id_1}/status',
            json={"is_active": True},
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.get_json()["is_active"])

    def test_06_delete_user_with_safeguards(self):
        """Test user deletion safeguard requirements."""
        # Attempt deletion without confirmation flag -> 400 Bad Request
        res_unconfirmed = self.client.delete(f'/admin/users/{self.test_account_id_2}',
            json={"confirm": False},
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res_unconfirmed.status_code, 400)
        data_unconfirmed = res_unconfirmed.get_json()
        self.assertTrue(data_unconfirmed.get("requires_confirmation"))

        # Confirmed deletion -> 200 OK
        res_confirmed = self.client.delete(f'/admin/users/{self.test_account_id_2}',
            json={"confirm": True},
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        self.assertEqual(res_confirmed.status_code, 200)
        self.assertTrue(res_confirmed.get_json()["success"])

        # Verify user is deleted
        get_res = self.client.get(f'/admin/users/{self.test_account_id_2}', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(get_res.status_code, 404)

    def test_07_unauthorized_user_access_blocked(self):
        """Test normal user or unauthenticated request cannot access admin user management APIs."""
        # No token
        res1 = self.client.get('/admin/users')
        self.assertEqual(res1.status_code, 401)

        # Invalid token
        res2 = self.client.put(f'/admin/users/{self.test_account_id_1}',
            json={"family_name": "Hacker", "email": "hacker@example.com"},
            headers={'Authorization': 'Bearer fake_user_token'}
        )
        self.assertEqual(res2.status_code, 401)

if __name__ == '__main__':
    unittest.main()
