import unittest
import json
from app import app
from db_config import get_db_connection
from init_db import setup_database

class TestAdminSystemMonitoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_database()
        cls.client = app.test_client()
        cls.client.testing = True

        # Login admin to obtain valid token
        login_res = cls.client.post('/admin/login', json={
            "username_or_email": "admin@niramaya.com",
            "password": "Admin@1234"
        })
        cls.admin_token = login_res.get_json()["token"]

    def test_01_stats_endpoint(self):
        """Test /admin/monitoring/stats returns real database metrics."""
        res = self.client.get('/admin/monitoring/stats', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        stats = data.get("stats", {})
        
        self.assertIn("total_users", stats)
        self.assertIn("active_users", stats)
        self.assertIn("deactivated_users", stats)
        self.assertIn("total_members", stats)
        self.assertIn("total_ai_chats", stats)
        self.assertIn("total_disease_predictions", stats)
        self.assertIn("total_health_content", stats)
        self.assertIn("published_health_content", stats)
        self.assertIn("active_admin_sessions", stats)

        self.assertGreaterEqual(stats["total_users"], 0)
        self.assertGreaterEqual(stats["published_health_content"], 1)

    def test_02_activity_endpoint(self):
        """Test /admin/monitoring/activity returns real activity logs without exposing passwords or hashes."""
        res = self.client.get('/admin/monitoring/activity', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        activity = data.get("activity", {})

        self.assertIn("recent_registrations", activity)
        self.assertIn("recent_chats", activity)
        self.assertIn("recent_content_updates", activity)

        # Check safety: No passwords or password_hash fields
        res_str = json.dumps(data)
        self.assertNotIn("password", res_str)
        self.assertNotIn("password_hash", res_str)

    def test_03_system_status_endpoint(self):
        """Test /admin/monitoring/system-status returns database health and table counts."""
        res = self.client.get('/admin/monitoring/system-status', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        sys_status = data.get("system_status", {})

        self.assertTrue(sys_status.get("database_connected"))
        self.assertEqual(sys_status.get("database_name"), "projectH")
        
        table_counts = sys_status.get("table_counts", {})
        self.assertIn("account_tbl", table_counts)
        self.assertIn("member_tbl", table_counts)
        self.assertIn("chat_history_tbl", table_counts)
        self.assertIn("health_content_tbl", table_counts)
        self.assertIn("admin_tbl", table_counts)

    def test_04_overview_endpoint(self):
        """Test /admin/monitoring/overview returns combined monitoring data."""
        res = self.client.get('/admin/monitoring/overview', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("stats", data)
        self.assertIn("activity", data)
        self.assertIn("system_status", data)

    def test_05_unauthorized_access_blocked(self):
        """Test unauthenticated or normal users cannot access monitoring endpoints."""
        endpoints = [
            '/admin/monitoring/stats',
            '/admin/monitoring/activity',
            '/admin/monitoring/system-status',
            '/admin/monitoring/overview'
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 401, f"Failed for endpoint {ep}")

if __name__ == '__main__':
    unittest.main()
